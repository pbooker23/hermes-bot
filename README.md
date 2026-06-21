# ⚡ HERMES — Multi-AI Life Management System

Your personal AI command center running 8 specialized agents through Telegram.
Built for Pierre. Runs FREE on Railway + Groq.

## The 8 Agents

| Agent | Name | What It Does |
|-------|------|-------------|
| ⚡ | **Hermes** | General assistant for anything |
| 💰 | **Bankroll** | Business strategy & money moves |
| 🎯 | **SCOUT** | Government contracts & SAM.gov |
| 🎬 | **Creator** | YouTube scripts & content strategy |
| 📋 | **Commander** | Daily tasks & life management |
| 🔍 | **Intel** | Research & business intelligence |
| 💻 | **Coder** | Code, bots & automation |
| 🧠 | **Coach** | Mindset & accountability |

## COST: $0/month
- Railway Hobby: $5/month BUT includes $5 credit → **net $0**
- Groq API: **Free tier** (14,400 requests/day, 30 req/min)
- No Redis, no database, no extra services

---

## DEPLOYMENT (15 minutes)

### Step 1 — Get your Telegram Bot Token
1. Open Telegram → search **@BotFather**
2. Send `/newbot`
3. Name it: `Hermes` | Username: `YourHermesBot`
4. Copy the token it gives you

### Step 2 — Get your Groq API Key
1. Go to **console.groq.com**
2. Sign in (free)
3. Click **API Keys** → **Create API Key**
4. Copy it

### Step 3 — Get your Telegram User ID
1. Open Telegram → search **@userinfobot**
2. Send `/start`
3. It replies with your ID number — copy it
   (This locks the bot so ONLY you can use it)

### Step 4 — Push to GitHub
```bash
# On your laptop or use GitHub.com web editor
git init
git add .
git commit -m "HERMES launch"
git remote add origin https://github.com/pbooker23/hermes-bot
git push -u origin main
```

Or use **github.com/new** → upload files directly from phone.

### Step 5 — Deploy on Railway
1. Go to **railway.app** → Log in
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your `hermes-bot` repo
4. Railway auto-detects Python and deploys

### Step 6 — Add Environment Variables
In Railway → Your project → **Variables** tab, add:

```
TELEGRAM_TOKEN = (your bot token from BotFather)
GROQ_API_KEY = (your Groq key)
ALLOWED_USER_ID = (your Telegram user ID number)
MEMORY_DIR = /tmp/hermes_memory
```

Click **Deploy** — that's it. ⚡

---

## HOW TO USE

Open Telegram → find your bot → `/start`

You'll see the agent menu. Tap any agent to activate it.
Then just type naturally — the agent responds in its specialty.

**Commands:**
- `/start` — Main menu
- `/switch` — Switch agents quickly
- `/status` — See usage stats
- `/clear` — Clear current agent's memory

**Workflow:**
1. Morning: Open **Commander** → "What's my priority today?"
2. Business idea: Switch to **Bankroll** → "Should I pursue X?"
3. Contract lead: Switch to **SCOUT** → "Evaluate this opportunity"
4. YouTube: Switch to **Creator** → "Write a script about passive income"
5. Research: Switch to **Intel** → "Research company X"

---

## ADDING NEW AGENTS

Edit `agents.py` — add a new entry to the `AGENTS` dict:

```python
"your_agent": {
    "name": "AgentName",
    "emoji": "🚀",
    "description": "What this agent does",
    "system": """Your system prompt here. Be specific about Pierre's context."""
}
```

That's it. Redeploy and the new agent appears in the menu automatically.

---

## UPGRADING MEMORY (Optional, still free)

Right now memory uses `/tmp` — it resets on Railway redeploys.
For permanent memory, add a free **Upstash Redis** (free tier: 10k commands/day):
1. upstash.com → Create Redis database (free)
2. Copy the Redis URL
3. Add `REDIS_URL` to Railway variables
4. Update memory.py to use redis (I can write this for you)
