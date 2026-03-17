# Shared Session (Gemini + Claude)

Both engines share context by reading/writing the same files:

- `shared-session/CONTEXT.md` (long-lived context)
- `shared-session/TODO.md` (current checklist)
- `shared-session/LAST_RESULT.md` (latest handoff)
- `shared-session/SESSION_LOG.md` (append-only history)

## Run

```bash
./scripts/run_gemini_shared.sh "요청 내용"
./scripts/run_claude_shared.sh "요청 내용"
```

## Recommended flow

1. Put stable constraints in `CONTEXT.md`
2. Put active work items in `TODO.md`
3. Alternate engines as needed (both read same files)
4. Check `LAST_RESULT.md` for the newest handoff

## Notes

- These wrappers force non-interactive mode to reduce timeout/prompt waits.
- If an engine fails to update `LAST_RESULT.md`, wrapper writes a fallback summary.
