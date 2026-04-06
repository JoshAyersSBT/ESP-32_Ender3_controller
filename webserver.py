# webserver.py

import socket
import ujson
import os
import config


def ensure_dirs():
    for path in (config.WWW_ROOT, config.UPLOAD_ROOT):
        try:
            os.mkdir(path)
        except OSError:
            pass


class WebServer:
    def __init__(self, state, printer):
        self.state = state
        self.printer = printer
        self.sock = None

    def start(self):
        ensure_dirs()
        addr = socket.getaddrinfo("0.0.0.0", config.HTTP_PORT)[0][-1]
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(addr)
        self.sock.listen(2)
        print("[web] listening on port", config.HTTP_PORT)

    def serve_once(self):
        client, _ = self.sock.accept()
        try:
            request = client.recv(2048)
            if not request:
                return
            request_line = request.split(b"\r\n", 1)[0].decode("utf-8", "ignore")
            method, path, _ = request_line.split(" ", 2)
            print("[web]", method, path)

            if path == "/api/status":
                self._json(client, self.state.as_dict())
                return

            if path == "/api/home":
                self.printer.home_all()
                self._json(client, {"ok": True})
                return

            if path.startswith("/api/hotend?"):
                temp = self._query_value(path, "s")
                self.printer.set_hotend_temp(temp)
                self._json(client, {"ok": True, "temp": temp})
                return

            if path.startswith("/api/bed?"):
                temp = self._query_value(path, "s")
                self.printer.set_bed_temp(temp)
                self._json(client, {"ok": True, "temp": temp})
                return

            if path == "/api/cooldown":
                self.printer.cooldown()
                self._json(client, {"ok": True})
                return

            if path == "/api/fan_on":
                self.printer.fan_on()
                self._json(client, {"ok": True})
                return

            if path == "/api/fan_off":
                self.printer.fan_off()
                self._json(client, {"ok": True})
                return

            if path == "/" or path == "/index.html":
                self._file(client, config.WWW_ROOT + "/index.html", "text/html")
                return

            if path == "/app.js":
                self._file(client, config.WWW_ROOT + "/app.js", "application/javascript")
                return

            if path == "/style.css":
                self._file(client, config.WWW_ROOT + "/style.css", "text/css")
                return

            self._not_found(client)
        except Exception as exc:
            try:
                self._json(client, {"ok": False, "error": str(exc)}, status="500 Internal Server Error")
            except Exception:
                pass
        finally:
            client.close()

    def _query_value(self, path, key):
        query = path.split("?", 1)[1]
        for part in query.split("&"):
            if "=" in part:
                k, v = part.split("=", 1)
                if k == key:
                    return int(v)
        raise ValueError("missing query arg: {}".format(key))

    def _send_headers(self, client, content_type, status="200 OK"):
        client.send("HTTP/1.1 {}\r\n".format(status))
        client.send("Content-Type: {}\r\n".format(content_type))
        client.send("Connection: close\r\n\r\n")

    def _json(self, client, obj, status="200 OK"):
        self._send_headers(client, "application/json", status=status)
        client.send(ujson.dumps(obj))

    def _file(self, client, path, content_type):
        try:
            with open(path, "rb") as f:
                self._send_headers(client, content_type)
                while True:
                    chunk = f.read(512)
                    if not chunk:
                        break
                    client.send(chunk)
        except OSError:
            self._not_found(client)

    def _not_found(self, client):
        self._send_headers(client, "text/plain", status="404 Not Found")
        client.send("404 Not Found")