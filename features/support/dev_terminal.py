import subprocess
import sys
import threading
import time
from queue import Empty, Queue


# How long (seconds) to wait after writing a command before declaring
# that all response lines have arrived.  Raise if your CLI is slow to
# respond; lower for faster test runs.
_RESPONSE_TIMEOUT = 0.5
_LINE_IDLE_TIMEOUT = 0.1  # Stop collecting once no new line arrives within this window


class DevTerminal:
    """
    A thin wrapper around the CLI subprocess that lets behave tests
    drive it as if they were a human sitting at a terminal.

    Lifecycle
    ---------
    1.  ``send_command("run")``   → spawns the CLI process and returns its
                                    welcome banner.
    2.  ``send_command("/foo …")`` → writes the command to the process stdin,
                                    collects the response, and returns it.
    3.  ``get_output()``          → returns the output captured from the most
                                    recent command (useful when the process was
                                    already started by *before_scenario*).
    4.  ``is_running()``          → ``True`` while the process is alive.

    Accumulated log
    ---------------
    ``terminal_text`` is an ever-growing string containing every byte the CLI
    has ever printed — useful for debugging.  The helpers below (append /
    write / flush / get) operate on it and mirror the original stub API.
    """

    def __init__(self) -> None:
        self.terminal_text: str = ""

        self._process: subprocess.Popen | None = None
        self._last_output: str = ""

        # Lines arriving from the subprocess stdout land in this queue so
        # the main thread can consume them without busy-waiting.
        self._line_queue: Queue[str] = Queue()
        self._reader_thread: threading.Thread | None = None

    # ──────────────────────────────────────────────────────────────────────────
    # Public API expected by environment.py and the step implementations
    # ──────────────────────────────────────────────────────────────────────────

    def send_command(self, command: str) -> str:
        """
        Send *command* to the CLI and return its response as a string.

        Passing ``"run"`` is special: if no process is running it spawns
        one and returns the welcome banner; if a process is already alive
        it simply returns the buffered output so far (idempotent restart
        from *before_scenario*).
        """
        if command == "run":
            if not self.is_running():
                self._spawn()
            # Drain whatever the CLI printed on startup (welcome banner).
            self._last_output = self._collect_output()
            return self._last_output

        if not self.is_running():
            raise RuntimeError(
                "Cannot send command — CLI process is not running. "
                "Call send_command('run') first."
            )

        self._write_stdin(command)
        self._last_output = self._collect_output()
        return self._last_output

    def get_output(self) -> str:
        """Return the response captured from the most recent command."""
        return self._last_output

    def is_running(self) -> bool:
        """Return ``True`` while the CLI subprocess is alive."""
        return self._process is not None and self._process.poll() is None

    # ──────────────────────────────────────────────────────────────────────────
    # Original stub API (fixed and promoted to proper instance methods)
    # ──────────────────────────────────────────────────────────────────────────

    def append_to_terminal(self, text: str) -> None:
        """Append *text* to the accumulated terminal log."""
        self.terminal_text += text

    def write_full_text(self, text: str) -> None:
        """Replace the accumulated terminal log with *text*."""
        self.terminal_text = text

    def flush(self) -> None:
        """Simulate a real terminal screen flush (no-op in tests)."""
        return

    def get_terminal_text(self) -> str:
        """Return the full accumulated terminal log."""
        return self.terminal_text

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _spawn(self) -> None:
        """Start the CLI subprocess and wire up a background stdout reader."""
        self._process = subprocess.Popen(
            # Run the CLI app as a module so relative imports resolve correctly.
            [sys.executable, "-m", "apps.cli_app"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,   # merge stderr into stdout
            text=True,
            bufsize=1,                  # line-buffered
        )
        self._line_queue = Queue()
        self._reader_thread = threading.Thread(
            target=self._stdout_reader,
            daemon=True,               # dies automatically when the test suite exits
        )
        self._reader_thread.start()

    def _stdout_reader(self) -> None:
        """
        Background thread: read stdout one line at a time and push each
        line onto ``_line_queue``.  Exits when the process closes its pipe.
        """
        for line in self._process.stdout:
            self._line_queue.put(line)
        # Sentinel — signals that the process has exited and there is no more
        # output to read.
        self._line_queue.put(None)

    def _collect_output(self) -> str:
        """
        Drain ``_line_queue`` until no new line arrives within
        ``_LINE_IDLE_TIMEOUT`` seconds (or the sentinel ``None`` is seen).

        Returns the collected lines joined as a single string and also
        appends them to the full ``terminal_text`` log.
        """
        # Give the CLI a moment to start producing output before we begin
        # polling.
        time.sleep(_RESPONSE_TIMEOUT)

        lines: list[str] = []
        while True:
            try:
                line = self._line_queue.get(timeout=_LINE_IDLE_TIMEOUT)
                if line is None:
                    # Process has exited — stop collecting.
                    break
                lines.append(line)
            except Empty:
                # No new line arrived within the idle window → response is done.
                break

        output = "".join(lines)
        self.append_to_terminal(output)
        return output

    def _write_stdin(self, command: str) -> None:
        """Write *command* followed by a newline to the CLI's stdin."""
        self._process.stdin.write(command + "\n")
        self._process.stdin.flush()