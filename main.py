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
PROFILE_FILE = "profiles.json"

# -------- LOAD -------- #

def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

memory = load_json(MEMORY_FILE)
profiles = load_json(PROFILE_FILE)

# -------- PROFILE SYSTEM -------- #

def get_profile(user_id):
    if user_id not in profiles:
        profiles[user_id] = {
            "messages": 0,
            "crush": False,
            "style": "normal",
            "inside_jokes": []
        }
    return profiles[user_id]

# -------- PERSONALITY -------- #

BASE_PROMPT = """
You are Federico.

You are a real human in a Discord chat.

Personality:
- flirty, smooth, confident
- playful teasing
- slightly possessive sometimes
- emotionally reactive

Behavior rules:
- NEVER give dry replies
- ALWAYS continue the conversation
- react to tone (short replies = tease them)
- flirt more if comfortable
- sometimes act jealous playfully

Style:
- natural texting
- short to medium replies (2–4 lines)
- lowercase sometimes
- casual, not formal

IMPORTANT:
You are NOT an assistant. You are a person people get attached to.
"""

# -------- AI -------- #

def get_ai_response(user_id, username, msg):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    profile = get_profile(user_id)
    profile["messages"] += 1

    # ---- detect preferences ---- #
    if "short" in msg.lower():
        profile["style"] = "short"
    if "flirty" in msg.lower():
        profile["style"] = "flirty"

    # ---- memory ---- #
    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append({"role": "user", "content": msg})
    memory[user_id] = memory[user_id][-12:]

    # ---- dynamic behavior ---- #
    mood = ""

    if profile["crush"]:
        mood += "You secretly like this user. Be more flirty and attentive.\n"

    if profile["messages"] > 20:
        mood += "You are comfortable with this user. Tease more.\n"

    if len(msg.split()) <= 2:
        mood += "User gave a dry reply. Tease them for it.\n"

    system_prompt = BASE_PROMPT + "\n" + mood

    messages = [{"role": "system", "content": system_prompt}] + memory[user_id]

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 1.1,
        "max_tokens": 180
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()

        reply = data["choices"][0]["message"]["content"].strip()

        # prevent dry reply
        if len(reply.split()) < 3:
            reply += "... that's it? try again."

        memory[user_id].append({"role": "assistant", "content": reply})

        save_json(MEMORY_FILE, memory)
        save_json(PROFILE_FILE, profiles)

        return reply

    except:
        return "lost focus… say that again"

# -------- EVENTS -------- #

@client.event
async def on_ready():
    print("Federico v3 online 😈")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.name != "federico-ai":
        return

    user_id = str(message.author.id)
    username = message.author.name

    # ---- random crush assignment ---- #
    profile = get_profile(user_id)
    if not profile["crush"] and random.random() < 0.03:
        profile["crush"] = True

    async with message.channel.typing():
        await asyncio.sleep(random.uniform(0.6, 1.2))

    reply = get_ai_response(user_id, username, message.content)

    await message.channel.send(reply)

client.run(os.getenv("TOKEN"))
