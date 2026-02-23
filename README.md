# TinyLlama 1.1B Setup Guide
### Realme 5i · Termux · llama.cpp

Complete guide to getting TinyLlama 1.1B running as an HTTP server on Android via Termux, accessible from your laptop.

---

## Prerequisites

- Realme 5i (or any Android phone with 3GB+ free RAM)
- **Termux installed from F-Droid** — not the Play Store version, it's outdated and breaks package installs
- WiFi connection for downloads
- A laptop on the same network

---

## Step 1 — SSH Access from Your Laptop

Working over SSH from your laptop is highly recommended over typing directly on the phone screen.

### On the phone (Termux)

```bash
pkg install openssh
sshd
passwd
# set a password when prompted
```

Find your phone's IP:
```bash
ifconfig
# or
ip route get 1.1.1.1
```

If all fail, go to **Settings → WiFi → tap your network → IP address**.

### On your laptop

```bash
ssh -p 8022 u0_a239@192.168.1.151
```

Replace `u0_a239` with your Termux username (`whoami` to check) and `192.168.1.151` with your phone's IP.

**Optional — add to `~/.ssh/config` on your laptop:**

```
Host phone
    HostName 192.168.1.151
    Port 8022
    User u0_a239
```

Then just type `ssh phone` to connect.

---

## Step 2 — Install Dependencies

```bash
pkg update && pkg upgrade -y
pkg install git cmake clang ninja python wget -y
```

---

## Step 3 — Build llama.cpp

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j4
```

> Build takes **10–20 minutes** on the Snapdragon 665. If it crashes, retry with `-j2`.

Verify:
```bash
ls build/bin/llama-server
```

---

## Step 4 — Download the Model

```bash
mkdir ~/models && cd ~/models

wget -O tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
  "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf?download=true"
```

Verify (~669MB):
```bash
ls -lh ~/models/
```

---

## Step 5 — Start the LLM Server

```bash
cd ~/llama.cpp

./build/bin/llama-server \
  -m ~/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  --ctx-size 2048 \
  -n 256
```

Health check:
```bash
curl http://localhost:8080/health
# {"status":"ok"}
```

---

## Step 6 — Start the Proxy Server

The proxy adds system prompt handling and formats responses as clean JSON.

```bash
python llm_proxy.py
```

Configure by editing the top of `llm_proxy.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLAMA_URL` | `http://127.0.0.1:8080/completion` | llama-server endpoint |
| `PORT` | `8081` | Proxy listen port |
| `N_PREDICT` | `256` | Max tokens to generate |
| `SYSTEM_PROMPT` | Phone assistant | System prompt for the LLM |

---

## Step 7 — Chat via Web Interface

Open `index.html` in your browser for a clean chat interface with:
- Pretty-printed JSON responses
- Loading indicator while waiting
- Configurable server URL

Set the server URL to `http://<PHONE_IP>:8081` (e.g., `http://192.168.1.151:8081`).

---

## Testing with tmux

For quick testing, use tmux to keep servers running when you disconnect:

```bash
pkg install tmux

# Start llama-server in background
tmux new -s llama
./build/bin/llama-server -m ~/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
  --host 0.0.0.0 --port 8080 --ctx-size 2048 -n 256
# Detach: Ctrl+B then D

# Start proxy in another session
tmux new -s proxy
python llm_proxy.py
# Detach: Ctrl+B then D

# Reattach later
tmux attach -t llama
tmux attach -t proxy
```

---

## Optional: Vulkan GPU Acceleration

The Adreno 610 supports Vulkan (30–50% faster):

```bash
pkg install vulkan-tools
cd ~/llama.cpp
cmake -B build -DGGML_VULKAN=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j4
```

---

## Auto-start on Boot

Install **Termux:Boot** from F-Droid:

```bash
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
sshd
cd /data/data/com.termux/files/home/llama.cpp
tmux new-session -d -s llama \
  "./build/bin/llama-server \
    -m /data/data/com.termux/files/home/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
    --host 0.0.0.0 --port 8080 --ctx-size 2048 -n 256"
EOF
chmod +x ~/.termux/boot/start.sh
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Model file too small | Download failed. Delete and retry. Should be ~669MB. |
| Build crashes / OOM | Use `-j2` instead of `-j4` |
| Termux dies when screen off | Run `termux-wake-lock`, disable battery optimization for Termux |
| SSH connection refused | Run `sshd` in Termux. Port is `8022` not `22`. |
| CORS error in browser | Restart proxy server — it includes CORS headers |

---

## License

MIT
