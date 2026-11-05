#!/usr/bin/env python3
"""exec_repl.py — run a block in the tmux REPL and print what the block printed.

    scripts/exec_repl.py <<'PY'
    print(driver.title)
    PY

The block runs in the REPL's globals, so the browser session survives between runs, and travels through
send-keys as one base64 line (send-keys mangles literal newlines). Raised exceptions exit 1 here.
Blocks run in the REPL's cwd, the skill root, which is also on sys.path, so snippets are imported as
modules: from snippets.common import read_text.
"""

import base64
import os
import pathlib
import socket
import subprocess
import sys

PROG = pathlib.Path(__file__).name
TARGET = os.environ.get("COWORK_TARGET", "cowork:browser")
TIMEOUT = float(os.environ.get("COWORK_TIMEOUT", "120"))
CHUNK = 65536

# Runs in a throwaway locals dict, so it leaves no names in the shared globals.
WRAPPER = '''\
import socket
import sys
import traceback

sink = socket.create_connection({addr!r}).makefile("w", encoding="utf-8", errors="backslashreplace", buffering=1)

status = 0
try:
    stdout, stderr = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = sink
    exec(compile({block!r}, "<block>", "exec"), globals())
except BaseException:
    traceback.print_exc()
    status = 1
finally:
    sys.stdout, sys.stderr = stdout, stderr
    sink.close()

socket.create_connection({addr!r}).sendall(str(status).encode())
'''


def fail(message):
    print(f"{PROG}: {message}", file=sys.stderr)
    return 1


def read_block():
    """The block from stdin; None when stdin is a tty, i.e. nothing was piped in."""
    if sys.stdin.isatty():
        print(f"usage: {PROG} <<'PY' ... PY   (the block comes from stdin)", file=sys.stderr)
        return None
    return sys.stdin.buffer.read()


def main():
    if len(sys.argv) > 1:
        return fail(f"takes no arguments - pipe the block instead: echo 'print(driver.title)' | {PROG}")
    block = read_block()
    if block is None:
        return 2

    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(2)
    addr = server.getsockname()

    wrapper = WRAPPER.format(addr=addr, block=block)
    encoded = base64.b64encode(wrapper.encode()).decode()
    command = f"exec(__import__('base64').b64decode({encoded!r}).decode(), globals(), {{}})"

    sent = subprocess.run(["tmux", "send-keys", "-t", TARGET, command, "Enter"],
                          capture_output=True, text=True)
    if sent.returncode:
        reason = (sent.stderr or sent.stdout).strip() or f"tmux exited {sent.returncode}"
        if "can't find" in reason or "no server" in reason:
            return fail(f"{TARGET} is gone - ask the user to start it again, then retry.")
        # tmux 3.8 refuses a command string over ~16 KiB and types nothing at all: say so, and how big
        # the block was, instead of blaming a dead pane. base64 inflates a block by 4/3 before that.
        return fail(f"tmux refused the block ({reason}); its command was {len(command)} chars - over the "
                    f"~16 KiB ceiling, so split the block into two runs")

    socket.setdefaulttimeout(TIMEOUT)
    try:
        conn, _ = server.accept()
        while chunk := conn.recv(CHUNK):
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
        conn.close()
        status_conn, _ = server.accept()
        status = int(status_conn.recv(8))
        status_conn.close()
        return status
    except (TimeoutError, ValueError):
        return fail(f"no completion within {TIMEOUT:g}s per stage (stuck?) - check the tmux pane")
    finally:
        server.close()


if __name__ == "__main__":
    sys.exit(main())
