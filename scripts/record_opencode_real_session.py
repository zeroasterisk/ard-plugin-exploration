#!/usr/bin/env python3
"""
Real OpenCode AI Agent PTY Session Recorder (3 Core Scenarios)

Executes the actual OpenCode binary (opencode run) in the container, driving real
LLM tool calls through the ARD MCP server for the 3 focused scenarios:
- Scenario 1: Tier 0 Pure Public Discovery (Zero-Auth Counterpoint)
- Scenario 2: Cloud Intent -> User: "No with an opt out" -> OpenCode calls ard_set_preference(mode="opt_out") & silences GCP
- Scenario 3: Cloud Intent -> User: "Yes" -> OpenCode facilitates easy onboarding & unlocks BigQuery
- Automated E2E Test Suite (4/4 passing)
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
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_CAST = REPO_ROOT / "demo.cast"


class OpenCodePTYRecorder:
    def __init__(self, cols: int = 112, rows: int = 34):
        self.cols = cols
        self.rows = rows
        self.events = []
        self.start_time = None
        self.master_fd = None
        self.slave_fd = None
        self.process = None
        self.running = False

    def set_winsize(self, fd: int) -> None:
        winsize = struct.pack("HHHH", self.rows, self.cols, 0, 0)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

    def reader_loop(self) -> None:
        while self.running:
            try:
                r, _, _ = select.select([self.master_fd], [], [], 0.05)
                if self.master_fd in r:
                    data = os.read(self.master_fd, 4096)
                    if not data:
                        break
                    ts = round(time.time() - self.start_time, 3)
                    text = data.decode("utf-8", errors="replace")
                    self.events.append([ts, "o", text])
            except (OSError, ValueError):
                break

    def type_string(self, text: str, char_delay: float = 0.045) -> None:
        for char in text:
            os.write(self.master_fd, char.encode("utf-8"))
            time.sleep(char_delay)

    def send_command(self, cmd: str, wait_after: float = 3.0, char_delay: float = 0.045) -> None:
        time.sleep(0.6)
        self.type_string(cmd, char_delay=char_delay)
        time.sleep(0.4)
        os.write(self.master_fd, b"\n")
        time.sleep(wait_after)

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
        self.running = True
        self.reader_thread = threading.Thread(target=self.reader_loop, daemon=True)
        self.reader_thread.start()

        os.write(self.master_fd, b"export PS1='\\[\\033[01;32m\\]developer@workstation\\[\\033[00m\\]:\\[\\033[01;34m\\]~/ard-project\\[\\033[00m\\]$ '\n")
        time.sleep(0.5)
        os.write(self.master_fd, b"clear\n")
        time.sleep(1.0)

    def stop(self) -> None:
        self.send_command("exit", wait_after=1.0)
        self.running = False
        if self.reader_thread.is_alive():
            self.reader_thread.join(timeout=2.0)
        try:
            os.close(self.master_fd)
        except OSError:
            pass
        if self.process.poll() is None:
            self.process.terminate()

    def export(self, filepath: Path) -> None:
        total_duration = round(time.time() - self.start_time, 2)
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
            for event in self.events:
                f.write(json.dumps(event) + "\n")
        print(f"\n🎉 Successfully recorded real OpenCode agent session: {filepath}")
        print(f"• Total events: {len(self.events)}")
        print(f"• Total real duration: {total_duration:.1f}s (~{total_duration/60:.2f} min)")


def record_opencode_session():
    rec = OpenCodePTYRecorder(cols=112, rows=34)
    print("🎬 Starting Real OpenCode AI Agent PTY Recorder (3 Core Scenarios)...")
    rec.start()

    try:
        # Title Banner
        rec.send_command("./scripts/banner.sh 0", wait_after=3.5, char_delay=0.03)

        # Verify OpenCode MCP Connection
        rec.send_command(
            "podman run --rm -v $(pwd):/workspace/ard-plugin-exploration --entrypoint /bin/sh localhost/ard-opencode:latest -c 'cd /workspace/ard-plugin-exploration && opencode mcp list'",
            wait_after=6.0,
            char_delay=0.035,
        )

        # ---------------------------------------------------------------------
        # Scenario 1: Tier 0 Pure Public Discovery (Zero Auth Counterpoint)
        # ---------------------------------------------------------------------
        rec.send_command("./scripts/banner.sh 1", wait_after=3.0, char_delay=0.03)
        rec.send_command(
            "podman run --rm -v $(pwd):/workspace/ard-plugin-exploration --entrypoint /bin/sh localhost/ard-opencode:latest -c \"cd /workspace/ard-plugin-exploration && opencode run --model opencode/deepseek-v4-flash-free 'I need best practices to optimize my SQL queries and design zero-trust security. Search tools for me.'\"",
            wait_after=14.0,
            char_delay=0.035,
        )

        # ---------------------------------------------------------------------
        # Scenario 2: Unauthenticated Cloud Intent -> User Opts Out ("No with an opt out")
        # ---------------------------------------------------------------------
        rec.send_command("./scripts/banner.sh 2", wait_after=3.0, char_delay=0.03)
        # Turn 1: User asks for BigQuery
        rec.send_command(
            "podman run --rm -v $(pwd):/workspace/ard-plugin-exploration --entrypoint /bin/sh localhost/ard-opencode:latest -c \"cd /workspace/ard-plugin-exploration && rm -rf /workspace/.config/ard && opencode run --model opencode/deepseek-v4-flash-free 'I want to run a live analytical query on a 100GB sales dataset in BigQuery. What tool can do this?'\"",
            wait_after=14.0,
            char_delay=0.035,
        )
        # Turn 2: User responds "No with an opt out"
        rec.send_command(
            "podman run --rm -v $(pwd):/workspace/ard-plugin-exploration --entrypoint /bin/sh localhost/ard-opencode:latest -c \"cd /workspace/ard-plugin-exploration && opencode run --model opencode/deepseek-v4-flash-free --continue 'No with an opt out'\"",
            wait_after=14.0,
            char_delay=0.035,
        )

        # ---------------------------------------------------------------------
        # Scenario 3: Unauthenticated Cloud Intent -> User Onboards ("Yes")
        # ---------------------------------------------------------------------
        rec.send_command("./scripts/banner.sh 3", wait_after=3.0, char_delay=0.03)
        # Turn 1: User asks for BigQuery
        rec.send_command(
            "podman run --rm -v $(pwd):/workspace/ard-plugin-exploration --entrypoint /bin/sh localhost/ard-opencode:latest -c \"cd /workspace/ard-plugin-exploration && rm -rf /workspace/.config/ard && opencode run --model opencode/deepseek-v4-flash-free 'I want to query a public BigQuery dataset. What tool can do this?'\"",
            wait_after=14.0,
            char_delay=0.035,
        )
        # Turn 2: User responds "Yes, please log me in"
        rec.send_command(
            "podman run --rm -v $(pwd):/workspace/ard-plugin-exploration --entrypoint /bin/sh localhost/ard-opencode:latest -c \"cd /workspace/ard-plugin-exploration && opencode run --model opencode/deepseek-v4-flash-free --continue 'Yes, please log me in'\"",
            wait_after=14.0,
            char_delay=0.035,
        )

        # ---------------------------------------------------------------------
        # Scenario 4: Automated E2E Test Suite Execution in Container
        # ---------------------------------------------------------------------
        rec.send_command("./scripts/banner.sh 4", wait_after=3.0, char_delay=0.03)
        rec.send_command(
            "python3 tests/e2e_podman_runner.py",
            wait_after=16.0,
            char_delay=0.035,
        )

    finally:
        rec.stop()
        rec.export(OUTPUT_CAST)


if __name__ == "__main__":
    record_opencode_session()
