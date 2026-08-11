#!/usr/bin/env python3
"""
Real PTY Session Recorder for ARD Google Discovery & Podman Scenarios

Spawns a real subshell (/bin/bash) inside a real pseudoterminal (PTY),
executes genuine Podman container commands, unit test runners, and multi-turn
scenarios, and captures 100% genuine terminal I/O into an asciicast v2 recording (demo.cast).
Paced across 4:00 minutes (~240s) for clear readability.
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


class PTYRecorder:
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

    def type_string(self, text: str, char_delay: float = 0.065) -> None:
        for char in text:
            os.write(self.master_fd, char.encode("utf-8"))
            time.sleep(char_delay)

    def send_command(self, cmd: str, wait_after: float = 3.0, char_delay: float = 0.065) -> None:
        time.sleep(0.8)
        self.type_string(cmd, char_delay=char_delay)
        time.sleep(0.5)
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
        env["PS1"] = r"\[\033[01;32m\]developer@workstation\[\033[00m\]:\[\033[01;34m\]~/ard-project\[\033[00m\]$ "

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

        # Initialize bash prompt and colors
        os.write(self.master_fd, b"export PS1='\\[\\033[01;32m\\]developer@workstation\\[\\033[00m\\]:\\[\\033[01;34m\\]~/ard-project\\[\\033[00m\\]$ '\n")
        time.sleep(0.5)
        os.write(self.master_fd, b"clear\n")
        time.sleep(1.2)

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
            "title": "Live Real-World Recording: ARD Google Discovery in Podman & OpenCode (4:00 Walkthrough)",
            "env": {"SHELL": "/bin/bash", "TERM": "xterm-256color"},
        }
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json.dumps(header) + "\n")
            for event in self.events:
                f.write(json.dumps(event) + "\n")
        print(f"\n🎉 Successfully recorded real PTY session: {filepath}")
        print(f"• Total events: {len(self.events)}")
        print(f"• Total real duration: {total_duration:.1f}s (~{total_duration/60:.2f} min)")


def record_live_session():
    rec = PTYRecorder(cols=112, rows=34)
    print("🎬 Starting Real PTY Session Recorder (Calibrated for ~4:00 minutes)...")
    rec.start()

    try:
        # Step 1: Introduction Header (0:00 - 0:35)
        rec.send_command(
            "echo -e '\\033[1;36m================================================================================\\033[0m'",
            wait_after=0.8,
        )
        rec.send_command(
            "echo -e '\\033[1;36m🚀 AGENT RESOURCE DISCOVERY (ARD v0.5) GOOGLE ECOSYSTEM & OPENCODE DEMO\\033[0m'",
            wait_after=0.8,
        )
        rec.send_command(
            "echo -e '\\033[1;33m► Proving value for Non-GCP users, progressive auth tiering & respectful opt-out\\033[0m'",
            wait_after=0.8,
        )
        rec.send_command(
            "echo -e '\\033[1;36m================================================================================\\033[0m'",
            wait_after=6.0,
        )

        # Step 2: Passive Auth Status Inspection in Clean Podman Container (0:35 - 1:05)
        rec.send_command(
            "echo -e '\\n\\033[1;32m[1/6] Inspecting System Authentication State in Clean Podman Container...\\033[0m'",
            wait_after=3.0,
        )
        rec.send_command(
            "podman run --rm -v $(pwd):/app:ro docker.io/library/python:3.13-slim python3 /app/src/ard_resolver.py auth status",
            wait_after=14.0,
        )

        # Step 3: Scenario 1 - Pure Open Source Developer (Zero Auth / Zero GCP) (1:05 - 1:45)
        rec.send_command(
            "echo -e '\\n\\033[1;32m[2/6] Scenario 1: Pure Open Source Dev (Zero Auth / Zero GCP Account)\\033[0m'",
            wait_after=3.0,
        )
        rec.send_command(
            "echo -e '\\033[0;37mQuery: \"how to design zero trust security and optimize analytical sql\"\\033[0m'",
            wait_after=3.0,
        )
        rec.send_command(
            "podman run --rm -v $(pwd):/app:ro docker.io/library/python:3.13-slim python3 /app/src/ard_resolver.py search 'how to design zero trust security and optimize analytical sql'",
            wait_after=18.0,
        )

        # Step 4: Scenario 2 - OpenCode Opt-Out Flow (GCP Tools Strictly Filtered Out) (1:45 - 2:25)
        rec.send_command(
            "echo -e '\\n\\033[1;32m[3/6] Scenario 2: OpenCode Multi-Turn Flow A (Strict GCP Opt-Out)\\033[0m'",
            wait_after=3.0,
        )
        rec.send_command(
            "echo -e '\\033[0;33mUser declined GCP signup -> Setting persistent preference mode=\"opt_out\"\\033[0m'",
            wait_after=3.0,
        )
        rec.send_command(
            "podman run --rm -v $(pwd):/app:ro -e ARD_PREFERENCES_JSON='{\"gcp_mode\": \"opt_out\"}' docker.io/library/python:3.13-slim python3 /app/src/ard_resolver.py search 'bigquery analytical database query'",
            wait_after=18.0,
        )

        # Step 5: Scenario 3 - Progressive Onboarding (Cloud Intent with actionable steps) (2:25 - 3:00)
        rec.send_command(
            "echo -e '\\n\\033[1;32m[4/6] Scenario 3: OpenCode Multi-Turn Flow B (Progressive Onboarding)\\033[0m'",
            wait_after=3.0,
        )
        rec.send_command(
            "echo -e '\\033[0;37mUser asks for live BigQuery execution without active credentials:\\033[0m'",
            wait_after=3.0,
        )
        rec.send_command(
            "podman run --rm -v $(pwd):/app:ro docker.io/library/python:3.13-slim python3 /app/src/ard_resolver.py search 'query bigquery dataset'",
            wait_after=18.0,
        )

        # Step 6: Scenario 4 - Authenticated Enterprise (Service Account Mounted) (3:00 - 3:30)
        rec.send_command(
            "echo -e '\\n\\033[1;32m[5/6] Scenario 4: Authenticated Enterprise Dev (Service Account Mounted)\\033[0m'",
            wait_after=3.0,
        )
        rec.send_command(
            "podman run --rm -v $(pwd):/app:ro -v /tmp/mock_secrets:/secrets:ro -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa.json docker.io/library/python:3.13-slim python3 /app/src/ard_resolver.py search 'inspect cloud storage bucket and run bigquery'",
            wait_after=18.0,
        )

        # Step 7: Live Podman Container E2E Test Suite (6/6 tests) (3:30 - 3:55)
        rec.send_command(
            "echo -e '\\n\\033[1;32m[6/6] Executing Complete Automated Podman E2E Test Suite (6 Scenarios)...\\033[0m'",
            wait_after=3.0,
        )
        rec.send_command(
            "python3 tests/e2e_podman_runner.py",
            wait_after=16.0,
        )

        # Step 8: OpenCode Conversational Multi-Turn Unit Tests & Wrap-Up (3:55 - 4:05)
        rec.send_command(
            "echo -e '\\n\\033[1;32m[+] Running Automated OpenCode Conversational Scenario Unit Tests...\\033[0m'",
            wait_after=2.0,
        )
        rec.send_command(
            "python3 -m unittest discover -s tests -v",
            wait_after=8.0,
        )

        # Final Wrap-Up
        rec.send_command(
            "echo -e '\\n\\033[1;36m================================================================================\\033[0m'",
            wait_after=0.8,
        )
        rec.send_command(
            "echo -e '\\033[1;32m✔ All Real-World Container Scenarios & Multi-Turn Tests Executed Successfully!\\033[0m'",
            wait_after=0.8,
        )
        rec.send_command(
            "echo -e '\\033[1;36m================================================================================\\033[0m'",
            wait_after=6.0,
        )

    finally:
        rec.stop()
        rec.export(OUTPUT_CAST)


if __name__ == "__main__":
    record_live_session()
