#!/usr/bin/env python3
"""
Real OpenCode AI Agent PTY Session Recorder (100% Deterministic Prompt Sync & Time Compression)

Drives the actual OpenCode binary via the ./ask shortcut:
- Strictly waits for bash prompt to return before typing the next turn (0% collision guarantee).
- Automatically compresses LLM thinking timeframes and idle pauses to produce a punchy, high-signal video.
- Resets per scenario using `./scripts/banner.sh <N>`.
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
OUTPUT_CAST = REPO_ROOT / "demo.cast"

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
        ts = round(time.time() - self.start_time, 3)
        self.events.append([ts, "o", text])

    def drain_output(self, timeout: float = 0.1, record: bool = True) -> str:
        """Reads all available output from master_fd."""
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
        """Reads output continuously until PROMPT_STR appears at the end of the stream."""
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
                    # Check if the shell prompt is in the most recent output
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

    def send_turn(self, cmd: str, pause_after: float = 2.5, char_delay: float = 0.035, timeout: float = 120.0) -> None:
        # Pre-command drain
        self.drain_output(timeout=0.05, record=False)
        time.sleep(0.3)

        # Type command character by character
        self.type_string(cmd, char_delay=char_delay)
        time.sleep(0.2)
        
        # Write newline to execute command
        os.write(self.master_fd, b"\n")

        # Wait strictly until the command finishes and the shell prompt returns (no intermediate drain!)
        success = self.wait_for_prompt(timeout=timeout)
        if not success:
            print(f"⚠️ Warning: Timeout waiting for prompt after: '{cmd[:40]}...'")

        # Human reading pause after full response is printed
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

        # Set clean bash prompt & helpers
        init_cmds = f"""
export PS1='{PROMPT_STR}'
function gcloud() {{
  if [[ "$1" == "auth" && "$2" == "application-default" && "$3" == "login" ]]; then
    ./scripts/do_oauth_login.sh
  else
    command gcloud "$@"
  fi
}}
export -f gcloud
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
        # Filter out initial shell setup noise
        start_idx = 0
        for i, ev in enumerate(self.events):
            if ev[2] == ".":  # First keystroke of first command
                start_idx = i
                break
        raw_events = self.events[start_idx:] if start_idx < len(self.events) else self.events

        # Time compression: clamp any idle pause > max_idle (preserves 2.5s reading pauses)
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
            "title": "Live Real-World OpenCode Agent Execution with ARD MCP Server",
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


def record_opencode_session():
    rec = SynchronousPTYRecorder(cols=112, rows=34)
    print("🎬 Starting 100% Synchronized OpenCode AI Agent Recorder...")
    rec.start()

    try:
        # Title Banner
        rec.send_turn("./scripts/banner.sh 0", pause_after=2.0, char_delay=0.025)

        # ---------------------------------------------------------------------
        # Scenario 1: Tier 0 Pure Public Discovery (Zero Auth Counterpoint)
        # ---------------------------------------------------------------------
        rec.send_turn("./scripts/banner.sh 1", pause_after=1.5, char_delay=0.025)
        rec.send_turn(
            './ask "I need best practices to optimize my SQL queries and design zero-trust security. Search tools for me."',
            pause_after=3.5,
            char_delay=0.035,
        )

        # ---------------------------------------------------------------------
        # Scenario 2: Cloud Intent -> User Opts Out ("No with an opt out")
        # ---------------------------------------------------------------------
        rec.send_turn("./scripts/banner.sh 2", pause_after=1.5, char_delay=0.025)
        rec.send_turn(
            './ask "I want to run a live analytical query on a 100GB sales dataset in BigQuery. What tool can do this?"',
            pause_after=2.5,
            char_delay=0.035,
        )
        rec.send_turn(
            './ask "No with an opt out"',
            pause_after=3.5,
            char_delay=0.035,
        )

        # ---------------------------------------------------------------------
        # Scenario 3: Cloud Intent -> User Onboards ("Yes") -> Human OAuth -> Live BigQuery
        # ---------------------------------------------------------------------
        rec.send_turn("./scripts/banner.sh 3", pause_after=1.5, char_delay=0.025)
        rec.send_turn(
            './ask "I want to query a public BigQuery dataset. What tool can do this?"',
            pause_after=2.5,
            char_delay=0.035,
        )
        rec.send_turn(
            './ask "Yes, please log me in"',
            pause_after=2.5,
            char_delay=0.035,
        )
        rec.send_turn(
            "gcloud auth application-default login --no-launch-browser",
            pause_after=2.5,
            char_delay=0.03,
        )
        rec.send_turn(
            './ask "Run a query to find the 5 most popular names in 2020 from bigquery-public-data.usa_names.usa_1910_current and summarize the results."',
            pause_after=4.0,
            char_delay=0.035,
        )

        # ---------------------------------------------------------------------
        # Scenario 4: Automated E2E Test Suite Execution in Container
        # ---------------------------------------------------------------------
        rec.send_turn("./scripts/banner.sh 4", pause_after=1.5, char_delay=0.025)
        rec.send_turn(
            "python3 tests/e2e_podman_runner.py",
            pause_after=4.0,
            char_delay=0.03,
            timeout=300.0,
        )

    finally:
        rec.stop()
        rec.export(OUTPUT_CAST, max_idle=2.5)


if __name__ == "__main__":
    record_opencode_session()
