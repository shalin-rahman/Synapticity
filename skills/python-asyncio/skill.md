# Skill: Python asyncio — Official Patterns
# Source: docs.python.org/3/library/asyncio.html

## Core Rules
- `async def` for coroutines. `await` for suspending. Never block the event loop.
- `asyncio.run(main())` — single entry point. Never nest `asyncio.run()`.
- `asyncio.create_task(coro)` — schedule concurrent work. Returns a `Task`; always `await` or cancel it.
- `asyncio.gather(*coros)` — run N coroutines in parallel, collect results in order.
- `asyncio.wait_for(coro, timeout=N)` — adds timeout; raises `asyncio.TimeoutError` on expiry.

## Blocking I/O → asyncio.to_thread
```python
result = await asyncio.to_thread(blocking_fn, *args)  # runs in ThreadPoolExecutor
```
Use for: file I/O, `json.load/dump`, `subprocess.run`, `requests`, DB drivers without async support.

## Subprocess (non-blocking)
```python
proc = await asyncio.create_subprocess_exec(
    "cmd", "arg",
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
)
stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
```
Kill on timeout: `proc.kill(); await proc.communicate()`

## Synchronisation Primitives
| Primitive | Use |
|---|---|
| `asyncio.Event` | Signal between tasks. `set()` / `wait()`. |
| `asyncio.Lock` | Mutual exclusion. `async with lock:` |
| `asyncio.Queue` | Producer-consumer between tasks. |
| `asyncio.Semaphore(N)` | Limit concurrency to N. |

## Task Lifecycle
```python
task = asyncio.create_task(coro())
task.cancel()          # requests cancellation
try:
    await task
except asyncio.CancelledError:
    pass               # expected — swallow or propagate
```

## Common Mistakes
- **Never** call `time.sleep()` in async code — use `await asyncio.sleep(N)`.
- **Never** `asyncio.get_event_loop().run_until_complete()` inside a running loop → `RuntimeError`.
- **Always** await `Task.cancel()` result or the task leaks.
- `threading.Thread` in async context blocks scheduling — use `asyncio.to_thread` or `create_task`.
