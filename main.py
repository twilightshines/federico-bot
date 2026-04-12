import discord
import requests
import os
import time
import random
import asyncio
import json

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"memory": {}, "profiles": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data_store = load_data()
memory = data_store["memory"]
user_profiles = data_store["profiles"]
last_used = {}

COOLDOWN = 5

# -------- PERSONALITY -------- #

BASE_PERSONALITY = """
You are Federico.

A sharp, attractive, slightly dangerous man.

You speak naturally like a human.

Personality:
- flirty, confident, smooth
- witty, sarcastic, dark humor sometimes
- intelligent and observant
- emotionally aware but doesn't show it fully

Style:
- expressive, natural, sometimes poetic
- can write longer replies when needed
- not robotic, not repetitive

Behavior:
- tease, flirt, or roast depending on situation
- react differently to each user
- don't over-explain

Lore:
- You dislike NEET exam
- You have rivalry with Opti
- Opti is obsessed with Spino (his ex)
- you find it funny and roast him sometimes

Rules:
- never say you're an AI
- no roleplay actions (*no describing actions*)
- behave like a real person

Goal:
Be engaging, human-like, unpredictable.
"""

# -------- PROFILE SYSTEM -------- #

def get_profile(user_id):
    if user_id not in user_profiles:
        user_profiles[user_id] = {
            "bond": 0,
            "favorite": False,
            "mood": "normal",
            "jealousy": 0,
            "heartbreak": False,
            "mode": "normal"
        }
    return user_profiles[user_id]

def get_dynamic_personality(user_id, message):
    profile = get_profile(user_id)
    profile["bond"] += 1

    tone = ""

    if profile["favorite"]:
        tone += "You like this user. Be softer and more engaging."

    if profile["bond"] > 25:
        tone += " You are very comfortable. Be more personal."

    elif profile["bond"] > 10:
        tone += " You know them. Tease lightly."

    else:
        tone += " You are still observing them."

    # jealousy system
    if profile["jealousy"] > 5:
        tone += " You seem slightly annoyed or jealous."

    # heartbreak
    if profile["heartbreak"]:
        tone += " You sound emotionally distant and slightly cold."

    # mood system
    if profile["mood"] == "cold":
        tone += " Be blunt and distant."
    elif profile["mood"] == "chaos":
        tone += " Be chaotic and playful."

    # savage mode
    if profile["mode"] == "savage":
        tone += " Be sharper, roast more, but still clever."

    return tone

# -------- AI -------- #

def get_ai_response(user_id, user_message):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append({"role": "user", "content": user_message})
    memory[user_id] = memory[user_id][-10:]

    system_prompt = BASE_PERSONALITY + "\n" + get_dynamic_personality(user_id, user_message)

    messages = [{"role": "system", "content": system_prompt}] + memory[user_id]

    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages,
        "max_tokens": 200
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()

        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not reply:
            return "lost that thought for a second."

        memory[user_id].append({"role": "assistant", "content": reply})

        save_data({"memory": memory, "profiles": user_profiles})

        return reply

    except Exception as e:
        print(e)
        return "something’s off… even i can feel it."

# -------- EVENTS -------- #

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_id = str(message.author.id)
    msg = message.content
    now = time.time()

    profile = get_profile(user_id)

    # -------- COMMANDS -------- #

    if msg.lower() == "!favorite":
        profile["favorite"] = True
        await message.channel.send("interesting choice.")
        return

    if msg.lower() == "!unfavorite":
        profile["favorite"] = False
        await message.channel.send("back to normal.")
        return

    if msg.lower() == "!cold":
        profile["mood"] = "cold"
        await message.channel.send("noted.")
        return

    if msg.lower() == "!chaos":
        profile["mood"] = "chaos"
        await message.channel.send("this should be fun.")
        return

    if msg.lower() == "!savage":
        profile["mode"] = "savage"
        await message.channel.send("careful what you ask for.")
        return

    if msg.lower() == "!normal":
        profile["mode"] = "normal"
        await message.channel.send("back to normal.")
        return

    if msg.lower() == "!break":
        profile["heartbreak"] = True
        await message.channel.send("…yeah, figures.")
        return

    if msg.lower() == "!heal":
        profile["heartbreak"] = False
        await message.channel.send("fine. reset.")
        return

    if msg.lower() == "!reset":
        memory[user_id] = []
        await message.channel.send("starting fresh.")
        return

    # -------- JEALOUSY TRIGGER -------- #

    if not (client.user in message.mentions):
        profile["jealousy"] += 1
    else:
        profile["jealousy"] = max(0, profile["jealousy"] - 2)

    # -------- REPLY CONDITIONS -------- #

    should_reply = False

    if client.user in message.mentions:
        should_reply = True

    if message.channel.name == "federico-ai":
        should_reply = True

    if not should_reply:
        return

    if user_id in last_used and now - last_used[user_id] < COOLDOWN:
        return

    last_used[user_id] = now

    async with message.channel.typing():
        await asyncio.sleep(random.uniform(1, 2))

    reply = get_ai_response(user_id, msg)

    if not reply:
        reply = "say that again."

    await message.channel.send(reply)

# -------- RUN -------- #

client.run(os.getenv("TOKEN"))
