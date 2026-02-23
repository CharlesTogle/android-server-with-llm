# Android Server with LLM

Lightweight HTTP proxy server for running local LLMs on Android (Termux).

## Requirements

- Termux with Python 3
- [llama.cpp](https://github.com/ggerganov/llama.cpp) compiled for Android
- A GGUF model (e.g., TinyLlama)

## Setup

1. Start llama-server:
```bash
./build/bin/llama-server \
  -m ~/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  --ctx-size 2048
```

2. Start the proxy:
```bash
python llm_proxy.py
```

Or add alias to `~/.bashrc`:
```bash
alias llmproxy="python ~/llm_proxy.py"
```

## Usage

Send prompts via HTTP POST:
```bash
curl -X POST http://<DEVICE_IP>:8081 \
  -H "Content-Type: application/json" \
  -d {prompt: hello}
```

## Configuration

Edit the top of `llm_proxy.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLAMA_URL` | `http://127.0.0.1:8080/completion` | llama-server endpoint |
| `PORT` | `8081` | Proxy listen port |
| `N_PREDICT` | `256` | Max tokens to generate |
| `SYSTEM_PROMPT` | Phone assistant | System prompt for the LLM |

## Logs

The server outputs verbose logs:
```
[2026-02-23 12:34:56] >>> REQUEST from 192.168.1.100:54321
[2026-02-23 12:34:56]     User prompt: hello
[2026-02-23 12:34:58] <<< RESPONSE (2.15s)
[2026-02-23 12:34:58]     Tokens: 84
```

## License

MIT
