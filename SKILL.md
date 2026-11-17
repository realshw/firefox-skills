---
name: firefox
description: >-
  Browser automation with Selenium against the session's live Firefox. Use it whenever a task reaches the web — checking a fact, reading or verifying a page, and any request you would otherwise send with curl or wget, even a one-off GET.
---

## Running a snippet or block

- Snippet: a file under `snippets/<site>/`, whatever it holds.
- Block: anything sent to the REPL — a snippet, or throwaway code that never lands in a file.
- List `snippets/<site>/` before writing anything: a file there may already do the task.
- `head -1 snippets/common/*.py` the same way: the helper a block needs usually already exists.
- Each snippet opens with one `exec(open("snippets/<site>/<file>.py").read())` line per neighbour.
- Everything lands in the one namespace the REPL holds: a name two sites both want carries its site prefix.
- `scripts/exec.py` feeds one block on stdin to the live REPL in tmux window `cowork:firefox`.
- The REPL keeps `driver` alive from block to block.
- Nothing in `snippets/<site>/` fits? Send a block of your own to that same REPL.
- Read the summary the block prints rather than re-reading the page.
- Wait on a condition, never a duration.
- Predicate to poll: [`wait_js()`](snippets/common/wait_js.py).
- Value that must settle: [`wait_js_stable()` / `wait_text_stable()`](snippets/common/wait_stable.py).

## Handling the driver

- [`connect()`](snippets/common/connect.py) attaches to the running Firefox.
- [`reattach()`](snippets/common/reattach.py) reconnects when a session dies or loses its window.
- Both hand back a `driver` instead of taking one.
- Reuse the `driver` the session already holds; do not attach again in each block.

## Respecting the tabs

- Different site: [`site_tab()`](snippets/common/site_tab.py) opens a tab; the old tab keeps its page.
- Same site: reuse that tab.
- Tabs are plain Selenium windows: WebDriver draws no distinction.
- Snippet API calls go out from the page the driver is on.
- That tab must be a loaded page on that site: a blank or foreign one fails.
- Send a `curl`/`wget` request as a `fetch` from that tab, so cookies and origin travel with it.

## Saving a snippet

- Read https://www.selenium.dev/llms.txt before writing a snippet.
- Read https://agentskills.io/llms.txt before changing this file.
- Both index what goes stale here: the Selenium docs and the skill format.
- Site code and its DOM quirks go in `snippets/<site>/`; shared code goes in `snippets/common/`.
- Read a file before editing it: the comment at the top records the traps it was written to avoid.
- Name as the library does: `SITE_NOUN` constant, `site_verb_noun(driver, ...)` function.
- Prefix `_` while only its own file calls it.
- Name a one-snippet file after the snippet.
- Save what will run again as a snippet, without being asked.
- Run it before saving; anything hard to undo takes `dry_run=True`.
- Format Python with `yapf -i`, pinned to 120 columns (`.style.yapf`).
- Format markdown with `prettier --write .`; it wraps nothing (`.prettierrc`).
- Commit as `<domain>: <verb phrase>`.
- Edits take effect on the next run; nothing needs reloading.

## Sourcing the answer

- Unsure about a fact? Run a search snippet first: `snippets/bing/` or `snippets/duckduckgo/`.
- Read the results; do not compose the answer from recall.
- Cite the page each fact came from in your reply.
