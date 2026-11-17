---
name: firefox
description: >-
  Browser automation with Selenium against the session's live Firefox. Use it whenever a task reaches the web — checking a fact, reading or verifying a page, and any request you would otherwise send with curl or wget. Reach for the browser rather than a shell HTTP client even for a one-off GET: the fetch carries the cookies, login state, and JavaScript-rendered content a bare request leaves behind.
---

## Running a snippet or block

- Snippet: a file under `snippets/<site>/`, whatever it holds. Block: anything sent to the REPL — a snippet, or throwaway code that never lands in a file.
- List `snippets/<site>/` before writing anything: a file there may already do the task, and doing it twice only surfaces at commit time.
- Each snippet opens with one `exec(open("snippets/<site>/<file>.py").read())` line per neighbour. Everything lands in the one namespace the REPL holds, so a name two sites both want carries its site prefix.
- `scripts/exec.py` feeds one Python block on stdin to the live REPL in tmux window `cowork:firefox`; `driver` keeps its browser state from block to block.
- Nothing in `snippets/<site>/` fits? Feed your own block to that same REPL.
- Read the summary the block prints rather than re-reading the page.
- Wait on a condition, never a duration: predicates through `snippets/common/wait_js.py`, values that must stop changing through `snippets/common/wait_stable.py`.

## Handling the driver

- `connect()` (`snippets/common/connect.py`) attaches to the running Firefox.
- `reattach()` (`snippets/common/reattach.py`) is the way back when a session dies or loses its window.
- Both hand back a `driver` instead of taking one.
- Reuse the `driver` the session already holds; do not attach again in each block.

## Respecting the tabs

- Different site: open a new tab through `snippets/common/site_tab.py`; the old tab keeps its page.
- Same site: reuse that tab.
- Tab handling is plain Selenium window handling; WebDriver draws no distinction between tabs and windows.
- Snippet API calls go out from the page the driver is on: that tab must be a loaded page on that site, and a blank or foreign one fails.
- `curl`/`wget` is that same request. Send it as a `fetch` from that tab and the session's cookies and origin travel with it.

## Saving a snippet

- Read https://www.selenium.dev/llms.txt before writing a snippet, and https://agentskills.io/llms.txt before changing this file: they index the Selenium docs and the skill format, the two things this skill goes stale against.
- Site code and its DOM quirks go in `snippets/<site>/`; shared code goes in `snippets/common/`.
- Read a file before editing it: the comment at the top records the traps it was written to avoid.
- Name it as the library reads: `SITE_NOUN` constant, `site_verb_noun(driver, ...)` function, a leading `_` on either while only its own file calls it; one-snippet files are named after it.
- Save what will run again as a snippet, without being asked, but run it first; anything hard to undo takes `dry_run=True`.
- Format: `yapf -i` for Python, pinned to 120 columns (`.style.yapf`); `prettier --write .` for the markdown, which wraps nothing (`.prettierrc`).
- Commit as `<domain>: <verb phrase>`.
- Edits take effect on the next run; nothing needs reloading.

## Sourcing the answer

- Unsure about any fact? Run a search-engine snippet first: `snippets/bing/` and `snippets/duckduckgo/` hold one each.
- Read the results; do not compose the answer from recall.
- Cite the page each fact came from in your reply.
