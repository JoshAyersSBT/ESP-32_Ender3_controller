# state.py

class AppState:
    def __init__(self):
        self.network_mode = "UNKNOWN"
        self.ip_address = "0.0.0.0"
        self.printer_connected = False
        self.printer_state = "idle"
        self.current_file = None
        self.progress_percent = 0.0
        self.nozzle_temp = None
        self.nozzle_target = None
        self.bed_temp = None
        self.bed_target = None
        self.last_message = "booting"
        self.last_error = None

    def as_dict(self):
        return {
            "network_mode": self.network_mode,
            "ip_address": self.ip_address,
            "printer_connected": self.printer_connected,
            "printer_state": self.printer_state,
            "current_file": self.current_file,
            "progress_percent": self.progress_percent,
            "nozzle_temp": self.nozzle_temp,
            "nozzle_target": self.nozzle_target,
            "bed_temp": self.bed_temp,
            "bed_target": self.bed_target,
            "last_message": self.last_message,
            "last_error": self.last_error,
        }