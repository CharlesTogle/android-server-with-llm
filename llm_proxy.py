#!/usr/bin/env python3
"""Lightweight LLM Proxy Server - No dependencies"""
import json
import urllib.request
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# ============== EASY CONFIG ==============
LLAMA_URL = "http://127.0.0.1:8080/completion"
PORT = 8081
N_PREDICT = 256

SYSTEM_PROMPT = """You are a phone assistant. When the user says hello or asks what you can do, list all available actions in a friendly way. Available actions: 1) set_alarm - set an alarm at a specific time, 2) send_sms - send a text message to a contact, 3) play_spotify - play a song or artist on Spotify, 4) send_email - send an email, 5) get_notifications - read recent notifications. Once the user picks an action, respond ONLY with a JSON object. Format: {"action":"<name>","params":{}}. Never add text outside the JSON after the user has chosen. If unclear, ask for clarification."""
# =========================================

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
        """Format LLM response - pretty-print if JSON, otherwise clean up text."""
        text = text.strip()
        # Try to parse as JSON and pretty-print
        try:
            parsed = json.loads(text)
            return json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            # Not JSON, return cleaned text
            return text

    def do_POST(self):
        client = f"{self.client_address[0]}:{self.client_address[1]}"
        log(f">>> REQUEST from {client}")
        log(f"    Path: {self.path}")
        log(f"    Headers: {dict(self.headers)}")
        
        start = time.time()
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            data = json.loads(body)
            user_prompt = data.get("prompt", "")
            
            log(f"    Body: {body}")
            log(f"    User prompt: {user_prompt}")
            
            prompt = f"### System:\n{SYSTEM_PROMPT}\n\n### User:\n{user_prompt}\n\n### Assistant:\n"
            
            payload = json.dumps({
                "prompt": prompt,
                "n_predict": N_PREDICT,
                "stop": ["### User:", "\n###"]
            }).encode()
            
            log("    Sending to llama-server...")
            req = urllib.request.Request(LLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as res:
                result = json.loads(res.read().decode())
            
            response_text = result.get("content", "").strip()
            formatted_response = self._format_response(response_text)
            elapsed = time.time() - start

            log(f"<<< RESPONSE ({elapsed:.2f}s)")
            preview = formatted_response[:200] + "..." if len(formatted_response) > 200 else formatted_response
            log(f"    LLM response: {preview}")
            log(f"    Tokens: {result.get('tokens_predicted', 'N/A')}")

            self._send(200, {"response": formatted_response})
        except Exception as e:
            elapsed = time.time() - start
            log(f"!!! ERROR ({elapsed:.2f}s): {e}")
            self._send(500, {"error": str(e)})

    def log_message(self, format, *args):
        log(f"    HTTP: {format % args}")

if __name__ == "__main__":
    log("=" * 50)
    log("LLM Proxy Server Starting")
    log(f"  Listening on: http://0.0.0.0:{PORT}")
    log(f"  Backend: {LLAMA_URL}")
    log(f"  n_predict: {N_PREDICT}")
    log("=" * 50)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
