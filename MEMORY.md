# ZEPHYR PROJECT MEMORY

## Context Summary
- Project Name: Zephyr
- Architecture: Hybrid (Antigravity + OpenClaw)
- Goal: Autonomous local coding assistant with multi-provider failbacks.

## Key Decisions
1. ReAct Loop: Using <thought> and <action> tags for transparent reasoning.
2. Local Priority: Prioritizing Zephyr Free (local reverse proxy) for heavy lifting.
3. Identity Sync: All core documents (SOUL, MEMORY, USER) are now rebranded to Zephyr.
4. Formal Tone: Strictly no emojis or emoticons in system and project files.
13. Strict Language Guard: Implemented "No Chinese" policy in SOUL and Orchestrator.
14. TUI Silence: Refactored main.py and orchestrator.py to prevent raw JSON observation leaks in the chat area.
15. Duplicate ID Fix: Changed ReasoningBox to use CSS classes instead of IDs to prevent crashes during multiple model iterations.
16. Session Reset: Successfully cleared current_session.json as requested by the user.
17. Robust Tools: Updated all tools to accept and ignore arbitrary **kwargs, preventing crashes from hallucinated parameters like 'requires_approval'.
18. Live Reasoning Stream: Removed tag-based filtering for the reasoning box. All incoming tokens are now displayed in real-time, but automatically hidden once an action (tool call) or final answer begins. This provides a truly interactive 'thinking' view.
19. Auto-Detect Proxy: Upgraded `run-zephyr-free.sh` with a multi-search algorithm (relative paths + $HOME search fallback) to automatically locate the DeepSeek-Free-API-master directory without manual configuration.

## Project Roadmap
- [x] Phase 1-5: TUI & Core Orchestration
- [x] Phase 6: Reliability Hardening
- [x] Phase 7: Local Proxy Integration
- [x] Phase 8-9: UI Polish & Async Stability
- [x] Phase 10: Zephyr Rebranding & Formalization
- [x] Phase 11: Linguistic & Output Hardening
- [x] Phase 12: TUI Layout & Stability (Duplicate ID Fix)
