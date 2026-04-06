# config.py

DEVICE_NAME = "ender3-ctrl"

# WIFI MODE:
#   "STA"      -> connect to existing Wi-Fi
#   "AP"       -> create hotspot only
#   "FALLBACK" -> try STA, then AP if STA fails
WIFI_MODE = "FALLBACK"

# Station mode credentials
STA_SSID = "YOUR_WIFI_NAME"
STA_PASSWORD = "YOUR_WIFI_PASSWORD"
STA_CONNECT_TIMEOUT_S = 15

# Access point settings
AP_SSID = "Ender3-Control"
AP_PASSWORD = "print1234"
AP_AUTHMODE = 3  # WPA2 on ESP32 MicroPython
AP_MAX_CLIENTS = 4
AP_IFCONFIG = ("192.168.4.1", "255.255.255.0", "192.168.4.1", "8.8.8.8")

# Printer UART
PRINTER_UART_ID = 2
PRINTER_BAUDRATE = 115200
PRINTER_TX_PIN = 17
PRINTER_RX_PIN = 16
UART_TIMEOUT_MS = 50

# Web server
HTTP_PORT = 80
STATUS_POLL_INTERVAL_MS = 2000

# File storage
WWW_ROOT = "/www"
UPLOAD_ROOT = "/uploads"

# Safety / behavior
ENABLE_EMERGENCY_STOP = False
MAX_UPLOAD_SIZE = 8 * 1024 * 1024