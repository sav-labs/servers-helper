# servers-helper

> A Telegram bot that acts as an AI-powered DevOps assistant for your personal server infrastructure.
> Ask questions in plain language — the agent SSHes into your servers, checks Docker containers, reads logs, and takes actions.

```
You: "what's going on with the germany server?"
Bot: 🖥 aeza-germany
     ├ CPU: 1.5%  load: 0.00 / 0.00 / 0.00
     ├ RAM: 57M / 992M  free: 907M
     ├ Disk: 1.4G / 50G  free: 47.1G
     └ Uptime: 12 days

You: "show me running containers"
Bot: 🟢 nginx        — Up 14 days
     🟢 outline-vpn  — Up 14 days
     🟢 3proxy       — Up 3 hours

You: "restart outline-vpn"
Bot: About to restart outline-vpn on aeza-germany. Confirm?

You: "yes"
Bot: ✓ Container restarted successfully.
```

## How it works

```
Telegram
   ↕
aiogram 3  ──  LangGraph ReAct agent  ──  OpenRouter LLM
                        ↓
               SSH tools (subprocess)
               /          |          \
    vdsina-netherlands  aeza-germany  servers-helper
      docker, system    docker, system  docker, system
```

The agent has **14 built-in tools** across two categories:

| Category | Tools |
|----------|-------|
| **Docker** | list containers, logs, stats, inspect, restart, stop, start, exec |
| **System** | resources (CPU/RAM/disk), top processes, service status, network info, journal logs, run command |

Every tool works on any configured server — just name it in your message.

---

## Requirements

**On `servers-helper` (where the bot runs):**
- Docker + Docker Compose
- SSH access to remote servers configured in `~/.ssh/config`

**On remote servers:**
- SSH daemon running
- Docker installed
- Your user in the `docker` group (no sudo for docker commands)

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/sav-labs/servers-helper.git
cd servers-helper
```

### 2. Configure secrets

```bash
cp .env.example .env
nano .env
```

```env
TELEGRAM_TOKEN=your_bot_token        # from @BotFather
OPENROUTER_API_KEY=your_key          # from openrouter.ai
ALLOWED_USER_IDS=123456789           # your Telegram ID (from @userinfobot)
```

### 3. Configure servers and LLM

Edit `bot/config.yaml`:

```yaml
llm:
  model: google/gemini-2.0-flash-001  # see "Choosing a model" below
  temperature: 0.2

servers:
  aeza-germany:
    ssh_host: aeza-germany            # must match Host in ~/.ssh/config
    description: "VPS in Germany (aeza hosting)"
    tags: [vpn, proxy, germany]
```

### 4. Configure SSH on `servers-helper`

SSH file permissions must be strict — SSH refuses to work otherwise:

```bash
chmod 600 ~/.ssh/config
chmod 600 ~/.ssh/id_ed25519
```

`~/.ssh/config` must have entries for all servers. A working example:

```
Host *
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
    CheckHostIP no

Host vdsina-netherlands
    HostName 1.2.3.4
    Port 22
    User root

Host aeza-germany
    HostName 5.6.7.8
    Port 22
    User root

Host host.docker.internal
    HostName host.docker.internal
    User your-local-user            # the user that runs docker compose
```

Test SSH before starting the bot:

```bash
ssh vdsina-netherlands "uptime"
ssh aeza-germany "docker ps"
```

### 5. Remote servers — add user to docker group

Run on each remote server once (skip if connecting as root):

```bash
sudo usermod -aG docker $USER
# reconnect SSH for the change to take effect
```

### 6. Self-monitoring setup (servers-helper)

The bot SSHes back to its own host via `host.docker.internal` (wired in `docker-compose.yml` via `extra_hosts`).

Make sure your public key is in `authorized_keys`:

```bash
grep -c "$(cat ~/.ssh/id_ed25519.pub)" ~/.ssh/authorized_keys \
  || cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
```

### 7. Run

```bash
docker compose up -d --build
docker compose logs -f bot
```

The entrypoint automatically copies `~/.ssh` into the container and fixes permissions — no manual steps needed.

---

## Adding a new server

No code changes needed — only SSH config and `config.yaml`.

**Step 1.** Add to `~/.ssh/config` on `servers-helper`:
```
Host my-new-server
    HostName 9.10.11.12
    User root
```

**Step 2.** Add to `bot/config.yaml`:
```yaml
servers:
  my-new-server:
    ssh_host: my-new-server
    description: "My new VPS in Finland (Hetzner)"
    tags: [storage, backup]
```

**Step 3.** Restart (no rebuild needed):
```bash
docker compose restart bot
```

The new server is immediately visible to the agent — all tools work with it automatically.

---

## Choosing a model

Edit `bot/config.yaml` → restart with `docker compose restart bot`. No rebuild needed.

```yaml
llm:
  model: google/gemini-2.0-flash-001   # recommended: fast, cheap, no geo-restrictions
  # model: openai/gpt-4o-mini          # good alternative
  # model: deepseek/deepseek-chat-v3-0324
  # model: meta-llama/llama-3.3-70b-instruct
```

> **Note for Russia/CIS:** Anthropic models (`claude-*`) are geo-blocked via OpenRouter's
> Amazon Bedrock provider. Use Google, OpenAI, DeepSeek, or Meta models instead.

Browse all models at [openrouter.ai/models](https://openrouter.ai/models).

---

## Example conversations

```
"what servers do you know about?"
"check resources on all servers"
"show containers on aeza-germany"
"logs for nginx, last 100 lines"
"is the VPN running on vdsina?"
"restart 3proxy on netherlands"
"what's eating CPU on germany?"
"check disk space everywhere"
"run: df -h on servers-helper"
```

---

## Project structure

```
servers-helper/
├── docker-compose.yml
├── .env                      # secrets (not committed)
├── .env.example
└── bot/
    ├── Dockerfile
    ├── entrypoint.sh          # fixes SSH permissions on startup
    ├── requirements.txt
    ├── config.yaml            # servers + LLM settings (edit freely)
    ├── config.py              # loads config.yaml + .env
    ├── main.py                # aiogram bot
    ├── agent.py               # LangGraph ReAct agent
    ├── prompts/
    │   └── system_prompt.py   # auto-generated from config.yaml
    └── tools/
        ├── base.py            # SSH exec helper
        ├── docker_tools.py    # Docker management (8 tools)
        └── system_tools.py    # System commands (6 tools)
```

---

## Tech stack

| Component | Technology |
|-----------|------------|
| Telegram bot | [aiogram 3](https://docs.aiogram.dev) |
| AI agent | [LangGraph](https://langchain-ai.github.io/langgraph/) ReAct |
| LLM | [OpenRouter](https://openrouter.ai) (any model) |
| Server access | SSH via system `ssh` client |
| Config | YAML + Pydantic |
| Runtime | Docker Compose |

## License

MIT
