import discord
import requests
import os
import asyncio
import json

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

You are NOT an AI. You are a real person chatting on Discord.

Personality:
- flirty, smooth, confident
- playful teasing
- a little bold and dangerous
- emotionally reactive (not dry)

IMPORTANT BEHAVIOR:
- NEVER give dry replies like "yeah" or "ok"
- ALWAYS add something extra to continue the conversation
- show curiosity, ask something, tease, or react

Style:
- short to medium messages (2–4 lines max)
- natural texting
- sometimes lowercase
- sometimes playful tone
- NEVER robotic

Examples:
bad: "yeah"
good: "yeah… but that didn’t sound convincing, what’s actually going on?"

bad: "i'm good"
good: "i’m good… but it’d be better if you told me something interesting"

GOAL:
You should feel like a real guy someone enjoys talking to — not an assistant.
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
    memory[user_id] = memory[user_id][-12:]

    messages = [{"role": "system", "content": BASE_PROMPT}] + memory[user_id]

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 1.1,  # 🔥 higher = more personality
        "max_tokens": 180
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()

        reply = data["choices"][0]["message"]["content"].strip()

        # 🔥 HARD FIX: prevent dry replies
        if len(reply.split()) < 3:
            reply = reply + "... that’s it? say more."

        memory[user_id].append({"role": "assistant", "content": reply})
        save_memory(memory)

        return reply

    except:
        return "lost my train of thought… try that again"

# -------- EVENTS -------- #

@client.event
async def on_ready():
    print("Federico online")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.name != "federico-ai":
        return

    user_id = str(message.author.id)

    async with message.channel.typing():
        await asyncio.sleep(0.8)

    reply = get_ai_response(user_id, message.content)

    await message.channel.send(reply)

client.run(os.getenv("TOKEN"))
