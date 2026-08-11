#!/usr/bin/env python3
"""
Real OpenCode AI Agent PTY Session Recorder

Executes the actual OpenCode binary (opencode run) in the container, driving real
LLM tool calls through the ARD MCP server:
- Uses scripts/banner.sh for instant scenario header rendering.
- Step 1: opencode mcp list -> Confirms ard-google-discovery connected.
- Step 2: opencode run -> User asks for security design & SQL optimization; OpenCode autonomously calls ard_search live.
- Step 3: opencode run --continue -> User opts out; OpenCode autonomously calls ard_set_preference(mode="opt_out") and re-searches.
- Step 4: opencode run with Service Account -> OpenCode calls ard_auth_status and ard_search live with active credentials.
- Step 5: Complete Podman OpenCode E2E test suite (5/5 passing).
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

    def type_string(self, text: str, char_delay: float = 0.05) -> None:
        for char in text:
            os.write(self.master_fd, char.encode("utf-8"))
            time.sleep(char_delay)

    def send_command(self, cmd: str, wait_after: float = 3.0, char_delay: float = 0.05) -> None:
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
    print("🎬 Starting Real OpenCode AI Agent PTY Recorder...")
    rec.start()

    try:
        # Title Banner (Instant shortcut via banner.sh)
        rec.send_command("./scripts/banner.sh 0", wait_after=4.0, char_delay=0.03)

        # 1. Verify OpenCode MCP Connection
        rec.send_command(
            "podman run --rm -v $(pwd):/workspace/ard-plugin-exploration --entrypoint /bin/sh localhost/ard-opencode:latest -c 'cd /workspace/ard-plugin-exploration && opencode mcp list'",
            wait_after=6.0,
            char_delay=0.04,
        )

        # 2. Scenario 1: OpenCode searches for zero-trust security & SQL optimization
        rec.send_command("./scripts/banner.sh 1", wait_after=3.0, char_delay=0.03)
        rec.send_command(
            "podman run --rm -v $(pwd):/workspace/ard-plugin-exploration --entrypoint /bin/sh localhost/ard-opencode:latest -c \"cd /workspace/ard-plugin-exploration && opencode run --model opencode/deepseek-v4-flash-free 'I need to design a zero trust security architecture and optimize my analytical SQL queries. Find tools for me.'\"",
            wait_after=14.0,
            char_delay=0.04,
        )

        # 3. Scenario 2: Multi-turn Opt-Out Flow (User declines GCP -> OpenCode calls ard_set_preference(mode="opt_out"))
        rec.send_command("./scripts/banner.sh 2", wait_after=3.0, char_delay=0.03)
        rec.send_command(
            "podman run --rm -v $(pwd):/workspace/ard-plugin-exploration --entrypoint /bin/sh localhost/ard-opencode:latest -c \"cd /workspace/ard-plugin-exploration && opencode run --model opencode/deepseek-v4-flash-free --continue 'I do not have a GCP account and never want to use Google Cloud. Opt me out permanently so you never show me cloud tools, and tell me what offline tools I can use.'\"",
            wait_after=14.0,
            char_delay=0.04,
        )

        # 4. Scenario 3: Authenticated Enterprise Dev with Service Account
        rec.send_command("./scripts/banner.sh 3", wait_after=3.0, char_delay=0.03)
        rec.send_command(
            "podman run --rm -v $(pwd):/workspace/ard-plugin-exploration -v /tmp/mock_secrets:/secrets:ro -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa.json --entrypoint /bin/sh localhost/ard-opencode:latest -c \"cd /workspace/ard-plugin-exploration && opencode run --model opencode/deepseek-v4-flash-free 'Check auth status with ard_auth_status and search for cloud storage tools'\"",
            wait_after=14.0,
            char_delay=0.04,
        )

        # 5. Scenario 4: Automated E2E Test Suite Execution in Podman Container
        rec.send_command("./scripts/banner.sh 4", wait_after=3.0, char_delay=0.03)
        rec.send_command(
            "python3 tests/e2e_podman_runner.py",
            wait_after=16.0,
            char_delay=0.04,
        )

    finally:
        rec.stop()
        rec.export(OUTPUT_CAST)


if __name__ == "__main__":
    record_opencode_session()
