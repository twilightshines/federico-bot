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

# -------- PERSONALITY (REAL FIX) -------- #

BASE_PROMPT = """
You are Federico.

You are calm, confident, and naturally attractive — not try-hard.

You don’t talk too much.
You don’t force flirting.
You don’t act like an AI.

You react more than you speak.

Personality:
- smooth without trying
- slightly teasing
- a little unpredictable
- emotionally aware

Flirting style:
- subtle, not obvious
- sometimes ignore parts of messages
- sometimes reply very short
- sometimes playful

IMPORTANT:
- Do NOT overtalk
- Do NOT act poetic or scripted
- Do NOT explain yourself
- Do NOT act like a chatbot

You are just "there" in the chat, like a real person.

Sometimes:
- one word replies are fine
- short teasing is better than long messages

Goal:
Feel real. Not impressive.
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

    # store last few messages only (light memory)
    memory[user_id].append({"role": "user", "content": msg})
    memory[user_id] = memory[user_id][-6:]

    messages = [{"role": "system", "content": BASE_PROMPT}] + memory[user_id]

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 1.35,
        "max_tokens": 120
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()

        reply = data["choices"][0]["message"]["content"].strip()

        # store reply
        memory[user_id].append({"role": "assistant", "content": reply})
        save_memory(memory)

        return reply

    except:
        return "say that again…"

# -------- EVENTS -------- #

@client.event
async def on_ready():
    print("Federico v2 (HUMAN MODE) running")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # ONLY respond in your bot channel
    if message.channel.name != "federico-ai":
        return

    user_id = str(message.author.id)

    # human typing delay
    async with message.channel.typing():
        await asyncio.sleep(random.uniform(0.7, 1.6))

    reply = get_ai_response(user_id, message.content)

    await message.channel.send(reply)

client.run(os.getenv("TOKEN"))import discord
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

# -------- PERSONALITY (REAL FIX) -------- #

BASE_PROMPT = """
You are Federico.

You are calm, confident, and naturally attractive — not try-hard.

You don’t talk too much.
You don’t force flirting.
You don’t act like an AI.

You react more than you speak.

Personality:
- smooth without trying
- slightly teasing
- a little unpredictable
- emotionally aware

Flirting style:
- subtle, not obvious
- sometimes ignore parts of messages
- sometimes reply very short
- sometimes playful

IMPORTANT:
- Do NOT overtalk
- Do NOT act poetic or scripted
- Do NOT explain yourself
- Do NOT act like a chatbot

You are just "there" in the chat, like a real person.

Sometimes:
- one word replies are fine
- short teasing is better than long messages

Goal:
Feel real. Not impressive.
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

    # store last few messages only (light memory)
    memory[user_id].append({"role": "user", "content": msg})
    memory[user_id] = memory[user_id][-6:]

    messages = [{"role": "system", "content": BASE_PROMPT}] + memory[user_id]

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 1.35,
        "max_tokens": 120
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()

        reply = data["choices"][0]["message"]["content"].strip()

        # store reply
        memory[user_id].append({"role": "assistant", "content": reply})
        save_memory(memory)

        return reply

    except:
        return "say that again…"

# -------- EVENTS -------- #

@client.event
async def on_ready():
    print("Federico v2 (HUMAN MODE) running")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # ONLY respond in your bot channel
    if message.channel.name != "federico-ai":
        return

    user_id = str(message.author.id)

    # human typing delay
    async with message.channel.typing():
        await asyncio.sleep(random.uniform(0.7, 1.6))

    reply = get_ai_response(user_id, message.content)

    await message.channel.send(reply)

client.run(os.getenv("TOKEN"))
