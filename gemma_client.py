"""
Edward AI Client — Multi-Backend Vision+Text Engine
Backends: Google Gemini (cloud, default), moondream2 (local CUDA), Ollama (local)
Hot-swap at runtime via set_backend().
"""

import asyncio
import base64
import io
import json
import os
from typing import Optional, AsyncGenerator

from PIL import Image
from dotenv import load_dotenv

from logger import get_logger

load_dotenv()
logger = get_logger(__name__)


_SYSTEM_PROMPT = """\
You are Edward, the FullCUDA Alchemist — brilliant, direct, GPU-accelerated assistant.
You can DIRECTLY CONTROL the user's computer: move the mouse, click, type, and press keys.

═══ COMPUTER CONTROL — ACTION SYNTAX ═══
Include action tags anywhere in your response to take control of the computer.
Edward's runtime will parse and execute them automatically.

[ACTION:mouse_move(x,y)]              — move mouse to screen coordinates
[ACTION:mouse_click(x,y)]             — left-click at (x, y)
[ACTION:mouse_double_click(x,y)]      — double-click at (x, y)
[ACTION:mouse_right_click(x,y)]       — right-click at (x, y)
[ACTION:type_text("text to type")]    — type text into focused field
[ACTION:key_press("ctrl+c")]          — keyboard shortcut (ctrl, shift, alt, enter, tab, esc…)
[ACTION:scroll(x,y,"down",3)]         — scroll at (x,y) — direction "up"/"down", amount 1–10

═══ COORDINATE RULES ═══
• Coordinates are SCREEN PIXELS on the actual monitor
• The coordinate map below shows the exact formula — always use it
• NEVER exceed the SCREEN BOUNDS shown in the coordinate map (e.g. x > 1920 on a 1920-wide screen is invalid)
• Aim for the CENTER of buttons, input fields, and icons

═══ WHEN TO ACT ═══
• If the user says "click X", "open Y", "type Z", "go to…", "scroll down" — execute it
• Chain actions naturally: move → click → type → enter
• Briefly explain what you're doing, then include the action tag(s)
• Do NOT ask for permission for simple, reversible actions (click, type, scroll)

═══ EXAMPLES ═══
User: "click the search bar"
You: I'll click the search bar for you. [ACTION:mouse_click(960,45)]

User: "type hello world"
You: Typing now. [ACTION:type_text("hello world")]

User: "close this window"
You: Closing with Alt+F4. [ACTION:key_press("alt+f4")]

User: "scroll down"
You: Scrolling down. [ACTION:scroll(960,540,"down",5)]
═══════════════════════════════════════
"""


# ── Image compression shared by all backends ──────────────────────────────────

def _compress_image(b64: str, max_side: int = 768) -> tuple[bytes, str]:
    """Resize + JPEG-compress a base64 image. Returns (raw_bytes, new_b64)."""
    raw = base64.b64decode(b64)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = img.size
    if max(w, h) > max_side:
        scale = max_side / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=82)
    data = buf.getvalue()
    return data, base64.b64encode(data).decode()


def _build_coord_context(compressed_bytes: bytes, region: Optional[dict]) -> str:
    """
    Build the coordinate-mapping context string that tells the model how to convert
    image pixel positions into real screen coordinates.

    Formula: screen_x = region_left + image_x * (region_w / img_w)
             screen_y = region_top  + image_y * (region_h / img_h)

    For full-screen mode region_left/top are 0 and the scale is > 1.
    For cursor-region mode region_left/top are non-zero and scale is ~1.
    """
    try:
        import io as _io
        from PIL import Image as _Image
        comp_img = _Image.open(_io.BytesIO(compressed_bytes))
        iw, ih = comp_img.width, comp_img.height

        if region:
            rl  = region.get("left",     0)
            rt  = region.get("top",      0)
            rw  = region.get("reg_w",    iw)
            rh  = region.get("reg_h",    ih)
            cx  = region.get("cursor_x", None)
            cy  = region.get("cursor_y", None)
            sw  = region.get("screen_w", None)
            sh  = region.get("screen_h", None)
            sx  = round(rw / iw, 3)
            sy  = round(rh / ih, 3)

            screen_note = (
                f"\n SCREEN BOUNDS: x must be 0–{sw}, y must be 0–{sh}  ← never exceed these"
                if sw and sh else ""
            )
            cursor_note = (
                f"\n Current cursor: ({cx}, {cy}) — shown as gold crosshair"
                if cx is not None else ""
            )
            return (
                f"\n[COORDINATE MAP — image {iw}×{ih}px covers screen region "
                f"({rl},{rt})→({rl+rw},{rt+rh})\n"
                f" To convert image (ix,iy) → screen: "
                f"screen_x = {rl} + ix × {sx},  screen_y = {rt} + iy × {sy}"
                f"{screen_note}{cursor_note}]"
            )
        else:
            return (
                f"\n[Image: {iw}×{ih}px — no region info available; "
                f"use the crosshair as the cursor reference]"
            )
    except Exception:
        return ""


# ── Google Gemini backend (default — fast, free, multimodal) ──────────────────

class GeminiBackend:
    name = "gemini"
    supports_vision = True

    # Use the new google-genai SDK; model IDs verified against this key
    MODELS = {
        "flash":      "gemini-2.5-flash",   # best quality, still fast
        "flash-lite": "gemini-2.0-flash-lite-001",
        "flash-2.0":  "gemini-2.0-flash-001",
    }
    DEFAULT_MODEL = "flash"

    def __init__(self, model_key: str = None):
        self.api_key   = os.getenv("GEMINI_API_KEY", "")
        self.model_key = model_key or os.getenv("AI_MODEL", self.DEFAULT_MODEL)
        self.model_id  = self.MODELS.get(self.model_key, self.MODELS[self.DEFAULT_MODEL])
        self._client   = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def is_available(self) -> bool:
        return bool(self.api_key)

    def set_model(self, model_key: str):
        self.model_key = model_key
        self.model_id  = self.MODELS.get(model_key, self.MODELS[self.DEFAULT_MODEL])
        self._client   = None

    async def ask(
        self,
        question: str,
        screenshot_b64: Optional[str] = None,
        region_info: Optional[dict] = None,
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            yield (
                "[Gemini API key missing — add GEMINI_API_KEY to your .env file. "
                "Get a free key at https://aistudio.google.com/apikey]\n"
            )
            return

        try:
            from google import genai
            from google.genai import types

            client = self._get_client()

            contents: list = []
            screen_ctx = ""
            if screenshot_b64:
                raw_bytes, _ = _compress_image(screenshot_b64)
                contents.append(types.Part.from_bytes(data=raw_bytes, mime_type="image/jpeg"))
                screen_ctx = _build_coord_context(raw_bytes, region_info)
            contents.append(_SYSTEM_PROMPT + screen_ctx + "\n\n" + question)

            model_id = self.model_id
            queue: asyncio.Queue = asyncio.Queue()
            loop = asyncio.get_event_loop()

            def _stream_worker():
                try:
                    for chunk in client.models.generate_content_stream(
                        model=model_id,
                        contents=contents,
                    ):
                        text = getattr(chunk, "text", None)
                        if text:
                            loop.call_soon_threadsafe(queue.put_nowait, text)
                except Exception as exc:
                    loop.call_soon_threadsafe(
                        queue.put_nowait,
                        f"\n[Gemini error ({type(exc).__name__}): {exc}]"
                    )
                finally:
                    loop.call_soon_threadsafe(queue.put_nowait, None)

            import threading
            threading.Thread(target=_stream_worker, daemon=True).start()

            while True:
                chunk = await queue.get()
                if chunk is None:
                    break
                yield chunk

        except Exception as e:
            err = f"Gemini error ({type(e).__name__}): {e}"
            logger.error(err)
            yield f"\n[{err}]"


# ── moondream backend (cloud API, v1.2+) ──────────────────────────────────────

class MoondreamBackend:
    name = "moondream"
    supports_vision = True

    def __init__(self):
        self._api_key = os.getenv("MOONDREAM_API_KEY", "")
        self._model = None

    def _get_model(self):
        if self._model is None:
            import moondream as md
            self._model = md.vl(api_key=self._api_key)
            logger.info("moondream cloud client ready")
        return self._model

    def is_available(self) -> bool:
        try:
            import moondream  # noqa: F401
            return bool(self._api_key)
        except ImportError:
            return False

    async def ask(
        self,
        question: str,
        screenshot_b64: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        if not self._api_key:
            yield (
                "[Moondream API key missing — add MOONDREAM_API_KEY to your .env file. "
                "Get a free key at https://moondream.ai]\n"
            )
            return

        try:
            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(None, self._get_model)

            if screenshot_b64:
                raw_bytes, _ = _compress_image(screenshot_b64, max_side=512)
                pil_image    = Image.open(io.BytesIO(raw_bytes))

                def _infer():
                    out = model.query(image=pil_image, question=question)
                    # Cloud API returns a dict; local/typed API returns QueryOutput
                    if isinstance(out, dict):
                        answer = out.get("answer", "")
                    else:
                        answer = out.answer
                    if isinstance(answer, str):
                        return answer
                    return "".join(answer)

                result = await loop.run_in_executor(None, _infer)
            else:
                result = (
                    "I'm moondream — a vision model. "
                    "Capture a screenshot (Ctrl+R or Win+Shift+E) so I can see your screen!"
                )

            yield result

        except ImportError:
            yield "[moondream not installed — run: pip install moondream]"
        except Exception as e:
            err = f"moondream error ({type(e).__name__}): {e}"
            logger.error(err)
            yield f"\n[{err}]"


# ── Ollama backend (kept as fallback) ─────────────────────────────────────────

class OllamaBackend:
    name = "ollama"
    supports_vision = True

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
        self.model    = os.getenv("OLLAMA_MODEL", "gemma4:latest")

    def is_available(self) -> bool:
        import httpx
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    async def ask(
        self,
        question: str,
        screenshot_b64: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        import httpx

        payload: dict = {
            "model":   self.model,
            "prompt":  f"{_SYSTEM_PROMPT}\n\nUser: {question}",
            "stream":  True,
            "options": {"temperature": 0.7, "num_predict": 600},
        }
        if screenshot_b64:
            _, compressed = _compress_image(screenshot_b64, max_side=512)
            payload["images"] = [compressed]

        try:
            async with httpx.AsyncClient(timeout=90) as client:
                async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        chunk = json.loads(line)
                        if "response" in chunk:
                            yield chunk["response"]
                        if chunk.get("done"):
                            break
        except httpx.ReadTimeout:
            yield "\n[Ollama timed out (90s) — switch to Gemini instead ⚡]"
        except httpx.ConnectError:
            yield f"\n[Cannot reach Ollama at {self.base_url} — switch to Gemini ⚡]"
        except Exception as e:
            yield f"\n[Ollama error ({type(e).__name__}): {e}]"


# ── Multi-backend orchestrator ────────────────────────────────────────────────

_BACKEND_REGISTRY: dict[str, type] = {
    "gemini":    GeminiBackend,
    "moondream": MoondreamBackend,
    "ollama":    OllamaBackend,
}

BACKEND_LABELS = {
    "gemini":    "GEMINI 2.5",
    "moondream": "MOONDREAM",
    "ollama":    "OLLAMA",
}

GEMINI_MODEL_LABELS = {
    "flash":      "2.5 Flash (recommended)",
    "flash-lite": "2.0 Flash Lite",
    "flash-2.0":  "2.0 Flash",
}


class EdwardAIClient:
    """
    Orchestrates multiple AI backends.
    Call set_backend(name) to hot-swap at runtime.
    """

    def __init__(self, backend_name: str = None):
        preferred = backend_name or os.getenv("AI_BACKEND", "gemini")
        self._backends: dict[str, object] = {
            "gemini":    GeminiBackend(os.getenv("AI_MODEL", "flash-lite")),
            "moondream": MoondreamBackend(),
            "ollama":    OllamaBackend(),
        }
        self._active_name = preferred
        logger.info(f"EdwardAIClient — active backend: {preferred}")

    @property
    def active_backend(self):
        return self._backends[self._active_name]

    @property
    def active_name(self) -> str:
        return self._active_name

    def set_backend(self, name: str):
        if name not in self._backends:
            logger.warning(f"Unknown backend: {name}")
            return
        self._active_name = name
        logger.info(f"AI backend switched → {name}")

    def set_gemini_model(self, model_key: str):
        gemini = self._backends.get("gemini")
        if isinstance(gemini, GeminiBackend):
            gemini.set_model(model_key)
            logger.info(f"Gemini model → {model_key}")

    def available_backends(self) -> list[str]:
        """Return names of backends that report as available."""
        return [n for n, b in self._backends.items() if b.is_available()]

    async def ask_question(
        self,
        question:          str,
        screenshot_base64: Optional[str] = None,
        stream:            bool = True,
        region_info:       Optional[dict] = None,
        raw_question:      Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        backend = self.active_backend
        # Moondream is a simple vision API — send only the raw question, not the
        # context-enhanced prompt (which adds clipboard/screen boilerplate it can't use).
        effective_q = raw_question if (raw_question and backend.name == "moondream") else question
        logger.info(f"⚡ {backend.name} ← {effective_q[:60]}…")
        if hasattr(backend, 'ask') and 'region_info' in backend.ask.__code__.co_varnames:
            async for chunk in backend.ask(effective_q, screenshot_base64, region_info=region_info):
                yield chunk
        else:
            async for chunk in backend.ask(effective_q, screenshot_base64):
                yield chunk


# ── Singleton ─────────────────────────────────────────────────────────────────

_client: Optional[EdwardAIClient] = None


def get_gemma_client(**_kwargs) -> EdwardAIClient:
    global _client
    if _client is None:
        _client = EdwardAIClient()
    return _client
