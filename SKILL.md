---
name: firefox
description: >-
  Browser automation with Selenium against the session's live Firefox. Use it whenever a task reaches the web — checking a fact, reading or verifying a page, and any request you would otherwise send with curl or wget, even a one-off GET.
---

## Loop: find, run, grow, cite

- Find: `scripts/help.py` names the sites, the snippets, and each snippet's callables.
- Run: `scripts/exec.py` sends one block at a time to the REPL that holds `driver`.
- Grow: what a block proved goes back into `snippets/` as a file, so the next task starts from the tree.
- Cite: the reply names the page behind every fact it states.

## Find: what exists already

- Snippet: a reusable `.py` file under `snippets/`, kept for the next run.
- Block: code sent to the Python REPL — a snippet, or throwaway code that never lands in a file.
- `scripts/help.py snippets/` lists the sites this skill covers.
- `scripts/help.py snippets/<site>/` gives each snippet's path and the docstring it opens with; run it before writing anything there.
- `scripts/help.py snippets/common/` does the same for the helper a block needs.
- `scripts/help.py snippets/<site>/<file>.py` lists one file's non-private callables: signature, then docstring.
- Read a file before editing it: its docstrings record the traps it was written to avoid.

## Run: one block at a time

- `scripts/exec.py` feeds one block on stdin to the live REPL in tmux window `cowork:firefox`.
- The REPL keeps `driver` alive from block to block.
- Each snippet opens with one `exec(open("snippets/<site>/<file>.py").read())` line per neighbour.
- Everything lands in the one namespace the REPL holds: a name two sites both want carries its site prefix.
- Nothing in `snippets/<site>/` fits? Send a block of your own to that same REPL.
- Read the summary the block prints rather than re-reading the page.
- Wait on a condition, never a duration.
- Predicate to poll: [`wait_js()`](snippets/common/wait_js.py).
- Value that must settle: [`wait_js_stable()` / `wait_text_stable()`](snippets/common/wait_stable.py).

### Handling the driver

- [`connect()`](snippets/common/connect.py) attaches to the running Firefox.
- [`reattach()`](snippets/common/reattach.py) reconnects when a session dies or loses its window.
- Both hand back a `driver` instead of taking one.
- Reuse the `driver` the session already holds; do not attach again in each block.

### Respecting the tabs

- Different site: [`site_tab()`](snippets/common/site_tab.py) opens a tab; the old tab keeps its page.
- Same site: reuse that tab.
- Tabs are plain Selenium windows: WebDriver draws no distinction.
- Snippet API calls go out from the page the driver is on.
- That tab must be a loaded page on that site: a blank or foreign one fails.
- Send a `curl`/`wget` request as a `fetch` from that tab, so cookies and origin travel with it.

## Grow: what proved itself stays

- Read https://www.selenium.dev/llms.txt before writing a snippet.
- Read https://agentskills.io/llms.txt before changing this file.
- Both index what goes stale here: the Selenium docs and the skill format.
- Open with the module docstring: one sentence on what the snippet can do, no signature.
- Give every non-private function a docstring: what it hands back, and the traps it was written to avoid.
- Site code and its DOM quirks go in `snippets/<site>/`; shared code goes in `snippets/common/`.
- Name as the library does: `SITE_NOUN` constant, `site_verb_noun(driver, ...)` function.
- Prefix `_` while only its own file calls it; those helpers need no docstring.
- Name a one-snippet file after the snippet.
- Save what will run again as a snippet, without being asked.
- Run it before saving; anything hard to undo takes `dry_run=True`.
- Format Python with `yapf -i`, pinned to 120 columns (`.style.yapf`).
- Format markdown with `prettier --write .`; it wraps nothing (`.prettierrc`).
- Commit as `<domain>: <verb phrase>`.
- Edits take effect on the next run; nothing needs reloading.

## Cite: every fact names its page

- Unsure about a fact? Run a search snippet first: `snippets/bing/` or `snippets/duckduckgo/`.
- Read the results; do not compose the answer from recall.
- Cite the page each fact came from in your reply.
