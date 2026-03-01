# servers-helper

> A Telegram bot that acts as an AI-powered DevOps assistant for your personal server infrastructure.
> Ask questions in plain language — the agent SSHes into your servers, checks Docker containers, reads logs, and takes actions.

```
You: "what's going on with the germany server?"
Bot: All good. Uptime 14 days, RAM 1.8/4 GB, disk 38/80 GB (47%).

You: "show me running containers"
Bot: • nginx          — Up 14 days
     • outline-vpn   — Up 14 days
     • 3proxy         — Up 3 hours

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
      docker, system      docker, system    docker, system
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

**On remote servers (`vdsina-netherlands`, `aeza-germany`):**
- SSH daemon running
- Docker installed
- Your user in the `docker` group (no sudo for docker commands)

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/sav116/servers-helper.git
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

> `OPENROUTER_MODEL` in `.env` is no longer used — model is set in `bot/config.yaml`.

### 3. Configure servers and LLM

Edit `bot/config.yaml`:

```yaml
llm:
  model: anthropic/claude-3.5-haiku  # change model here
  temperature: 0.2

servers:
  aeza-germany:
    ssh_host: aeza-germany            # must match Host in ~/.ssh/config
    description: "VPS in Germany (aeza hosting)"
    tags: [vpn, proxy, germany]
```

SSH host aliases in `config.yaml` must match entries in `~/.ssh/config` on `servers-helper`.

### 4. Configure SSH on `servers-helper`

Make sure `~/.ssh/config` has entries for all your servers:

```
Host vdsina-netherlands
    HostName 1.2.3.4
    User your-user
    IdentityFile ~/.ssh/id_ed25519

Host aeza-germany
    HostName 5.6.7.8
    User your-user
    IdentityFile ~/.ssh/id_ed25519
```

Test that SSH works before starting the bot:

```bash
ssh vdsina-netherlands "uptime"
ssh aeza-germany "docker ps"
```

### 5. Remote servers — add user to docker group

Run this on each remote server once:

```bash
sudo usermod -aG docker $USER
# reconnect SSH for the change to take effect
```

### 6. Self-monitoring setup (servers-helper)

The bot can also monitor the machine it runs on. It SSHes back to the host via `host.docker.internal` (already wired in `docker-compose.yml`).

Add this to `~/.ssh/config` on `servers-helper`:

```
Host host.docker.internal
    HostName host.docker.internal
    User your-user
    IdentityFile ~/.ssh/id_ed25519
```

Make sure your own public key is in `~/.ssh/authorized_keys`:

```bash
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
```

### 7. Run

```bash
docker compose up -d --build
docker compose logs -f bot   # watch logs
```

---

## Adding a new server

No code changes needed — only `config.yaml` and SSH config.

**Step 1.** Add to `~/.ssh/config` on `servers-helper`:
```
Host my-new-server
    HostName 9.10.11.12
    User your-user
    IdentityFile ~/.ssh/id_ed25519
```

**Step 2.** Add to `bot/config.yaml`:
```yaml
servers:
  my-new-server:
    ssh_host: my-new-server
    description: "My new VPS in Finland"
    tags: [storage, backup]
```

**Step 3.** Restart the bot (no rebuild needed):
```bash
docker compose restart bot
```

The new server is now visible to the agent and all tools work with it automatically.

---

## Changing the LLM model

Edit `bot/config.yaml`:

```yaml
llm:
  model: anthropic/claude-3.7-sonnet   # upgrade for complex reasoning
  # model: google/gemini-2.0-flash     # cheapest option
  # model: openai/gpt-4o-mini          # OpenAI alternative
```

Then restart:
```bash
docker compose restart bot
```

Browse all available models at [openrouter.ai/models](https://openrouter.ai/models).

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
├── .env                    # secrets (not committed)
├── .env.example
└── bot/
    ├── Dockerfile
    ├── requirements.txt
    ├── config.yaml         # servers + LLM settings (edit freely)
    ├── config.py           # loads config.yaml + .env
    ├── main.py             # aiogram bot
    ├── agent.py            # LangGraph ReAct agent
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
|-----------|-----------|
| Telegram bot | [aiogram 3](https://docs.aiogram.dev) |
| AI agent | [LangGraph](https://langchain-ai.github.io/langgraph/) ReAct |
| LLM | [OpenRouter](https://openrouter.ai) (any model) |
| Server access | SSH via system `ssh` client |
| Config | YAML + Pydantic |
| Runtime | Docker Compose |

## License

MIT
