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
spam_tracker = {}

COOLDOWN = 1.5  # fast but safe

# -------- PERSONALITY -------- #

BASE_PERSONALITY = """
You are Federico.

A sharp, attractive, slightly dangerous man.

You speak like a real human.

Personality:
- flirty, confident
- witty, sarcastic
- dark humor occasionally
- observant and emotionally aware

Style:
- expressive, natural
- can write longer replies
- sometimes poetic, sometimes casual

Behavior:
- tease, flirt, roast when needed
- adapt tone per user

Lore:
- dislikes NEET exam
- rivals Opti
- Opti is obsessed with Spino (his ex)
- you mock him for it sometimes

Rules:
- no AI talk
- no roleplay actions
- behave like a real person
"""

# -------- PROFILE -------- #

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

def dynamic_tone(user_id):
    p = get_profile(user_id)
    p["bond"] += 1

    tone = ""

    if p["favorite"]:
        tone += "You like them. Be warmer."

    if p["bond"] > 30:
        tone += " Very close. Be personal."
    elif p["bond"] > 10:
        tone += " Familiar. Light teasing."
    else:
        tone += " Observing."

    if p["jealousy"] > 5:
        tone += " Slight jealousy tone."

    if p["heartbreak"]:
        tone += " Emotionally distant."

    if p["mood"] == "cold":
        tone += " Cold and blunt."
    elif p["mood"] == "chaos":
        tone += " Chaotic energy."

    if p["mode"] == "savage":
        tone += " More savage roasting."

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
    memory[user_id] = memory[user_id][-15:]  # increased memory

    system_prompt = BASE_PERSONALITY + "\n" + dynamic_tone(user_id)

    messages = [{"role": "system", "content": system_prompt}] + memory[user_id]

    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages,
        "max_tokens": 300
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()

        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not reply:
            return "lost that thought."

        memory[user_id].append({"role": "assistant", "content": reply})

        save_data({"memory": memory, "profiles": user_profiles})

        return reply

    except Exception as e:
        print(e)
        return "something’s off…"

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
        await message.channel.send("interesting.")
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
        await message.channel.send("careful.")
        return

    if msg.lower() == "!normal":
        profile["mode"] = "normal"
        await message.channel.send("fine.")
        return

    if msg.lower() == "!break":
        profile["heartbreak"] = True
        await message.channel.send("…right.")
        return

    if msg.lower() == "!heal":
        profile["heartbreak"] = False
        await message.channel.send("whatever.")
        return

    if msg.lower() == "!reset":
        memory[user_id] = []
        await message.channel.send("starting over.")
        return

    # -------- JEALOUSY -------- #

    if not (client.user in message.mentions):
        profile["jealousy"] += 1
    else:
        profile["jealousy"] = max(0, profile["jealousy"] - 2)

    # -------- SMART SPAM CONTROL -------- #

    spam_tracker.setdefault(user_id, [])
    spam_tracker[user_id].append(now)
    spam_tracker[user_id] = [t for t in spam_tracker[user_id] if now - t < 5]

    if len(spam_tracker[user_id]) > 5:
        return  # user spamming too fast

    # -------- REPLY CONDITIONS -------- #

    if not (client.user in message.mentions or message.channel.name == "federico-ai"):
        return

    # light cooldown
    if user_id in last_used and now - last_used[user_id] < COOLDOWN:
        return

    last_used[user_id] = now

    async with message.channel.typing():
        await asyncio.sleep(random.uniform(0.8, 1.8))

    reply = get_ai_response(user_id, msg)

    if not reply:
        reply = "say that again."

    await message.channel.send(reply)

# -------- RUN -------- #

client.run(os.getenv("TOKEN"))
