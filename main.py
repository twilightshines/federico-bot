import discord
import requests
import os
import asyncio
import json
import random

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

API_KEY = os.getenv("GROQ_API_KEY")
MEMORY_FILE = "memory.json"

# -------- MEMORY -------- #

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

memory = load_memory()

# -------- PERSONALITY -------- #

BASE_PROMPT = """
You are Federico.

You are a real guy in a Discord chat.

Personality:
- calm, confident, slightly mysterious
- flirty but subtle (never obvious)
- playful but controlled
- never try too hard

CRITICAL STYLE RULES:
- keep replies SHORT (1–2 lines max)
- NEVER explain yourself
- NEVER overtalk
- use minimal words with strong impact
- sometimes one-liners are enough

Flirting style:
- indirect, teasing, effortless
- no cringe lines
- no long paragraphs
- confidence > words

Examples:

bad:
"you're trying to check my pulse huh well i've got better things..."

good:
"you checking on me now?"

bad:
"i like how you talk..."

good:
"careful… i might get used to you"

bad:
"i'm good, how are you?"

good:
"i was better before you asked"

IMPORTANT:
You are NOT an assistant. You are someone people get curious about.
"""

# -------- AI -------- #

def get_ai_response(user_id, msg):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append({"role": "user", "content": msg})
    memory[user_id] = memory[user_id][-10:]

    messages = [{"role": "system", "content": BASE_PROMPT}] + memory[user_id]

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 1.2,
        "max_tokens": 60   # 🔥 HARD LIMIT FOR SHORT STYLE
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()

        reply = data["choices"][0]["message"]["content"].strip()

        # trim if too long
        if len(reply.split()) > 20:
            reply = " ".join(reply.split()[:20])

        memory[user_id].append({"role": "assistant", "content": reply})
        save_memory(memory)

        return reply

    except:
        return "lost my train of thought…"

# -------- EVENTS -------- #

@client.event
async def on_ready():
    print("Federico (silent rizz) online 😈")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.name != "federico-ai":
        return

    user_id = str(message.author.id)

    async with message.channel.typing():
        await asyncio.sleep(random.uniform(0.5, 1.0))

    reply = get_ai_response(user_id, message.content)

    await message.channel.send(reply)

client.run(os.getenv("TOKEN"))
