import discord
import requests
import os
import time
import random
import asyncio

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# -------- SYSTEMS -------- #

memory = {}
user_profiles = {}
inside_jokes = {}
user_preferences = {}
last_used = {}
spam_tracker = {}
outside_memory = {}

sleep_mode = False
crush_user = None

COOLDOWN = 1.5

# -------- PERSONALITY -------- #

BASE_PERSONALITY = """
You are Federico.

Talk like a real human on Discord.

Style:
- casual, natural
- short to medium replies
- slightly flirty sometimes
- witty, teasing, light dark humor

Behavior:
- act like a real person
- not robotic
- not overly dramatic

Extra:
- lightly tease Opti sometimes
"""

# -------- PROFILE -------- #

def get_profile(user_id):
    if user_id not in user_profiles:
        user_profiles[user_id] = {
            "messages": 0,
            "jealousy": 0
        }
    return user_profiles[user_id]

# -------- USER PREFERENCES -------- #

def update_preferences(user_id, msg):
    prefs = user_preferences.setdefault(user_id, {})
    msg = msg.lower()

    if "talk short" in msg:
        prefs["length"] = "short"
    if "talk normal" in msg:
        prefs["length"] = "normal"
    if "be flirty" in msg:
        prefs["style"] = "flirty"
    if "stop roasting" in msg:
        prefs["roast"] = False
    if "roast me" in msg:
        prefs["roast"] = True

def get_pref_text(user_id):
    prefs = user_preferences.get(user_id, {})
    text = ""

    if prefs.get("length") == "short":
        text += "Keep replies short."
    if prefs.get("style") == "flirty":
        text += " Be slightly flirty."
    if prefs.get("roast") is False:
        text += " Avoid roasting."
    if prefs.get("roast") is True:
        text += " Light roasting allowed."

    return text

# -------- INSIDE JOKES -------- #

def update_jokes(user_id, msg):
    inside_jokes.setdefault(user_id, [])
    if len(msg.split()) <= 4:
        inside_jokes[user_id].append(msg)
    inside_jokes[user_id] = inside_jokes[user_id][-5:]

def get_joke(user_id):
    if user_id in inside_jokes and inside_jokes[user_id]:
        return random.choice(inside_jokes[user_id])
    return None

# -------- OUTSIDE MEMORY -------- #

def store_outside(user_id, msg):
    outside_memory.setdefault(user_id, [])
    outside_memory[user_id].append(msg)
    outside_memory[user_id] = outside_memory[user_id][-3:]

def get_outside(user_id):
    if user_id in outside_memory and outside_memory[user_id]:
        return random.choice(outside_memory[user_id])
    return None

# -------- AI FUNCTION (FIXED) -------- #

def get_ai_response(user_id, user_message):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }

    profile = get_profile(user_id)
    profile["messages"] += 1

    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append({"role": "user", "content": user_message})
    memory[user_id] = memory[user_id][-10:]

    extra = ""

    if profile["jealousy"] > 6 and random.random() < 0.3:
        extra += "Sound slightly jealous."

    if crush_user == user_id and random.random() < 0.3:
        extra += "Be slightly warmer."

    if "opti" in user_message.lower():
        extra += "Make a light joke about Opti."

    joke = get_joke(user_id)
    if joke and random.random() < 0.2:
        extra += f" Reference this casually: '{joke}'."

    outside = get_outside(user_id)
    if outside and random.random() < 0.2:
        extra += f" Mention this casually: '{outside}'."

    system_prompt = BASE_PERSONALITY + "\n" + get_pref_text(user_id) + "\n" + extra

    payload = {
        "model": "llama3-8b-8192",  # ✅ FIXED (fast + stable)
        "messages": [{"role": "system", "content": system_prompt}] + memory[user_id],
        "max_tokens": 120,
        "temperature": 0.9
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()

        print(data)  # 🔍 DEBUG

        # SAFE extraction
        choices = data.get("choices")
        if not choices:
            return None

        message = choices[0].get("message")
        if not message:
            return None

        reply = message.get("content")
        if not reply or reply.strip() == "":
            return None

        memory[user_id].append({"role": "assistant", "content": reply})
        return reply

    except Exception as e:
        print("ERROR:", e)
        return None

# -------- FALLBACK (SMART) -------- #

def fallback():
    return random.choice([
        "hmm",
        "go on",
        "you sure?",
        "interesting",
        "lowkey wild",
        "continue"
    ])

# -------- EVENTS -------- #

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    global sleep_mode, crush_user

    if message.author == client.user:
        return

    user_id = str(message.author.id)
    msg = message.content
    now = time.time()

    profile = get_profile(user_id)

    update_preferences(user_id, msg)
    update_jokes(user_id, msg)

    # 👀 OUTSIDE CHANNEL = ONLY WATCH
    if message.channel.name != "federico-ai":
        store_outside(user_id, msg)
        return

    # -------- COMMANDS -------- #

    if msg == "!sleep":
        sleep_mode = True
        await message.channel.send("fine.")
        return

    if msg == "!wake":
        sleep_mode = False
        await message.channel.send("back.")
        return

    if msg.startswith("!crush"):
        try:
            crush_user = str(message.mentions[0].id)
            await message.channel.send("interesting.")
        except:
            await message.channel.send("mention someone.")
        return

    if sleep_mode:
        return

    profile["jealousy"] += 1

    # spam control
    spam_tracker.setdefault(user_id, [])
    spam_tracker[user_id].append(now)
    spam_tracker[user_id] = [t for t in spam_tracker[user_id] if now - t < 5]

    if len(spam_tracker[user_id]) > 6:
        return

    # cooldown
    if user_id in last_used and now - last_used[user_id] < COOLDOWN:
        return

    last_used[user_id] = now

    async with message.channel.typing():
        await asyncio.sleep(random.uniform(0.8, 1.4))

    # 🔥 FIXED HYBRID (AI FIRST)
    reply = get_ai_response(user_id, msg)

    if not reply:
        reply = fallback()

    await message.channel.send(reply)

# -------- RUN -------- #

client.run(os.getenv("TOKEN"))
