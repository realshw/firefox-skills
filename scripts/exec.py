#!/usr/bin/env python3
"""exec.py — pipe one Python block into the live REPL and echo what it printed.

    scripts/exec.py <<'PY'
    print(driver.current_url)
    PY

The block runs in the REPL's globals, so the browser session survives between runs, and travels through
send-keys as one base64 line (send-keys mangles literal newlines). Raised exceptions echo as a single
"Type: message" line and exit 1 here; their tracebacks stay in the REPL. Blocks run in the REPL's cwd,
the skill root, so snippets import as modules.
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

# Runs in a throwaway locals dict, so it leaves no names in the shared globals. The socket file object is
# the sink, so output streams out as the block prints, and the status byte it writes last says whether the
# block raised - that byte is the whole exit code. Braces are doubled: this template goes through format.
WRAPPER = '''\
import contextlib
import socket

with (
    socket.create_connection({addr!r}) as conn,
    conn.makefile("w", encoding="utf-8", errors="backslashreplace") as sink,
    contextlib.redirect_stdout(sink),
    contextlib.redirect_stderr(sink),
):
    try:
        exec(compile({block!r}, "<block>", "exec"), globals())
    except BaseException as exc:
        sink.write(f"{{type(exc).__name__}}: {{exc}}\\n")
        sink.write("\\x01")
    else:
        sink.write("\\x00")
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
        return fail("takes no arguments - the block comes from stdin")
    block = read_block()
    if block is None:
        return 2

    socket.setdefaulttimeout(TIMEOUT)
    with socket.create_server(("127.0.0.1", 0)) as server:
        wrapper = WRAPPER.format(addr=server.getsockname(), block=block)
        encoded = base64.b64encode(wrapper.encode()).decode()
        command = f"exec(__import__('base64').b64decode({encoded!r}).decode(), globals(), {{}})"

        sent = subprocess.run(["tmux", "send-keys", "-t", TARGET, command, "Enter"],
                              capture_output=True, text=True)
        if sent.returncode:
            reason = (sent.stderr or sent.stdout).strip() or f"tmux exited {sent.returncode}"
            if "can't find" in reason or "no server" in reason:
                return fail(f"{TARGET} is gone - ask the user to start it again, then retry.")
            # tmux 3.8 refuses a command string over ~16 KiB and types nothing at all: say so, and how
            # big the block was, instead of blaming a dead pane. base64 inflates a block by 4/3 first.
            return fail(f"tmux refused the block ({reason}); its command was {len(command)} chars - over "
                        f"the ~16 KiB ceiling, so split the block into two runs")

        try:
            conn, _ = server.accept()
            data = conn.makefile("rb").read()  # to EOF: output plus its status byte
        except TimeoutError:
            return fail(f"no completion within {TIMEOUT:g}s (stuck?) - check the tmux pane")

        sys.stdout.buffer.write(data[:-1])  # what the block printed, minus that byte
        return int(data[-1:] != b"\x00")


if __name__ == "__main__":
    sys.exit(main())
