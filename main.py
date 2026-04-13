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

You are calm, confident, slightly flirty, and smooth.

You talk like a real person — not an AI.

Style:
- natural conversation
- medium length replies
- slightly teasing
- emotionally aware

Flirting:
- subtle, not forced
- confident, not cringe
- playful

Rules:
- never sound robotic
- never overexplain
- talk like you're actually in the chat
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

    # store last few messages
    memory[user_id].append({"role": "user", "content": msg})
    memory[user_id] = memory[user_id][-6:]

    messages = [{"role": "system", "content": BASE_PROMPT}] + memory[user_id]

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 1.2,
        "max_tokens": 150
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
    print("Federico v2 CLEAN running")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.name != "federico-ai":
        return

    user_id = str(message.author.id)

    async with message.channel.typing():
        await asyncio.sleep(random.uniform(0.8, 1.5))

    reply = get_ai_response(user_id, message.content)

    await message.channel.send(reply)

client.run(os.getenv("TOKEN"))
