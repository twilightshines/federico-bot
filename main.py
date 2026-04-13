import discord
import requests
import os
import time
import random
import asyncio

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

memory = {}
last_used = {}
sleep_mode = False

COOLDOWN = 1.0

BASE_PERSONALITY = """
You are Federico.

Talk like a real human.

Style:
- casual
- natural
- slightly flirty
- witty
- sometimes sarcastic

Behavior:
- respond properly to what user says
- NEVER give generic replies like "continue", "hmm", etc
- always give a meaningful response
"""

# -------- AI FUNCTION (HARD FIXED) -------- #

def get_ai_response(user_id, user_message):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }

    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append({"role": "user", "content": user_message})
    memory[user_id] = memory[user_id][-8:]

    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "system", "content": BASE_PERSONALITY}] + memory[user_id],
        "max_tokens": 120,
        "temperature": 0.9
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)

        print("STATUS:", res.status_code)
        print("RAW:", res.text)  # 🔥 IMPORTANT DEBUG

        if res.status_code != 200:
            return None

        data = res.json()

        reply = data["choices"][0]["message"]["content"]

        if not reply or reply.strip() == "":
            return None

        memory[user_id].append({"role": "assistant", "content": reply})
        return reply

    except Exception as e:
        print("ERROR:", e)
        return None

# -------- BACKUP HUMAN RESPONSE (NOT DUMB) -------- #

def smart_backup(user_message):
    msg = user_message.lower()

    if "how are" in msg:
        return "i'm alright. you?"
    if "hi" in msg or "hello" in msg:
        return "hey."
    if "what" in msg:
        return "depends what you mean"
    if "why" in msg:
        return "good question"
    
    return random.choice([
        "go on",
        "i'm listening",
        "say it properly",
        "you’re being vague"
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

    if message.channel.name != "federico-ai":
        return

    user_id = str(message.author.id)
    msg = message.content
    now = time.time()

    # commands
    if msg == "!sleep":
        sleep_mode = True
        await message.channel.send("fine.")
        return

    if msg == "!wake":
        sleep_mode = False
        await message.channel.send("back.")
        return

    if sleep_mode:
        return

    if user_id in last_used and now - last_used[user_id] < COOLDOWN:
        return

    last_used[user_id] = now

    async with message.channel.typing():
        await asyncio.sleep(random.uniform(0.6, 1.2))

    # 🔥 TRY AI FIRST
    reply = get_ai_response(user_id, msg)

    # 🔥 IF AI FAILS → SMART BACKUP (NOT STUPID)
    if not reply:
        reply = smart_backup(msg)

    await message.channel.send(reply)

# -------- RUN -------- #

client.run(os.getenv("TOKEN"))
