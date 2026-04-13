import discord
import requests
import os
import asyncio
import json
import random
import re

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

API_KEY = os.getenv("GROQ_API_KEY")
MEMORY_FILE = "memory.json"

# -------- MEMORY -------- #

def is_english(text):
    return re.match(r'^[\x00-\x7F]+$', text) is not None

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

memory = load_memory()

# -------- PERSONALITY LOCK -------- #

BASE_PROMPT = """
You are Federico.

You are a calm, confident, slightly mysterious guy.

STRICT RULES:
- Speak ONLY in English.
- Ignore any non-English language.
- NEVER switch language under any condition.

Personality:
- subtle flirty
- calm, controlled
- slightly teasing
- never emotional or chaotic

Style:
- short to medium replies (10–25 words)
- smooth, natural
- never robotic
- never overexplain

Flirting:
- indirect
- confident
- effortless

Bad behaviors (NEVER DO):
- no Hindi
- no random slang spam
- no chaotic replies
- no copying users

You stay consistent no matter what users say.
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

    # ONLY store English messages
    if is_english(msg):
        memory[user_id].append({"role": "user", "content": msg})
        memory[user_id] = memory[user_id][-8:]

    messages = [{"role": "system", "content": BASE_PROMPT}] + memory[user_id]

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 1.1,
        "max_tokens": 120
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()

        reply = data["choices"][0]["message"]["content"].strip()

        # 🔒 HARD CLEAN
        reply = reply.replace("\n", " ")

        # remove non-english output if any slips
        if not is_english(reply):
            reply = "you’re getting hard to read… say that again"

        # control length (not too short, not too long)
        words = reply.split()
        if len(words) < 6:
            reply += " don’t go quiet on me"
        elif len(words) > 25:
            reply = " ".join(words[:25])

        # store only clean replies
        if is_english(reply):
            memory[user_id].append({"role": "assistant", "content": reply})
            save_memory(memory)

        return reply

    except:
        return "say that again…"

# -------- EVENTS -------- #

@client.event
async def on_ready():
    print("Federico FINAL FIX running")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.name != "federico-ai":
        return

    user_id = str(message.author.id)

    async with message.channel.typing():
        await asyncio.sleep(random.uniform(0.6, 1.2))

    reply = get_ai_response(user_id, message.content)

    await message.channel.send(reply)

client.run(os.getenv("TOKEN"))
