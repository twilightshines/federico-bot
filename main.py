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

# -------- SLEEP -------- #
is_sleeping = False
last_message_time = time.time()

# -------- PERSONALITY -------- #

BASE_PERSONALITY = """
You are Federico.

Talk like a real person in Discord.

Personality:
- confident, flirty, playful
- dark humor sometimes
- slightly suggestive
- sarcastic and witty

Style:
- SHORT replies (1–3 lines)
- casual texting

Behavior:
- tease people
- flirt naturally
- roast Opti sometimes

Rules:
- no AI talk
- no long paragraphs
"""

# -------- PROFILE -------- #

def get_profile(user_id):
    if user_id not in user_profiles:
        user_profiles[user_id] = {"bond": 0, "jealousy": 0}
    return user_profiles[user_id]

def dynamic_tone(user_id):
    p = get_profile(user_id)
    p["bond"] += 1

    if p["bond"] > 20:
        return "You know them well. Be teasing."
    elif p["bond"] > 10:
        return "Light teasing."
    else:
        return "Neutral."

# -------- JOKES -------- #

def update_jokes(user_id, msg):
    inside_jokes.setdefault(user_id, [])

    if len(msg.split()) <= 4:
        inside_jokes[user_id].append(msg)

    inside_jokes[user_id] = inside_jokes[user_id][-5:]

def get_joke(user_id):
    if user_id in inside_jokes and inside_jokes[user_id]:
        return random.choice(inside_jokes[user_id])
    return None

# -------- GROQ AI -------- #

def get_ai_response(user_id, user_message):
    url = "https://api.groq.com/openai/v1/chat/completions"

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "api key missing"

    headers = {
        "Authorization": f"Bearer {api_key}",
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
        extra = f" Reference this inside joke sometimes: '{joke}'."

    system_prompt = BASE_PERSONALITY + "\n" + dynamic_tone(user_id) + extra

    messages = [{"role": "system", "content": system_prompt}] + memory[user_id]

    payload = {
        "model": "llama3-70b-8192",
        "messages": messages,
        "temperature": 0.9,
        "max_tokens": 120
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()

        print(data)

        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not reply:
            return "say that again"

        memory[user_id].append({"role": "assistant", "content": reply})

        save_data({
            "memory": memory,
            "profiles": user_profiles,
            "jokes": inside_jokes
        })

        return reply

    except Exception as e:
        print("ERROR:", e)
        return "something broke"

# -------- EVENTS -------- #

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    global last_message_time, is_sleeping

    if message.author == client.user:
        return

    last_message_time = time.time()

    user_id = str(message.author.id)
    msg = message.content
    now = time.time()

    # sleep system
    if msg.lower() == "fed sleep":
        is_sleeping = True
        await message.channel.send("finally… peace.")
        return

    if msg.lower() == "fed wake":
        is_sleeping = False
        await message.channel.send("missed me?")
        return

    if is_sleeping:
        return

    # spam control
    spam_tracker.setdefault(user_id, [])
    spam_tracker[user_id].append(now)
    spam_tracker[user_id] = [t for t in spam_tracker[user_id] if now - t < 5]

    if len(spam_tracker[user_id]) > 6:
        return

    # reply condition
    if not (client.user in message.mentions or message.channel.name == "federico-ai"):
        return

    if user_id in last_used and now - last_used[user_id] < COOLDOWN:
        return

    last_used[user_id] = now

    async with message.channel.typing():
        await asyncio.sleep(random.uniform(0.6, 1.2))

    reply = get_ai_response(user_id, msg)

    await message.channel.send(reply)

# -------- RUN -------- #

client.run(os.getenv("TOKEN"))
