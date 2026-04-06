# storage.py

import os
import config


def ensure_upload_root():
    try:
        os.mkdir(config.UPLOAD_ROOT)
    except OSError:
        pass


def list_files():
    ensure_upload_root()
    items = []
    try:
        for name in os.listdir(config.UPLOAD_ROOT):
            path = config.UPLOAD_ROOT + "/" + name
            try:
                st = os.stat(path)
                size = st[6] if len(st) > 6 else 0
            except Exception:
                size = 0
            items.append({
                "name": name,
                "size": size,
                "path": path,
            })
    except OSError:
        pass

    items.sort(key=lambda x: x["name"].lower())
    return items


def file_exists(filename):
    try:
        os.stat(config.UPLOAD_ROOT + "/" + filename)
        return True
    except OSError:
        return False


def delete_file(filename):
    os.remove(config.UPLOAD_ROOT + "/" + filename)


def safe_filename(name):
    out = []
    for ch in name:
        if ch.isalnum() or ch in ("-", "_", "."):
            out.append(ch)
        else:
            out.append("_")
    cleaned = "".join(out).strip("._")
    if not cleaned:
        cleaned = "upload.gcode"
    return cleaned