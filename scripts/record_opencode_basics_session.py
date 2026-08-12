#!/usr/bin/env python3
"""
Record ARD 101 Basics Walkthrough:
1. Here's OpenCode (Agent Environment)
2. Here's how it searches (ARD Discovery)
3. Here's how it finds what it wants (AI Catalog Lookup)
4. Here's how it sets up the plugin (Plugin Enablement)
5. Here's how it uses the plugin (Skill Execution)
"""

import fcntl
import json
import os
import pty
import select
import struct
import subprocess
import sys
import termios
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_CAST = REPO_ROOT / "demo-basics.cast"

PROMPT_STR = "developer@workstation:~/ard-project$ "


class SynchronousPTYRecorder:
    def __init__(self, cols: int = 112, rows: int = 34):
        self.cols = cols
        self.rows = rows
        self.events = []
        self.start_time = None
        self.master_fd = None
        self.slave_fd = None
        self.process = None

    def set_winsize(self, fd: int) -> None:
        winsize = struct.pack("HHHH", self.rows, self.cols, 0, 0)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

    def record_event(self, text: str) -> None:
        if self.start_time is not None and text:
            ts = time.time() - self.start_time
            self.events.append([ts, "o", text])

    def drain_output(self, timeout: float = 0.05, record: bool = True) -> str:
        collected = ""
        while True:
            r, _, _ = select.select([self.master_fd], [], [], timeout)
            if self.master_fd in r:
                try:
                    data = os.read(self.master_fd, 4096)
                    if not data:
                        break
                    text = data.decode("utf-8", errors="replace")
                    if record:
                        self.record_event(text)
                    collected += text
                except (OSError, ValueError):
                    break
            else:
                break
        return collected

    def wait_for_prompt(self, timeout: float = 120.0) -> bool:
        start = time.time()
        buf = ""
        while time.time() - start < timeout:
            r, _, _ = select.select([self.master_fd], [], [], 0.05)
            if self.master_fd in r:
                try:
                    data = os.read(self.master_fd, 4096)
                    if not data:
                        break
                    text = data.decode("utf-8", errors="replace")
                    self.record_event(text)
                    buf += text
                    if PROMPT_STR in buf[-80:] or "developer@workstation" in buf[-80:]:
                        return True
                except (OSError, ValueError):
                    break
        return False

    def type_string(self, text: str, char_delay: float = 0.035) -> None:
        for char in text:
            os.write(self.master_fd, char.encode("utf-8"))
            self.drain_output(timeout=0.005)
            time.sleep(char_delay)

    def send_turn(self, cmd: str, pause_after: float = 3.0, char_delay: float = 0.035, timeout: float = 120.0) -> None:
        self.drain_output(timeout=0.05, record=False)
        time.sleep(0.3)
        self.type_string(cmd, char_delay=char_delay)
        time.sleep(0.2)
        os.write(self.master_fd, b"\n")
        self.wait_for_prompt(timeout=timeout)
        time.sleep(pause_after)

    def start(self) -> None:
        self.master_fd, self.slave_fd = pty.openpty()
        self.set_winsize(self.master_fd)
        self.set_winsize(self.slave_fd)

        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        env["COLUMNS"] = str(self.cols)
        env["LINES"] = str(self.rows)

        self.process = subprocess.Popen(
            ["/bin/bash", "--norc", "--noprofile"],
            stdin=self.slave_fd,
            stdout=self.slave_fd,
            stderr=self.slave_fd,
            cwd=str(REPO_ROOT),
            env=env,
            close_fds=True,
        )
        os.close(self.slave_fd)

        self.start_time = time.time()

        init_cmds = f"""
export PS1='{PROMPT_STR}'
clear
"""
        os.write(self.master_fd, init_cmds.encode("utf-8"))
        time.sleep(0.4)
        self.drain_output(timeout=0.2, record=False)
        os.write(self.master_fd, b"clear\n")
        time.sleep(0.5)
        self.drain_output(timeout=0.2, record=False)
        self.events = []
        self.start_time = time.time()

    def stop(self) -> None:
        try:
            self.type_string("exit\n", char_delay=0.01)
            time.sleep(0.3)
            self.drain_output(timeout=0.2)
        except Exception:
            pass
        try:
            os.close(self.master_fd)
        except OSError:
            pass
        if self.process.poll() is None:
            self.process.terminate()

    def export(self, filepath: Path, max_idle: float = 2.5) -> None:
        start_idx = 0
        for i, ev in enumerate(self.events):
            if ev[2] == ".":
                start_idx = i
                break
        raw_events = self.events[start_idx:] if start_idx < len(self.events) else self.events

        compressed_events = []
        if raw_events:
            prev_raw_ts = raw_events[0][0]
            curr_comp_ts = 0.0
            for raw_ts, kind, text in raw_events:
                delta = raw_ts - prev_raw_ts
                clamped_delta = min(delta, max_idle)
                curr_comp_ts += clamped_delta
                compressed_events.append([round(curr_comp_ts, 3), kind, text])
                prev_raw_ts = raw_ts

        header = {
            "version": 2,
            "width": self.cols,
            "height": self.rows,
            "timestamp": int(self.start_time),
            "title": "ARD & Agent Plugins Basics: 5-Step Lifecycle Walkthrough",
            "env": {"SHELL": "/bin/bash", "TERM": "xterm-256color"},
        }
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json.dumps(header) + "\n")
            for event in compressed_events:
                f.write(json.dumps(event) + "\n")

        raw_dur = self.events[-1][0] if self.events else 0
        comp_dur = compressed_events[-1][0] if compressed_events else 0
        print(f"\n🎉 Successfully recorded & compressed session: {filepath}")
        print(f"• Total events: {len(compressed_events)}")
        print(f"• Raw duration: {raw_dur:.1f}s | Compressed duration: {comp_dur:.1f}s (~{comp_dur/60:.2f} min)")


def record_basics_session():
    rec = SynchronousPTYRecorder(cols=112, rows=34)
    print("🎬 Starting ARD 101 Basics OpenCode Agent Recorder...")
    rec.start()

    try:
        # Title Banner
        rec.send_turn("./scripts/banner_basics.sh 0", pause_after=2.0, char_delay=0.025)

        # ---------------------------------------------------------------------
        # Step 1: The Agent Environment (Here's OpenCode)
        # ---------------------------------------------------------------------
        rec.send_turn("./scripts/banner_basics.sh 1", pause_after=1.5, char_delay=0.025)
        rec.send_turn(
            './ask "What resource discovery plugins are active in your environment?"',
            pause_after=3.0,
            char_delay=0.035,
        )

        # ---------------------------------------------------------------------
        # Step 2: Capability Search (Here's How It Searches via ARD)
        # ---------------------------------------------------------------------
        rec.send_turn("./scripts/banner_basics.sh 2", pause_after=1.5, char_delay=0.025)
        rec.send_turn(
            './ask "I need help with database schema design and SQL query optimization. What tools or skills can help?"',
            pause_after=3.5,
            char_delay=0.035,
        )

        # ---------------------------------------------------------------------
        # Step 3: AI Catalog Lookup (Here's How It Finds What It Wants)
        # ---------------------------------------------------------------------
        rec.send_turn("./scripts/banner_basics.sh 3", pause_after=1.5, char_delay=0.025)
        rec.send_turn(
            './ask "Inspect the details and capabilities of the BigQuery guidelines skill from the catalog."',
            pause_after=3.5,
            char_delay=0.035,
        )

        # ---------------------------------------------------------------------
        # Step 4: Plugin Setup & Enablement (Here's How It Installs / Loads the Plugin)
        # ---------------------------------------------------------------------
        rec.send_turn("./scripts/banner_basics.sh 4", pause_after=1.5, char_delay=0.025)
        rec.send_turn(
            './ask "Enable and load the BigQuery guidelines skill for my session."',
            pause_after=3.0,
            char_delay=0.035,
        )

        # ---------------------------------------------------------------------
        # Step 5: Normal Execution (Here's How It Uses the Plugin to Solve Tasks)
        # ---------------------------------------------------------------------
        rec.send_turn("./scripts/banner_basics.sh 5", pause_after=1.5, char_delay=0.025)
        rec.send_turn(
            './ask "Using the loaded skill, provide the optimal schema design and partitioning strategy for an e-commerce orders table with 50M rows."',
            pause_after=4.5,
            char_delay=0.035,
        )

    finally:
        rec.stop()
        rec.export(OUTPUT_CAST, max_idle=2.5)


if __name__ == "__main__":
    record_basics_session()
