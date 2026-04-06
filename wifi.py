# wifi.py

import time
import network
import config


def _wait_for_sta(sta, timeout_s):
    start = time.time()
    while time.time() - start < timeout_s:
        if sta.isconnected():
            return True
        time.sleep(0.25)
    return False


def start_sta():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        print("[wifi] connecting STA to", config.STA_SSID)
        sta.connect(config.STA_SSID, config.STA_PASSWORD)
    if _wait_for_sta(sta, config.STA_CONNECT_TIMEOUT_S):
        ip = sta.ifconfig()[0]
        print("[wifi] STA connected:", ip)
        return {
            "mode": "STA",
            "ip": ip,
            "wlan": sta,
        }
    print("[wifi] STA failed")
    try:
        sta.disconnect()
    except Exception:
        pass
    return None


def start_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.ifconfig(config.AP_IFCONFIG)
    ap.config(
        essid=config.AP_SSID,
        password=config.AP_PASSWORD,
        authmode=config.AP_AUTHMODE,
        max_clients=config.AP_MAX_CLIENTS,
    )
    ip = ap.ifconfig()[0]
    print("[wifi] AP active:", config.AP_SSID, ip)
    return {
        "mode": "AP",
        "ip": ip,
        "wlan": ap,
    }


def start_wifi():
    mode = config.WIFI_MODE.upper()

    if mode == "STA":
        result = start_sta()
        if result:
            return result
        raise RuntimeError("STA mode requested but connection failed")

    if mode == "AP":
        return start_ap()

    if mode == "FALLBACK":
        result = start_sta()
        if result:
            return result
        return start_ap()

    raise ValueError("Invalid WIFI_MODE: {}".format(config.WIFI_MODE))