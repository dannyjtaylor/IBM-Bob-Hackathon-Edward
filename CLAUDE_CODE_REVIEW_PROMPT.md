# Claude Code Review & Overhaul Prompt

Hey Claude! I need you to do a comprehensive review and overhaul of the Edward AI Assistant project. Here's what needs to be done:

## 🎯 Primary Objectives

### 1. **Verify Bob's Implementation**
Review ALL changes made by Bob (my AI partner) and verify:
- ✅ Cursor-focused screenshot capture is working correctly
- ✅ Gemma 4 integration is properly implemented
- ✅ No Bob API references remain (should all be Gemma 4 now)
- ✅ FullMetal Alchemist theme is consistent throughout
- ✅ Logging is clean (no duplicates)
- ✅ NumPy compatibility issues are resolved
- ✅ All error handling is robust

**Files to review:**
- `main.py` - Main application logic
- `agent.py` - Screenshot capture (cursor-focused)
- `gemma_client.py` - New Gemma 4 client
- `overlay.py` - UI overlay
- `logger.py` - Logging system
- `.env` - Configuration

### 2. **UI/UX Overhaul** 🎨
The current UI looks generic and AI-generated. Make it IMPRESSIVE and unique:

#### Design Requirements:
- **Theme**: FullCUDA Alchemist / Edward aesthetic
  - Gold (#DAA520) and Red (#B22222) color scheme
  - Alchemy circle motifs
  - Automail-inspired design elements
  - Transmutation circle animations

#### Specific Improvements Needed:

**A. Overlay Panel (`overlay.py`):**
- [ ] Add animated alchemy circle background
- [ ] Improve button designs (not generic rounded rectangles)
- [ ] Add glow effects on hover
- [ ] Animated transitions (transmutation effects)
- [ ] Better typography (more impactful fonts)
- [ ] Add Edward's automail arm as a visual element
- [ ] Cursor indicator should look like a transmutation circle
- [ ] Response area should have a "parchment" or "blueprint" aesthetic

**B. Visual Indicators:**
- [ ] Acting indicator should be an animated alchemy circle
- [ ] Listening indicator should pulse with energy
- [ ] Loading states should show transmutation animations
- [ ] Error states should show "failed transmutation" effects

**C. System Tray Icon:**
- [ ] Custom icon (not generic)
- [ ] Animated when active
- [ ] Context menu with FMA-themed options

**D. Startup Screen (Optional):**
- [ ] Brief splash screen with alchemy circle
- [ ] "Equivalent Exchange" quote
- [ ] Fade-in animation

### 3. **Code Quality & Architecture** 🏗️

#### Review & Fix:
- [ ] Remove any remaining Bob API code/references
- [ ] Ensure all async operations are properly handled
- [ ] Verify error handling in all critical paths
- [ ] Check for memory leaks (especially in screenshot capture)
- [ ] Optimize cursor-focused screenshot performance
- [ ] Ensure Gemma 4 streaming works correctly
- [ ] Validate all type hints
- [ ] Add missing docstrings

#### Architecture Improvements:
- [ ] Separate UI components into modular files
- [ ] Create a proper theme/styling system
- [ ] Implement proper state management
- [ ] Add configuration validation
- [ ] Create proper event system for UI updates

### 4. **Feature Enhancements** ⚡

#### Must-Have:
- [ ] Real-time STT text display (show text as user speaks)
- [ ] Conversation history (save/load previous interactions)
- [ ] Keyboard shortcuts (beyond just Win+Shift+E)
- [ ] Screenshot preview in overlay (show what Edward sees)
- [ ] Adjustable cursor region size (user preference)
- [ ] Voice selection for TTS (if using ElevenLabs)

#### Nice-to-Have:
- [ ] Multiple alchemy circles for different actions
- [ ] Sound effects (transmutation sounds)
- [ ] Particle effects on actions
- [ ] Customizable hotkeys
- [ ] Dark/Light mode toggle (with FMA themes)
- [ ] Export conversation to file

### 5. **Testing & Validation** 🧪

Create/Update test files:
- [ ] `test_cursor_capture.py` - Test cursor-focused screenshots
- [ ] `test_gemma4_integration.py` - Test Gemma 4 responses
- [ ] `test_ui_components.py` - Test UI elements
- [ ] `test_error_handling.py` - Test error scenarios

### 6. **Documentation** 📚

Update/Create:
- [ ] `README.md` - Complete user guide
- [ ] `ARCHITECTURE.md` - System architecture
- [ ] `UI_DESIGN.md` - UI design philosophy
- [ ] `TROUBLESHOOTING.md` - Common issues
- [ ] Inline code comments where needed

## 🎨 UI Design Inspiration

Think:
- **Alchemy circles** - Geometric, mystical, animated
- **Automail** - Mechanical, precise, golden accents
- **Transmutation** - Energy flows, particle effects
- **Blueprint aesthetic** - Technical drawings, schematics
- **Gothic/Steampunk** - Victorian era meets alchemy

**NOT**:
- Generic Material Design
- Plain rounded rectangles
- Boring gradients
- Stock UI components
- Anything that looks "AI-generated"

## 🔧 Technical Constraints

- Must work on Windows 11
- Python 3.11
- PySide6 for UI
- Ollama + Gemma 4 for AI
- Must maintain cursor-focused screenshot feature
- Keep FullMetal Alchemist theme

## 📋 Deliverables

1. **Code Review Report**: List all issues found and fixed
2. **Updated Files**: All modified files with improvements
3. **New UI Components**: Enhanced visual elements
4. **Test Results**: Verification that everything works
5. **Screenshots**: Show the new UI design
6. **Documentation**: Updated guides and docs

## 🚀 Priority Order

1. **CRITICAL**: Verify Bob's implementation works correctly
2. **HIGH**: UI/UX overhaul (make it impressive)
3. **MEDIUM**: Code quality improvements
4. **LOW**: Nice-to-have features

## 💡 Notes

- The cursor-focused screenshot is a KEY feature - don't break it!
- Gemma 4 integration must work flawlessly
- UI should feel like Edward is actually your AI assistant
- Every interaction should feel like "alchemy" or "transmutation"
- Performance matters - keep it snappy

## 🎯 Success Criteria

- [ ] All Bob's code verified and working
- [ ] UI looks professional and unique (not AI-generated)
- [ ] No bugs or crashes
- [ ] Smooth animations and transitions
- [ ] Fast response times
- [ ] Clear error messages
- [ ] Comprehensive documentation
- [ ] User says "WOW!" when they see it

---

**Start with a comprehensive code review, then tackle the UI overhaul. Make Edward truly impressive!** ⚡🔥
