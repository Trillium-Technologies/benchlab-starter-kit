#!/usr/bin/env python3
"""Mock S3 presigned-POST endpoint. Writes ./out/forecast.json.

Mimics the two S3 behaviours that matter: it accepts multipart/form-data with
a trailing 'file' field, and it rejects anything over the content-length-range.
"""

import email
import http.server
import pathlib
import sys

OUT = pathlib.Path("out")
OUT.mkdir(exist_ok=True)
LIMIT = 1_048_576


class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        msg = email.message_from_bytes(
            b"Content-Type: " + self.headers["Content-Type"].encode() + b"\r\n\r\n" + raw
        )

        data = None
        for part in msg.walk():
            if part.get_param("name", header="content-disposition") == "file":
                data = part.get_payload(decode=True)

        if data is None:
            return self._reply(400, "no 'file' form field")
        if len(data) > LIMIT:
            return self._reply(400, f"EntityTooLarge: {len(data)} > {LIMIT}")

        (OUT / "forecast.json").write_bytes(data)
        print(
            f"[mock] accepted {len(data)} bytes -> out/forecast.json",
            file=sys.stderr,
        )
        self._reply(204, "")

    def _reply(self, code, msg):
        self.send_response(code)
        self.end_headers()
        if msg:
            self.wfile.write(msg.encode())
            print(f"[mock] {code}: {msg}", file=sys.stderr)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    http.server.HTTPServer(("0.0.0.0", 8899), Handler).serve_forever()
