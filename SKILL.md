---
name: firefox
description: Browser automation with Selenium. Use when unsure about a fact, or a task needs a browser.
compatibility: Firefox with Marionette, geckodriver, selenium, tmux window cowork:firefox.
---

## Running a snippet

Snippets are reusable Selenium blocks that take `driver` first; each site keeps its own under `snippets/<site>/`. List that directory before writing anything of your own — a file there may already do the task, and doing it twice is a mistake that only surfaces at commit time.

`scripts/exec.py` feeds one Python block on stdin to the live REPL in the tmux window `cowork:firefox`, where `driver` keeps its browser state from block to block. Snippets print a short labelled summary; read that instead of re-reading the page.

Each file opens with one `exec(open("snippets/<site>/<file>.py").read())` line per neighbour. Everything lands in the single namespace the REPL holds, so a name two sites both want carries its site prefix.

When `snippets/<site>/` has nothing that fits, feed your own block to the same REPL.

Wait on a condition, never a duration: predicates through `snippets/common/wait_js.py`, values that must stop changing through `snippets/common/wait_stable.py`.

## Handling the driver

`snippets/common/connect.py` and `snippets/common/reattach.py` hold the two callables that hand back a `driver` instead of taking one: `connect()` attaches to the running Firefox, `reattach()` is the way back when a session dies or loses its window.

Reuse the `driver` the session already holds rather than attaching again in each block.

## Respecting the tabs

Open a new tab before going to a different site, through `snippets/common/site_tab.py`; the current tab keeps the page it was on, and staying within the same site reuses that tab. Tab handling is plain Selenium window handling: WebDriver draws no distinction between tabs and windows.

Calling a site's API from a snippet issues the request from the page the driver is on, so that tab has to be a loaded page on that site: a blank or foreign one will not do.

## Saving a snippet

Read https://www.selenium.dev/llms.txt before writing a snippet, and https://agentskills.io/llms.txt before changing this file. They index the Selenium docs and the skill format, the two things this skill goes stale against.

Site code and its DOM quirks go in a file under `snippets/<site>/`, beside its neighbours; shared code goes in a file under `snippets/common/`. Read a file before editing it: the comment at the top records the traps that file was written to avoid, and a blind overwrite throws those notes away.

Name what you add as the library already reads: `SITE_NOUN` for a constant, `site_verb_noun(driver, ...)` for a function, a leading `_` on either while only its own file calls it. Files that hold one snippet are named after it.

Save reusable snippets without being asked, but run them first; anything hard to undo takes `dry_run=True`. Format with `yapf -i`, commit as `<domain>: <verb phrase>`. Edits take effect on the next run: nothing needs reloading.

## Sourcing the answer

Unsure about any fact? Run a search-engine snippet — `snippets/bing/` and `snippets/duckduckgo/` hold one each — before guessing, and read the results instead of composing an answer from recall. Cite the page each fact came from in your reply.
