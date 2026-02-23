#!/usr/bin/env python3
"""Lightweight LLM Proxy Server - No dependencies"""
import json
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

# ============== EASY CONFIG ==============
LLAMA_URL = "http://127.0.0.1:8080/completion"
PORT = 8081
N_PREDICT = 256

SYSTEM_PROMPT = """You are a phone assistant. When the user says hello or asks what you can do, list all available actions in a friendly way. Available actions: 1) set_alarm - set an alarm at a specific time, 2) send_sms - send a text message to a contact, 3) play_spotify - play a song or artist on Spotify, 4) send_email - send an email, 5) get_notifications - read recent notifications. Once the user picks an action, respond ONLY with a JSON object. Format: {"action":"<name>","params":{}}. Never add text outside the JSON after the user has chosen. If unclear, ask for clarification."""
# =========================================

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            data = json.loads(body)
            user_prompt = data.get("prompt", "")
            
            prompt = f"### System:\n{SYSTEM_PROMPT}\n\n### User:\n{user_prompt}\n\n### Assistant:\n"
            
            payload = json.dumps({
                "prompt": prompt,
                "n_predict": N_PREDICT,
                "stop": ["### User:", "\n###"]
            }).encode()
            
            req = urllib.request.Request(LLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as res:
                result = json.loads(res.read().decode())
            
            self._send(200, {"response": result.get("content", "").strip()})
        except Exception as e:
            self._send(500, {"error": str(e)})

    def log_message(self, *args): pass

if __name__ == "__main__":
    print(f"LLM Proxy running on http://0.0.0.0:{PORT}")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
