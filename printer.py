# printer.py

from machine import UART, Pin
import config


class PrinterController:
    def __init__(self, state, job_manager=None):
        self.state = state
        self.job_manager = job_manager
        self.uart = UART(
            config.PRINTER_UART_ID,
            baudrate=config.PRINTER_BAUDRATE,
            tx=Pin(config.PRINTER_TX_PIN),
            rx=Pin(config.PRINTER_RX_PIN),
            timeout=config.UART_TIMEOUT_MS,
        )
        self._rx_buffer = b""
        self.state.last_message = "printer uart initialized"

    def set_job_manager(self, job_manager):
        self.job_manager = job_manager

    def send_line(self, line):
        if not line.endswith("\n"):
            line += "\n"
        self.uart.write(line.encode("utf-8"))

    def send_command(self, cmd):
        print("[printer] >>", cmd)
        self.send_line(cmd)

    def poll(self):
        data = self.uart.read()
        if not data:
            return []

        self._rx_buffer += data
        lines = []

        while b"\n" in self._rx_buffer:
            raw, self._rx_buffer = self._rx_buffer.split(b"\n", 1)
            line = raw.decode("utf-8", "ignore").strip()
            if line:
                print("[printer] <<", line)
                lines.append(line)
                self._parse_line(line)

        return lines

    def _parse_line(self, line):
        self.state.printer_connected = True

        if "T:" in line and "B:" in line:
            self._parse_temp_line(line)
            return

        if line == "ok":
            self.state.last_message = "last command acknowledged"
            if self.job_manager:
                self.job_manager.notify_ok()
            return

        if line.lower().startswith("error"):
            self.state.last_error = line
            self.state.printer_state = "error"
            if self.job_manager:
                self.job_manager.notify_error(line)
            return

    def _parse_temp_line(self, line):
        try:
            t_index = line.find("T:")
            b_index = line.find("B:")
            if t_index >= 0:
                t_part = line[t_index + 2 :].split()[0]
                if "/" in t_part:
                    cur, target = t_part.split("/", 1)
                    self.state.nozzle_temp = float(cur)
                    self.state.nozzle_target = float(target)
            if b_index >= 0:
                b_part = line[b_index + 2 :].split()[0]
                if "/" in b_part:
                    cur, target = b_part.split("/", 1)
                    self.state.bed_temp = float(cur)
                    self.state.bed_target = float(target)
        except Exception as exc:
            self.state.last_error = "temp parse error: {}".format(exc)

    def request_status(self):
        self.send_command("M105")

    def home_all(self):
        self.send_command("G28")
        self.state.last_message = "homing"

    def set_hotend_temp(self, temp_c):
        self.send_command("M104 S{}".format(int(temp_c)))
        self.state.last_message = "setting hotend"

    def set_bed_temp(self, temp_c):
        self.send_command("M140 S{}".format(int(temp_c)))
        self.state.last_message = "setting bed"

    def cooldown(self):
        self.send_command("M104 S0")
        self.send_command("M140 S0")
        self.state.last_message = "cooldown requested"

    def fan_on(self, speed=255):
        self.send_command("M106 S{}".format(int(speed)))
        self.state.last_message = "fan on"

    def fan_off(self):
        self.send_command("M107")
        self.state.last_message = "fan off"