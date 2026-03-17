# Shared Session (Gemini + Claude)

Both engines share context by reading/writing the same files:

- `shared-session/CONTEXT.md` (long-lived context)
- `shared-session/TODO.md` (**strict JSON** task state)
- `shared-session/LAST_RESULT.md` (latest handoff)
- `shared-session/SESSION_LOG.md` (append-only history)

## Run

```bash
./scripts/run_gemini_shared.sh "요청 내용"
./scripts/run_claude_shared.sh "요청 내용"
```

## Concurrency safety

- Wrappers use `flock` on `shared-session/.session.lock`.
- If both engines start at once, one waits (up to 120s), so shared files do not collide.

## TODO format (strict)

`TODO.md` must be valid JSON object with this minimum schema:

```json
{
  "version": 1,
  "tasks": [
    {
      "id": "TASK-001",
      "title": "...",
      "status": "todo",
      "updated_at": "2026-03-17T12:00:00+09:00"
    }
  ]
}
```

Wrappers validate this before/after each run.
If an engine breaks JSON, wrapper restores previous valid TODO and logs a note.

## Recommended flow

1. Put stable constraints in `CONTEXT.md`
2. Keep active tasks in `TODO.md` JSON
3. Alternate engines as needed (both read same files)
4. Check `LAST_RESULT.md` for newest handoff
