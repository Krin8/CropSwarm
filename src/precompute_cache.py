"""Disk-backed HTTP request cache for precompute commands."""

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


class RequestCache:
    def __init__(self, directory, offline=False):
        self.directory = Path(directory)
        self.manifest = self.directory / "manifest.json"
        self.records = json.loads(self.manifest.read_text()) if self.manifest.exists() else {}
        self.offline = offline
        self.session = requests.Session()
        self.last_request = {}

    def fetch(self, name, url, *, params=None, data=None, parse=json.loads, suffix="json",
              attempts=3, timeout=15, interval=0):
        method = "POST" if data is not None else "GET"
        request = {"method": method, "url": url, "params": params, "data": data}
        signature = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
        record = self.records.setdefault(name, {"request": request, "signature": signature, "attempts": []})
        if record["signature"] != signature:
            raise ValueError(f"Request changed for cache key {name}")
        if record.get("status") == "complete":
            return parse((self.directory / record["body"]).read_bytes())
        if self.offline:
            return None
        self.directory.mkdir(parents=True, exist_ok=True)
        for index in range(len(record["attempts"]), attempts):
            if index:
                time.sleep(2 ** (index - 1))
            time.sleep(max(0, interval - (time.monotonic() - self.last_request.get(url, 0))))
            attempt = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "http_status": None}
            try:
                self.last_request[url] = time.monotonic()
                response = self.session.request(method, url, params=params, data=data, timeout=timeout)
                attempt.update(url=response.url, http_status=response.status_code)
                attempt["body"] = f"{name}.{index + 1}.{suffix}"
                (self.directory / attempt["body"]).write_bytes(response.content)
                response.raise_for_status()
                result = parse(response.content)
            except (requests.RequestException, ValueError, OSError, KeyError) as error:
                attempt["error"] = str(error)
                record["attempts"].append(attempt)
                record["status"] = "incomplete"
                write_json(self.manifest, self.records)
            else:
                record["attempts"].append(attempt)
                record.update(status="complete", body=attempt["body"])
                write_json(self.manifest, self.records)
                return result
        return None
