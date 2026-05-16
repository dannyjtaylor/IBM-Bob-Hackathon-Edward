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


_SYSTEM_PROMPT = (
    "You are Edward, the FullCUDA Alchemist — brilliant, direct, GPU-accelerated. "
    "Help the user with their computer tasks using equivalent exchange. "
    "When given a screenshot, analyse it carefully and provide specific, actionable advice."
)


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
            if screenshot_b64:
                raw_bytes, _ = _compress_image(screenshot_b64)
                contents.append(types.Part.from_bytes(data=raw_bytes, mime_type="image/jpeg"))
            contents.append(_SYSTEM_PROMPT + "\n\n" + question)

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


# ── moondream2 backend (local, CUDA-accelerated, ~2 GB) ───────────────────────

class MoondreamBackend:
    name = "moondream"
    supports_vision = True

    def __init__(self):
        self._model = None
        self._loading = False

    def _load_model(self):
        if self._model is None and not self._loading:
            self._loading = True
            logger.info("Loading moondream2 (~2 GB — first run downloads the model)…")
            import moondream as md
            self._model = md.vl(model="vikhyatk/moondream2")
            logger.info("moondream2 ready")
            self._loading = False
        return self._model

    def is_available(self) -> bool:
        try:
            import moondream  # noqa: F401
            return True
        except ImportError:
            return False

    async def ask(
        self,
        question: str,
        screenshot_b64: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        try:
            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(None, self._load_model)

            if screenshot_b64:
                raw_bytes, _ = _compress_image(screenshot_b64, max_side=512)
                pil_image    = Image.open(io.BytesIO(raw_bytes))

                def _infer():
                    enc = model.encode_image(pil_image)
                    return model.query(enc, question)["answer"]

                result = await loop.run_in_executor(None, _infer)
            else:
                result = (
                    "I'm moondream — a vision model. "
                    "Press Ctrl+R to capture a screenshot so I can see what you're working on!"
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
    "moondream": "MOONDREAM 2",
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
        stream:            bool = True,      # kept for API compatibility
    ) -> AsyncGenerator[str, None]:
        backend = self.active_backend
        logger.info(f"⚡ {backend.name} ← {question[:60]}…")
        async for chunk in backend.ask(question, screenshot_base64):
            yield chunk


# ── Singleton ─────────────────────────────────────────────────────────────────

_client: Optional[EdwardAIClient] = None


def get_gemma_client(**_kwargs) -> EdwardAIClient:
    global _client
    if _client is None:
        _client = EdwardAIClient()
    return _client
