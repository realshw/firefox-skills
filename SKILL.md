---
name: firefox
description: >-
  Browser automation with Selenium against the session's live Firefox. Use it whenever a task reaches the web — checking a fact, reading or verifying a page, and any request you would otherwise send with curl or wget, even a one-off GET.
---

## Terminology

- Snippet: a reusable Python file under `snippets/`.
- Block: code sent to the Python REPL — a snippet, or throwaway code.

## Loop: find, exec, grow, cite

- Find: `scripts/help.py` names the sites, the snippets, and each snippet's callables.
- Exec: `scripts/exec.py` sends one block at a time to the REPL that holds `driver`.
- Grow: what a block proved goes back into `snippets/` as a file.
- Cite: the reply names the page behind every fact it states.

## Find: what exists already

- `scripts/help.py snippets` lists the sites this skill covers.
- `scripts/help.py snippets/<site>` gives each snippet's path and the docstring it opens with.
- `scripts/help.py snippets/common` does the same for the shared helpers.
- `scripts/help.py snippets/<site>/<file>.py` lists one file's non-private callables: signature, then docstring.
- Read the file, not just its line.

## Exec: one block at a time

- `scripts/exec.py` feeds one block on stdin to the live REPL in tmux window `cowork:firefox`.
- The REPL keeps `driver` alive from block to block.
- Load a snippet into the block with `exec(open("snippets/<site>/<file>.py").read())`.
- One namespace for every snippet and block.
- Nothing in `snippets/<site>/` fits? Send a block of your own to that same REPL.
- Read the summary the block prints rather than re-reading the page.
- Wait on a condition; a tick, a backoff or a pause between calls may be a duration, a page's readiness may not.
- Predicate to poll: [`wait_js()`](snippets/common/wait_js.py).
- Value that must settle: [`wait_js_stable()` / `wait_text_stable()`](snippets/common/wait_stable.py).

### Handling the driver

- [`connect()`](snippets/common/connect.py) attaches to the running Firefox.
- [`reattach()`](snippets/common/reattach.py) reconnects when a session dies or loses its window.
- Reuse the `driver` the session already holds; do not attach again in each block.

### Respecting the tabs

- Call [`site_tab()`](snippets/common/site_tab.py) before `driver.get()`.
- Snippet API calls need a loaded page on the site.
- Send a `curl`/`wget` request as a `fetch` from that page.

## Grow: what proved itself stays

- Read https://www.selenium.dev/llms.txt before writing a snippet.
- Read https://agentskills.io/llms.txt before changing this file.
- Open with the module docstring: one sentence on what the snippet can do, no signature.
- Give every non-private function a docstring: what it hands back, and the traps it was written to avoid.
- Pull in what it needs with `exec(open("snippets/<site>/<file>.py").read())` lines.
- Site code and its DOM quirks go in `snippets/<site>/`; shared code goes in `snippets/common/`.
- Name as the library does: `SITE_NOUN` constant, `site_verb_noun(driver, ...)` function.
- Prefix `_` on anything only its own file calls; those helpers need no docstring.
- Save what will run again as a snippet, without being asked.
- Exec it before saving; anything hard to undo takes `dry_run=True`.
- Commit as `<domain>: <verb phrase>`.

## Cite: every fact names its page

- Unsure about a fact? Search first: [`bing_search()`](snippets/bing/search.py).
- Read the results; do not compose the answer from recall.
- Cite the page each fact came from in your reply.

## Miscellaneous

- Edits on a snippet take effect on the next block that loads it; nothing needs reloading.
- Format Python with `yapf -i`, pinned to 120 columns (`.style.yapf`).
- Format Markdown with `prettier --write .` (`.prettierrc`).

## Examples

Ask what is already there, one path at a time:

```bash
scripts/help.py snippets
scripts/help.py snippets/bilibili
scripts/help.py snippets/bilibili/api.py
```

Exec a block, then read the print it leaves:

```bash
scripts/exec.py <<'PY'
print(driver.current_url)
PY
```
