---
name: firefox
description: Browser automation with Selenium. Use when unsure about a fact, or a task needs a browser.
compatibility: Firefox with Marionette on port 2828, geckodriver, selenium, tmux window cowork:browser.
---

## Running a snippet

Snippets are reusable Selenium blocks that take `driver` first. `scripts/exec_repl.py` takes one Python block on stdin and runs it in the long-lived REPL in the tmux window `cowork:browser`, so `driver` and earlier names survive. Snippets print a short labelled summary; read that instead of re-reading the page.

When no snippet fits the task, send your own Selenium block to the same REPL. Wait on a condition, never a duration: predicates through `snippets/common/wait_js.py`, values that must stop changing through `snippets/common/wait_stable.py`.

## Saving a snippet

Proactively save reusable ones, but run them first; anything hard to undo takes `dry_run=True`. Shared code goes in a file under `snippets/common/`; site code and its DOM quirks go in a file under `snippets/<site>/`. Format with `yapf -i`, and commit as `<domain>: <verb phrase>`.

Edits to an existing snippet need `importlib.reload` on the module before the REPL sees the change.

## Handling the driver

`snippets/common/connect.py` and `snippets/common/reattach.py` hold the two callables that hand back a `driver` instead of taking one. `connect()` attaches to the running Firefox; `reattach()` clears stray geckodrivers first and is the way back when a session dies or loses its window. Both leave the session on a blank tab.

## Respecting the tabs

Open a new tab before going to a different site; the current tab keeps the page it was on. Staying within the same site reuses that tab. Tab handling is plain Selenium WebDriver: `driver.window_handles`, `driver.switch_to.window`, `driver.switch_to.new_window`.

## Sourcing the answer

Unsure about any fact? Proactively search before guessing and read the results instead of composing an answer from recall. Cite the page each fact came from in your reply.
