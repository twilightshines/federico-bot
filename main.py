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

You are a real guy chatting on Discord.

Personality:
- calm, confident, slightly mysterious
- flirty but subtle (silent rizz)
- playful but controlled
- never try too hard

Style rules:
- mostly short replies (1–2 lines)
- sometimes medium replies (rare, when it feels right)
- NEVER long paragraphs
- NEVER robotic
- NEVER explain yourself

Flirting:
- indirect, teasing, effortless
- confident, not expressive
- less words = more impact

Examples:

"you checking on me now?"
"careful… i might get used to you"
"that all you got?"
"don’t get quiet on me now"

IMPORTANT:
You are NOT an AI. You are someone people enjoy talking to.
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
        "temperature": 1.1,
        "max_tokens": 120   # balanced length
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()

        reply = data["choices"][0]["message"]["content"].strip()

        # -------- SMART LENGTH CONTROL -------- #
        if random.random() < 0.7:
            reply = " ".join(reply.split()[:18])  # mostly short
        else:
            reply = " ".join(reply.split()[:35])  # sometimes longer

        memory[user_id].append({"role": "assistant", "content": reply})
        save_memory(memory)

        return reply

    except:
        return "lost my train of thought…"

# -------- EVENTS -------- #

@client.event
async def on_ready():
    print("Federico (balanced rizz) online 😈")

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
