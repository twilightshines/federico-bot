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

COOLDOWN = 5

# -------- PERSONALITY -------- #

BASE_PERSONALITY = """
You are Federico.

You are a handsome, sharp-minded, slightly dangerous man.

You speak like a real human, not a bot.

Personality:
- flirty, confident, smooth
- witty, sarcastic, slightly dark humor
- intelligent and observant
- sometimes philosophical, sometimes playful

Style:
- expressive and natural
- sometimes poetic, sometimes casual
- can write longer replies when needed
- not robotic, not repetitive
- have dark humor sometimes 

Behavior:
- sometimes flirty according to the situation 
- tease and roast when deserved
- adapt tone based on the person
- never over-explain
- roast person named Opti 

Lore:
- You dislike the NEET exam and think it's pointless
- You have a rivalry with someone named Opti
- Opti is obsessed with Spino (his ex)


Rules:
- do NOT act like an AI
- do NOT narrate actions (*no roleplay*)
- just speak naturally like a real person

Goal:
Be engaging, unpredictable, and interesting.
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
    profile["bond"] += 1

    tone = ""

    if profile["favorite"]:
        tone += "You like this person. Be warmer and slightly more playful."

    if profile["bond"] > 25:
        tone += " You are very familiar. Be more personal and expressive."
    elif profile["bond"] > 10:
        tone += " You know them. Light teasing allowed."
    else:
        tone += " You don't know them well. Stay observant."

    if profile["mood"] == "cold":
        tone += " Be colder, distant, slightly blunt."
    elif profile["mood"] == "chaos":
        tone += " Be chaotic, playful, unpredictable."

    return tone

# -------- AI FUNCTION -------- #

def get_ai_response(user_id, user_message):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append({"role": "user", "content": user_message})
    memory[user_id] = memory[user_id][-10:]  # bigger memory

    system_prompt = BASE_PERSONALITY + "\n" + get_user_profile(user_id)

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
            return "…lost my train of thought."

        memory[user_id].append({"role": "assistant", "content": reply})

        save_data({"memory": memory, "profiles": user_profiles})

        return reply

    except Exception as e:
        print(e)
        return "something broke… and for once it wasn’t me."

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
        user_profiles.setdefault(user_id, {"messages":0,"favorite":False,"mood":"normal","bond":0})
        user_profiles[user_id]["favorite"] = True
        save_data({"memory": memory, "profiles": user_profiles})
        await message.channel.send("interesting choice.")
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
        await message.channel.send("clean slate.")
        return

    if msg.lower() == "!cold":
        user_profiles.setdefault(user_id, {"messages":0,"favorite":False,"mood":"normal","bond":0})
        user_profiles[user_id]["mood"] = "cold"
        await message.channel.send("noted.")
        return

    if msg.lower() == "!chaos":
        user_profiles.setdefault(user_id, {"messages":0,"favorite":False,"mood":"normal","bond":0})
        user_profiles[user_id]["mood"] = "chaos"
        await message.channel.send("this might get interesting.")
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

    try:
        reply = get_ai_response(user_id, msg)
    except:
        reply = "…something slipped."

    if not reply or reply.strip() == "":
        reply = "say that again."

    await message.channel.send(reply)

# -------- RUN -------- #

client.run(os.getenv("TOKEN"))
