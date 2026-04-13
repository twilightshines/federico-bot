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
You are Federico.

You talk like a real human on Discord.

Style:
- casual, natural, short-medium replies
- slightly flirty sometimes
- witty, teasing, a bit dark humor
- not poetic, not robotic

Behavior:
- respond like a person in a group chat
- don’t over-explain
- don’t act like an assistant
- don’t use roleplay actions

Extra:
- lightly tease "Opti"
- remember users over time
"""

# -------- SYSTEMS -------- #

memory = {}
last_used = {}
user_profiles = {}
sleep_mode = False

COOLDOWN = 2   # very small so it feels active

# -------- USER PROFILE -------- #

def get_user_profile(user_id):
    if user_id not in user_profiles:
        user_profiles[user_id] = {
            "messages": 0,
            "favorite": False
        }

    profile = user_profiles[user_id]

    if profile["favorite"]:
        tone = "You like this user. Be warmer and slightly flirty."
    elif profile["messages"] > 15:
        tone = "You know this user. Light teasing allowed."
    else:
        tone = "You don’t know this user well. Stay neutral but curious."

    return tone

# -------- AI FUNCTION -------- #

def get_ai_response(user_id, user_message):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    # update profile
    profile = user_profiles.get(user_id, {"messages": 0})
    profile["messages"] += 1
    user_profiles[user_id] = profile

    # memory
    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append({"role": "user", "content": user_message})
    memory[user_id] = memory[user_id][-8:]

    system_prompt = BASE_PERSONALITY + "\n" + get_user_profile(user_id)

    messages = [{"role": "system", "content": system_prompt}] + memory[user_id]

    payload = {
        "model": "meta-llama/llama-3-8b-instruct",
        "messages": messages,
        "max_tokens": 120
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()

        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        # rate limit or fail fallback
        if not reply or "rate limit" in str(data).lower():
            return random.choice([
                "chat’s moving too fast… say that again",
                "one at a time damn 😭",
                "slow down, i’m not infinite",
                "repeat that, lost it mid thought"
            ])

        memory[user_id].append({"role": "assistant", "content": reply})
        return reply

    except Exception as e:
        print(e)
        return random.choice([
            "something broke 😭",
            "my brain lagged",
            "yeah that didn’t process",
            "try that again"
        ])

# -------- HUMAN-LIKE FALLBACK REPLIES -------- #

def human_fallback(user_id, msg):
    msg = msg.lower()

    if "hi" in msg or "hello" in msg:
        return random.choice([
            "yo",
            "hey",
            "hi… took you long enough",
            "what’s up"
        ])

    if "how are you" in msg:
        return random.choice([
            "alive. barely",
            "doing better than opti",
            "could be worse",
            "depends who’s asking"
        ])

    if "opti" in msg:
        return random.choice([
            "opti still stuck on spino?",
            "opti needs help fr",
            "don’t bring that guy up",
            "he still coping?"
        ])

    return random.choice([
        "hmm",
        "go on",
        "i’m listening",
        "that’s interesting",
        "you sure about that?",
        "lowkey wild",
        "explain that better"
    ])

# -------- EVENTS -------- #

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    global sleep_mode

    if message.author == client.user:
        return

    user_id = str(message.author.id)
    now = time.time()
    msg = message.content.lower()

    # -------- COMMANDS -------- #

    if msg == "!sleep":
        sleep_mode = True
        await message.channel.send("fine. i’ll be quiet.")
        return

    if msg == "!wake":
        sleep_mode = False
        await message.channel.send("i’m back.")
        return

    if msg == "!favorite":
        user_profiles[user_id]["favorite"] = True
        await message.channel.send("noted.")
        return

    if msg == "!unfavorite":
        user_profiles[user_id]["favorite"] = False
        await message.channel.send("back to normal.")
        return

    if sleep_mode:
        return

    # -------- SHOULD REPLY LOGIC -------- #

    should_reply = False

    if client.user in message.mentions:
        should_reply = True

    elif message.channel.name == "federico-ai":
        should_reply = True

    # smart random replies so not ghosting but not spamming
    elif random.random() < 0.4:
        should_reply = True

    if not should_reply:
        return

    # cooldown (very small)
    if user_id in last_used and now - last_used[user_id] < COOLDOWN:
        return

    last_used[user_id] = now

    # typing effect
    async with message.channel.typing():
        await asyncio.sleep(random.uniform(0.8, 1.5))

    # -------- HYBRID RESPONSE -------- #

    # 60% fallback (FREE) | 40% AI
    if random.random() < 0.6:
        reply = human_fallback(user_id, msg)
    else:
        reply = get_ai_response(user_id, msg)

    if not reply or reply.strip() == "":
        reply = "say that again"

    await message.channel.send(reply)

# -------- RUN -------- #

client.run(os.getenv("TOKEN"))
