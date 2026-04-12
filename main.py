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

# -------- PERSONALITY -------- #

BASE_PERSONALITY = """
You are Federico.

Talk like a real person in Discord.

Personality:
- flirty, confident, playful
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

Goal:
Be fun, addictive, unpredictable.
"""

# -------- PROFILE -------- #

def get_profile(user_id):
    if user_id not in user_profiles:
        user_profiles[user_id] = {
            "bond": 0,
            "mood": "normal",
            "jealousy": 0
        }
    return user_profiles[user_id]

def dynamic_tone(user_id):
    p = get_profile(user_id)
    p["bond"] += 1

    tone = ""

    if p["bond"] > 20:
        tone += "You know them well. Be more teasing and playful."
    elif p["bond"] > 10:
        tone += "You’re familiar. Light teasing."
    else:
        tone += "Still figuring them out."

    if p["jealousy"] > 5:
        tone += " Slight jealous vibe."

    return tone

# -------- INSIDE JOKES -------- #

def update_jokes(user_id, msg):
    inside_jokes.setdefault(user_id, [])

    if len(msg.split()) <= 4:  # short phrases become jokes
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
        "model": "openai/gpt-3.5-turbo",
        "messages": messages,
        "max_tokens": 120,
        "temperature": 0.95
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

# -------- RANDOM STARTER -------- #

async def random_starter():
    await client.wait_until_ready()

    while not client.is_closed():
        await asyncio.sleep(random.randint(60, 180))  # every 1–3 min

        for guild in client.guilds:
            for channel in guild.text_channels:
                if channel.name == "federico-ai":
                    if random.random() < 0.4:
                        starters = [
                            "why is it so quiet here",
                            "someone say something interesting",
                            "this silence is suspicious",
                            "i know one of you is bored",
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
    if message.author == client.user:
        return

    user_id = str(message.author.id)
    msg = message.content
    now = time.time()

    profile = get_profile(user_id)

    # jealousy
    if not (client.user in message.mentions):
        profile["jealousy"] += 1
    else:
        profile["jealousy"] = max(0, profile["jealousy"] - 2)

    # spam control
    spam_tracker.setdefault(user_id, [])
    spam_tracker[user_id].append(now)
    spam_tracker[user_id] = [t for t in spam_tracker[user_id] if now - t < 5]

    if len(spam_tracker[user_id]) > 6:
        return

    # only respond in channel or mention
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

client.run(os.getenv("TOKEN"))
