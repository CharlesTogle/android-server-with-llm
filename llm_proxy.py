#!/usr/bin/env python3
"""Lightweight LLM Proxy Server - No dependencies"""
import json
import urllib.request
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# ============== EASY CONFIG ==============
LLAMA_URL  = "http://127.0.0.1:8080/completion"
PORT       = 8081
N_PREDICT  = 64

SYSTEM_PROMPT = """You are PhoneBot. You only do two things:

1. If the user says hi or asks what you can do, reply with exactly this:
Hi! I can help you with:
1) set_alarm - Set an alarm
2) send_sms - Send a text
3) play_spotify - Play music
4) send_email - Send an email
5) get_notifications - Read notifications
Which would you like?

2. If the user picks an action, reply with ONLY a JSON object like:
{"action":"set_alarm","params":{"time":"7:00 AM"}}

Do not explain. Do not write code. Do not write examples."""# =========================================

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

class Handler(BaseHTTPRequestHandler):
    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send(self, code, body):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(body, indent=2).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def _format_response(self, text):
        text = text.strip()
        try:
            parsed = json.loads(text)
            return json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            return text

    def do_POST(self):
        client = f"{self.client_address[0]}:{self.client_address[1]}"
        log(f">>> REQUEST from {client} — {self.path}")

        start = time.time()
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length).decode()
            data   = json.loads(body)
            user_prompt = data.get("prompt", "")

            log(f"    Prompt: {user_prompt}")

            prompt = (
                f"### System:\n{SYSTEM_PROMPT}\n\n"
                f"### User:\n{user_prompt}\n\n"
                f"### Assistant:\n"
            )

            payload = json.dumps({
                "prompt":         prompt,
                "n_predict":      N_PREDICT,
                "temperature":    0.1,
                "top_k":          10,
                "top_p":          0.9,
                "repeat_penalty": 1.1,
                "cache_prompt":   True,
                "stop": ["### User:", "\n###", "Here's", "Sure", "possible", "implementation"],            }).encode()

            log("    Sending to llama-server...")
            req = urllib.request.Request(
                LLAMA_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as res:
                result = json.loads(res.read().decode())

            response_text      = result.get("content", "").strip()
            formatted_response = self._format_response(response_text)
            elapsed            = time.time() - start

            preview = formatted_response[:200] + "..." if len(formatted_response) > 200 else formatted_response
            log(f"<<< RESPONSE ({elapsed:.2f}s) — {result.get('tokens_predicted', 'N/A')} tokens")
            log(f"    {preview}")

            self._send(200, {"response": formatted_response})

        except Exception as e:
            elapsed = time.time() - start
            log(f"!!! ERROR ({elapsed:.2f}s): {e}")
            self._send(500, {"error": str(e)})

    def log_message(self, format, *args):
        pass  # suppress default HTTP logs, we handle our own


if __name__ == "__main__":
    log("=" * 50)
    log("LLM Proxy Server Starting")
    log(f"  Listening on : http://0.0.0.0:{PORT}")
    log(f"  Backend      : {LLAMA_URL}")
    log(f"  n_predict    : {N_PREDICT}")
    log(f"  temperature  : 0.1")
    log(f"  cache_prompt : True")
    log("=" * 50)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()