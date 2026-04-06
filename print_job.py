# print_job.py

import os
import time
import config


class PrintJobManager:
    def __init__(self, state, printer):
        self.state = state
        self.printer = printer
        self.active = False
        self.paused = False
        self.stop_requested = False
        self.file_path = None
        self.file_name = None
        self.file_size = 0
        self.bytes_sent = 0
        self.waiting_for_ok = False
        self.last_send_ms = 0
        self.last_ok_ms = 0
        self.stream = None
        self._line_number = 0

    def start(self, file_path, file_name=None):
        if self.active:
            raise RuntimeError("A print is already active")

        st = os.stat(file_path)
        self.file_size = st[6] if len(st) > 6 else 0
        self.stream = open(file_path, "rb")
        self.file_path = file_path
        self.file_name = file_name or file_path.rsplit("/", 1)[-1]
        self.bytes_sent = 0
        self.waiting_for_ok = False
        self.stop_requested = False
        self.paused = False
        self.active = True
        self._line_number = 0

        self.state.current_file = self.file_name
        self.state.progress_percent = 0.0
        self.state.printer_state = "printing"
        self.state.last_message = "print started"
        self.state.last_error = None

    def pause(self):
        if self.active:
            self.paused = True
            self.state.printer_state = "paused"
            self.state.last_message = "print paused"

    def resume(self):
        if self.active:
            self.paused = False
            self.state.printer_state = "printing"
            self.state.last_message = "print resumed"

    def stop(self):
        if self.active:
            self.stop_requested = True
            self.state.last_message = "stop requested"

    def update(self):
        if not self.active:
            return

        if self.stop_requested:
            self._finish("stopped")
            return

        if self.paused:
            return

        if self.waiting_for_ok:
            return

        raw = self.stream.readline()
        if not raw:
            self._finish("complete")
            return

        self.bytes_sent += len(raw)
        line = raw.decode("utf-8", "ignore").strip()
        if not line or line.startswith(";"):
            self._update_progress()
            return

        self._line_number += 1
        self.printer.send_command(line)
        self.waiting_for_ok = True
        self.last_send_ms = time.ticks_ms()
        self._update_progress()

    def notify_ok(self):
        self.waiting_for_ok = False
        self.last_ok_ms = time.ticks_ms()

    def notify_error(self, line):
        self.state.last_error = line
        self._finish("error")

    def _update_progress(self):
        if self.file_size > 0:
            self.state.progress_percent = round((self.bytes_sent / self.file_size) * 100.0, 2)
        else:
            self.state.progress_percent = 0.0

    def _finish(self, outcome):
        try:
            if self.stream:
                self.stream.close()
        except Exception:
            pass

        self.stream = None
        self.active = False
        self.paused = False
        self.stop_requested = False
        self.waiting_for_ok = False

        if outcome == "complete":
            self.state.printer_state = "idle"
            self.state.progress_percent = 100.0
            self.state.last_message = "print complete"
        elif outcome == "stopped":
            self.state.printer_state = "idle"
            self.state.last_message = "print stopped"
        else:
            self.state.printer_state = "error"
            self.state.last_message = "print failed"

        self.state.current_file = None
        self.file_path = None
        self.file_name = None
        self.file_size = 0
        self.bytes_sent = 0
        self._line_number = 0