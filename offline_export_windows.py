"""Wrapper to run `marimo export html-wasm --offline` on Windows.

marimo's `initialize_asyncio()` unconditionally forces
`asyncio.WindowsSelectorEventLoopPolicy()` on win32 (see
marimo/_utils/asyncio_utils.py). The offline exporter uses Playwright
under the hood to resolve the real Pyodide package set, and Playwright's
`asyncio.create_subprocess_exec()` is not supported by the Selector event
loop on Windows -> NotImplementedError, always, regardless of environment.

The Selector policy only matters for marimo *sessions* (which need
`add_reader()`); a one-shot `export` CLI invocation never starts a
session, so it's safe to no-op that function for this process only and
let Python's Windows default (Proactor) stand, which does support
subprocesses.

Usage: same args as `marimo export html-wasm`, e.g.
    python offline_export_windows.py html-wasm notebook.py -o out --offline -f
"""
import asyncio
import sys

# marimo calls `asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())`
# unconditionally on win32 -- some call sites at import time (module-level
# code), others at runtime right before the exact `asyncio.run()` call that
# needs Playwright's `create_subprocess_exec()` (which Selector doesn't
# support on Windows -> NotImplementedError, every time). Patching each
# call site individually is fragile (several modules import the function
# by name, which rebinds it locally), so instead make
# `set_event_loop_policy` itself refuse to install the Selector policy and
# keep Windows' default (Proactor, which does support subprocesses). A
# one-shot `export` CLI run never starts a marimo Session -- the only
# thing that actually needs Selector's `add_reader()` -- so this is safe
# here.
if sys.platform == "win32":
    _real_set_policy = asyncio.set_event_loop_policy

    def _set_event_loop_policy_guard(policy: object | None = None) -> None:
        if isinstance(policy, asyncio.WindowsSelectorEventLoopPolicy):
            return
        _real_set_policy(policy)

    asyncio.set_event_loop_policy = _set_event_loop_policy_guard

from marimo._cli.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "export", *sys.argv[1:]]
    main()
