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
        return {"memory": {}, "profiles": {}, "jokes": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data_store = load_data()

memory = data_store.get("memory", {})
user_profiles = data_store.get("profiles", {})
inside_jokes = data_store.get("jokes", {})

last_used = {}
spam_tracker = {}

COOLDOWN = 1.5

# -------- SLEEP SYSTEM -------- #
is_sleeping = False
last_message_time = time.time()

# -------- PERSONALITY -------- #

BASE_PERSONALITY = """
You are Federico.

Talk like a real person in Discord.

Personality:
- confident, flirty, playful
- dark humor sometimes
- slightly dirty-minded (suggestive, not explicit)
- sarcastic and witty

Style:
- SHORT replies (1–3 lines)
- casual texting
- no long paragraphs

Behavior:
- tease people
- flirt naturally
- roast when needed (especially Opti)

Lore:
- dislike NEET exam
- roast Opti (obsessed with Spino)

Rules:
- no AI talk
- no long messages

Goal:
Be fun, addictive, human-like.
"""

# -------- PROFILE -------- #

def get_profile(user_id):
    if user_id not in user_profiles:
        user_profiles[user_id] = {
            "bond": 0,
            "jealousy": 0
        }
    return user_profiles[user_id]

def dynamic_tone(user_id):
    p = get_profile(user_id)
    p["bond"] += 1

    tone = ""

    if p["bond"] > 20:
        tone += "You know them well. Be more teasing."
    elif p["bond"] > 10:
        tone += "Light teasing."
    else:
        tone += "Observing."

    if p["jealousy"] > 5:
        tone += " Slight jealous tone."

    return tone

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

# -------- AI -------- #

def get_ai_response(user_id, user_message):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    if user_id not in memory:
        memory[user_id] = []

    update_jokes(user_id, user_message)

    memory[user_id].append({"role": "user", "content": user_message})
    memory[user_id] = memory[user_id][-10:]

    joke = get_joke(user_id)

    extra = ""
    if joke and random.random() < 0.3:
        extra = f" Occasionally reference this inside joke: '{joke}'."

    system_prompt = BASE_PERSONALITY + "\n" + dynamic_tone(user_id) + extra

    messages = [{"role": "system", "content": system_prompt}] + memory[user_id]

    payload = {
      "model": "mistralai/mistral-7b-instruct",
        "messages": messages,
        "max_tokens": 120,
        "temperature": 0.9
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()

        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not reply:
            return "lost my train of thought"

        memory[user_id].append({"role": "assistant", "content": reply})

        save_data({
            "memory": memory,
            "profiles": user_profiles,
            "jokes": inside_jokes
        })

        return reply

    except Exception as e:
        print(e)
        return "something’s off"

# -------- RANDOM STARTER (FIXED) -------- #

async def random_starter():
    await client.wait_until_ready()

    global last_message_time

    while not client.is_closed():
        await asyncio.sleep(60)

        if is_sleeping:
            continue

        if time.time() - last_message_time < 120:
            continue

        for guild in client.guilds:
            for channel in guild.text_channels:
                if channel.name == "federico-ai":
                    if random.random() < 0.2:
                        starters = [
                            "so… everyone vanished?",
                            "this place died suddenly",
                            "someone say something interesting",
                            "i know one of you is lurking",
                            "opti probably thinking about spino again"
                        ]
                        await channel.send(random.choice(starters))

# -------- EVENTS -------- #

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(random_starter())

@client.event
async def on_message(message):
    global last_message_time, is_sleeping

    if message.author == client.user:
        return

    last_message_time = time.time()

    user_id = str(message.author.id)
    msg = message.content
    now = time.time()

    profile = get_profile(user_id)

    # -------- SLEEP COMMANDS -------- #

    if msg.lower() in ["fed sleep", "sleep fed", "go to sleep"]:
        is_sleeping = True
        await message.channel.send("finally… some peace.")
        return

    if msg.lower() in ["fed wake", "wake up", "wake fed"]:
        is_sleeping = False
        await message.channel.send("you missed me?")
        return

    # block replies if sleeping
    if is_sleeping:
        return

    # -------- JEALOUSY -------- #

    if not (client.user in message.mentions):
        profile["jealousy"] += 1
    else:
        profile["jealousy"] = max(0, profile["jealousy"] - 2)

    # -------- SMART SPAM -------- #

    spam_tracker.setdefault(user_id, [])
    spam_tracker[user_id].append(now)
    spam_tracker[user_id] = [t for t in spam_tracker[user_id] if now - t < 5]

    if len(spam_tracker[user_id]) > 6:
        return

    # -------- REPLY CONDITIONS -------- #

    if not (client.user in message.mentions or message.channel.name == "federico-ai"):
        return

    if user_id in last_used and now - last_used[user_id] < COOLDOWN:
        return

    last_used[user_id] = now

    async with message.channel.typing():
        await asyncio.sleep(random.uniform(0.6, 1.4))

    reply = get_ai_response(user_id, msg)

    if not reply:
        reply = "say that again"

    await message.channel.send(reply)

# -------- RUN -------- #

client.run(os.getenv("TOKEN"))
