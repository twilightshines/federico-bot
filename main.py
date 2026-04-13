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
user_modes = {}
user_preferences = {}
last_used = {}
spam_tracker = {}

sleep_mode = False
crush_user = None
roast_mode = False

COOLDOWN = 1.5

# -------- PERSONALITY -------- #

BASE_PERSONALITY = """
You are Federico.

You talk like a real human on Discord.

Style:
- natural, casual
- short to medium replies (unless user wants otherwise)
- slightly flirty sometimes
- witty, teasing, light dark humor

Behavior:
- adapt to user preferences
- don’t be robotic
- don’t over-explain
- act like a real person

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

def get_user_mode(user_id):
    return user_modes.get(user_id, "chill")

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

def get_preference_text(user_id):
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

# -------- AI -------- #

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

    # -------- EXTRA BEHAVIOR -------- #

    extra = ""

    # jealousy
    if profile["jealousy"] > 6 and random.random() < 0.3:
        extra += "Sound slightly jealous."

    # crush
    if crush_user == user_id and random.random() < 0.3:
        extra += "Be slightly warmer."

    # opti
    if "opti" in user_message.lower():
        extra += "Make a light joke about Opti."

    # inside joke
    joke = get_joke(user_id)
    if joke and random.random() < 0.25:
        extra += f" Reference this: '{joke}'."

    # user preferences
    pref_text = get_preference_text(user_id)

    system_prompt = BASE_PERSONALITY + "\n" + pref_text + "\n" + extra

    payload = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "system", "content": system_prompt}] + memory[user_id],
        "max_tokens": 120,
        "temperature": 0.9
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()

        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not reply or "rate limit" in str(data).lower():
            return random.choice([
                "too many people talking… slow down",
                "say that again",
                "lost that mid-way"
            ])

        memory[user_id].append({"role": "assistant", "content": reply})

        return reply

    except Exception as e:
        print(e)
        return "something broke"

# -------- FALLBACK -------- #

def fallback_reply(msg):
    return random.choice([
        "hmm",
        "go on",
        "you sure?",
        "interesting",
        "lowkey wild"
    ])

# -------- EVENTS -------- #

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    global sleep_mode, crush_user, roast_mode

    if message.author == client.user:
        return

    user_id = str(message.author.id)
    msg = message.content
    now = time.time()

    profile = get_profile(user_id)

    # update memory systems
    update_preferences(user_id, msg)
    update_jokes(user_id, msg)

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

    # jealousy update
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

    # should reply
    if not (client.user in message.mentions or message.channel.name == "federico-ai" or random.random() < 0.4):
        return

    if user_id in last_used and now - last_used[user_id] < COOLDOWN:
        return

    last_used[user_id] = now

    async with message.channel.typing():
        await asyncio.sleep(random.uniform(0.8, 1.5))

    # hybrid system
    if random.random() < 0.5:
        reply = fallback_reply(msg)
    else:
        reply = get_ai_response(user_id, msg)

    if not reply:
        reply = "say that again"

    await message.channel.send(reply)

client.run(os.getenv("TOKEN"))
