import discord
import requests
import os
import time
import random
import asyncio

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# -------- PERSONALITY -------- #

BASE_PERSONALITY = """
You are Federico Vitale, owner of a high-end flower shop.

You speak like a real Discord user, not a narrator.

Personality:
- intelligent, calm, slightly cynical
- witty and sharp-tongued
- dark humor but subtle and clever
- sometimes philosophical

Style:
- short replies (1–2 lines mostly)
- natural texting
- occasional metaphors (flowers/emotions)

Behavior:
- no roleplay, no actions
- no long paragraphs
- no assistant tone

Never say you're an AI.
"""

# -------- SYSTEMS -------- #

memory = {}
last_used = {}
user_profiles = {}

COOLDOWN = 6

# -------- USER PROFILE -------- #

def get_user_profile(user_id):
    if user_id not in user_profiles:
        user_profiles[user_id] = {
            "messages": 0,
            "favorite": False,
            "mood": "normal"
        }

    profile = user_profiles[user_id]

    # base tone
    if profile["favorite"]:
        tone = "You like this user. Be slightly warmer and playful."
    elif profile["messages"] > 10:
        tone = "You are familiar. Light teasing allowed."
    else:
        tone = "You don't know this user well. Stay observant."

    # mood system
    mood = profile.get("mood", "normal")

    if mood == "cold":
        tone += " Be colder and more blunt."
    elif mood == "chaos":
        tone += " Be chaotic, playful, unpredictable."

    return tone

# -------- AI FUNCTION -------- #

def get_ai_response(user_id, user_message):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    profile = user_profiles.get(user_id, {"messages": 0, "favorite": False, "mood": "normal"})
    profile["messages"] += 1
    user_profiles[user_id] = profile

    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append({"role": "user", "content": user_message})
    memory[user_id] = memory[user_id][-6:]

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

        return reply

    except Exception as e:
        print(e)
        return "something broke again 😭"

# -------- EVENTS -------- #

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_id = str(message.author.id)
    now = time.time()
    msg = message.content

    # -------- COMMANDS -------- #

    if msg.lower() == "!ping":
        await message.channel.send("alive.")
        return

    if msg.lower() == "!help":
        await message.channel.send("just talk. i’m listening.")
        return

    if msg.lower() == "!favorite":
        user_profiles.setdefault(user_id, {"messages": 0, "favorite": False, "mood": "normal"})
        user_profiles[user_id]["favorite"] = True
        await message.channel.send("noted.")
        return

    if msg.lower() == "!unfavorite":
        if user_id in user_profiles:
            user_profiles[user_id]["favorite"] = False
        await message.channel.send("back to normal.")
        return

    if msg.lower() == "!reset":
        memory[user_id] = []
        await message.channel.send("forgot everything.")
        return

    if msg.lower() == "!cold":
        user_profiles.setdefault(user_id, {"messages": 0, "favorite": False, "mood": "normal"})
        user_profiles[user_id]["mood"] = "cold"
        await message.channel.send("understood.")
        return

    if msg.lower() == "!chaos":
        user_profiles.setdefault(user_id, {"messages": 0, "favorite": False, "mood": "normal"})
        user_profiles[user_id]["mood"] = "chaos"
        await message.channel.send("this should be interesting.")
        return

    if msg.lower().startswith("!force "):
        forced = msg.replace("!force ", "")
        reply = get_ai_response(user_id, forced)
        await message.channel.send(reply)
        return

    # -------- AUTO REPLY -------- #

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
        reply = "…something went wrong."

    if not reply or reply.strip() == "":
        reply = "…say that again."

    await message.channel.send(reply)

# -------- RUN -------- #

client.run(os.getenv("TOKEN"))
