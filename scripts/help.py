#!/usr/bin/env python3
"""help.py — say what a directory or a snippet offers, without opening it.

    scripts/help.py snippets/                  the sites this skill covers
    scripts/help.py snippets/<site>/           one line per snippet: path — what it does
    scripts/help.py snippets/<site>/<file>.py  the callables it defines: signature + docstring

The source is parsed, never imported or run, so this works on a snippet that would need a browser. The
docstring a file opens with is what answers "is there already a snippet for this?", and the same parse
hands back every non-private function's signature and docstring.
"""

import ast
import os
import pathlib
import sys

PROG = pathlib.Path(__file__).name

USAGE = f"""usage: {PROG} <path>

  snippets/                  the sites, and how many snippets each holds
  snippets/<site>/           each .py file there, with the docstring it opens with
  snippets/<site>/<file>.py  each non-private function in it, with its signature and docstring

Prints paths relative to the directory you run it from, so a line copies straight into
exec(open("<path>").read())."""


def fail(message):
    print(f"{PROG}: {message}", file=sys.stderr)
    return 1


def lines(node):
    """The node's docstring as lines, [] when it has none."""
    text = ast.get_docstring(node)
    return text.split("\n") if text else []


def summary(node):
    """The docstring's first paragraph on one line — what a listing row can carry."""
    out = []
    for line in lines(node):
        if out and not line.strip():
            break
        out.append(line.strip())
    return " ".join(out)


def parse(path):
    """The file's AST, or None after saying what went wrong."""
    try:
        return ast.parse(path.read_text(encoding="utf-8"), str(path))
    except (OSError, SyntaxError, UnicodeDecodeError) as e:
        sys.stdout.flush()  # keep the message next to the row it belongs to
        print(f"{PROG}: {path}: {type(e).__name__}: {e}", file=sys.stderr)
        return None


def shown(path):
    """The path as the command was given it — relative, so it can be pasted into a snippet line."""
    return os.path.relpath(str(path))


def row(path, text):
    """One listing row: path, then what it does. A docstring that opens with its own file name loses it."""
    for prefix in (path.name + " — ", path.stem + " — "):
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    return f"{shown(path)} — {text}"


def snippets_in(directory):
    """The .py files directly under directory, by name."""
    return sorted(p for p in directory.glob("*.py") if p.is_file())


def callables(node, prefix=""):
    """(name, node) for every non-private def inside node, in source order; methods as Class.method."""
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not child.name.startswith("_"):
                yield prefix + child.name, child
        elif isinstance(child, ast.ClassDef):
            yield from callables(child, prefix + child.name + ".")


def signature(name, node):
    """The def's signature rebuilt from the AST: name(args) -> return."""
    ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return f"{name}({ast.unparse(node.args)}){ret}"


def list_sites(directory):
    """One row per subdirectory: its name and how many snippets it holds."""
    sites = sorted(d for d in directory.iterdir() if d.is_dir() and not d.name.startswith("."))
    width = max((len(d.name) for d in sites), default=0)
    total = 0
    for site in sites:
        n = len(snippets_in(site))
        total += n
        print(f"{site.name:<{width}}  {n}")
    print(f"SITES {len(sites)}, SNIPPETS {total}")
    return 0


def list_snippets(directory):
    """One row per .py file: its path and the docstring it opens with."""
    files = snippets_in(directory)
    for path in files:
        tree = parse(path)
        print(row(path, summary(tree) if tree else "(unreadable)"))
    print(f"SNIPPETS {len(files)}")
    return 0


def list_callables(path):
    """The file's own summary, then every non-private def: signature, then its docstring indented."""
    tree = parse(path)
    if tree is None:
        return 1
    print(row(path, summary(tree) or "(no docstring)"))
    found = 0
    for name, node in callables(tree):
        print()
        print(signature(name, node))
        for line in lines(node):
            print(f"    {line}".rstrip())
        found += 1
    print()
    print(f"CALLABLES {found}")
    return 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(USAGE)
        return 0
    if len(sys.argv) != 2:
        print(USAGE, file=sys.stderr)
        return 2
    target = pathlib.Path(sys.argv[1]).resolve()
    if not target.exists():
        return fail(f"no such path: {sys.argv[1]}")
    if target.is_file():
        if target.suffix != ".py":
            return fail(f"not a .py file: {sys.argv[1]}")
        return list_callables(target)
    if snippets_in(target):
        return list_snippets(target)
    if any(d.is_dir() for d in target.iterdir()):
        return list_sites(target)
    return fail(f"nothing to list under {sys.argv[1]} — no .py files and no subdirectories")


if __name__ == "__main__":
    sys.exit(main())
