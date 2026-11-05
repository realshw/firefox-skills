# Stray geckodrivers make NewSession stall on "Session already started", and survive SIGINT. Match comm
# only, never cmdline — a tmux session's cmdline contains "geckodriver" and pkill -f would take the
# browser down with it. Skip zombies; Firefox + marionette stay alive.
import os
import time

from snippets.common.connect import connect


def reattach():
    """Kill stray geckodrivers, then attach and return the driver."""
    strays = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            comm, state = open("/proc/%s/stat" % pid).read().split()[1:3]
        except OSError:
            continue
        if comm == "(geckodriver)" and state != "Z":
            strays.append(int(pid))

    if strays:
        print("REATTACH: killing stray geckodriver", " ".join(map(str,
                                                                  strays)))
        for pid in strays:
            try:
                os.kill(pid, 9)
            except OSError:
                pass  # already gone between scan and kill
        time.sleep(1)
    return connect()
