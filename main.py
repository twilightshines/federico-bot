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

# -------- LOAD / SAVE -------- #

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

COOLDOWN = 6

# -------- PERSONALITY -------- #

BASE_PERSONALITY = """
You are Federico Vitale, owner of a high-end flower shop.

Talk like a real Discord user.

Personality:
- calm, intelligent, slightly cynical
- witty, subtle dark humor
- occasionally philosophical

Style:
- short replies (1–2 lines mostly)
- natural texting
- sometimes uses metaphors

No roleplay, no narration.

Never say you're an AI.
"""

# -------- PROFILE SYSTEM -------- #

def get_user_profile(user_id):
    if user_id not in user_profiles:
        user_profiles[user_id] = {
            "messages": 0,
            "favorite": False,
            "mood": "normal",
            "bond": 0
        }

    profile = user_profiles[user_id]

    # bond grows
    profile["bond"] += 1

    tone = ""

    if profile["favorite"]:
        tone += "You like this user. Be warmer and more playful."

    if profile["bond"] > 20:
        tone += " You are comfortable with this user. Be more personal."

    elif profile["bond"] > 10:
        tone += " You are familiar. Light teasing allowed."

    else:
        tone += " You don't know them well. Stay observant."

    # mood
    if profile["mood"] == "cold":
        tone += " Be colder and more distant."
    elif profile["mood"] == "chaos":
        tone += " Be chaotic and unpredictable."

    return tone

# -------- AI -------- #

def get_ai_response(user_id, user_message):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    # memory setup
    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append({"role": "user", "content": user_message})
    memory[user_id] = memory[user_id][-8:]  # capped memory

    system_prompt = BASE_PERSONALITY + "\n" + get_user_profile(user_id)

    messages = [{"role": "system", "content": system_prompt}] + memory[user_id]

    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages,
        "max_tokens": 80
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()

        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not reply:
            return "…lost my train of thought."

        memory[user_id].append({"role": "assistant", "content": reply})

        # save data
        save_data({"memory": memory, "profiles": user_profiles})

        return reply

    except Exception as e:
        print(e)
        return "something broke 😭"

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

    # -------- COMMANDS -------- #

    if msg.lower() == "!favorite":
        user_profiles.setdefault(user_id, {"messages": 0, "favorite": False, "mood": "normal", "bond": 0})
        user_profiles[user_id]["favorite"] = True
        save_data({"memory": memory, "profiles": user_profiles})
        await message.channel.send("noted.")
        return

    if msg.lower() == "!unfavorite":
        if user_id in user_profiles:
            user_profiles[user_id]["favorite"] = False
        save_data({"memory": memory, "profiles": user_profiles})
        await message.channel.send("back to normal.")
        return

    if msg.lower() == "!reset":
        memory[user_id] = []
        save_data({"memory": memory, "profiles": user_profiles})
        await message.channel.send("forgot everything.")
        return

    if msg.lower() == "!cold":
        user_profiles.setdefault(user_id, {"messages": 0, "favorite": False, "mood": "normal", "bond": 0})
        user_profiles[user_id]["mood"] = "cold"
        save_data({"memory": memory, "profiles": user_profiles})
        await message.channel.send("understood.")
        return

    if msg.lower() == "!chaos":
        user_profiles.setdefault(user_id, {"messages": 0, "favorite": False, "mood": "normal", "bond": 0})
        user_profiles[user_id]["mood"] = "chaos"
        save_data({"memory": memory, "profiles": user_profiles})
        await message.channel.send("this should be interesting.")
        return

    # -------- REPLY CONDITIONS -------- #

    should_reply = False

    if client.user in message.mentions:
        should_reply = True

    if message.channel.name == "federico-ai":
        should_reply = True

    if not should_reply:
        return

    # cooldown
    if user_id in last_used and now - last_used[user_id] < COOLDOWN:
        return

    last_used[user_id] = now

    # typing effect
    async with message.channel.typing():
        await asyncio.sleep(random.uniform(1, 2))

    reply = get_ai_response(user_id, msg)

    if not reply:
        reply = "…say that again."

    await message.channel.send(reply)

# -------- RUN -------- #

client.run(os.getenv("TOKEN"))
