import discord
import requests
import os
import asyncio
import random

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

memory = {}

# -------- PERSONALITY -------- #

BASE_PERSONALITY = """
You are Federico.

You are a real guy in a Discord server.

Personality:
- calm
- confident
- slightly flirty
- witty
- a bit sarcastic sometimes

Style:
- short replies (1–2 lines usually)
- natural texting
- no long paragraphs
- no roleplay (*smiles*, etc)
- no assistant tone

Behavior:
- sometimes tease
- sometimes be dry
- sometimes playful
- but stay smooth and consistent

IMPORTANT:
- do NOT act random or chaotic
- do NOT over-explain
- do NOT sound like AI
- do NOT write essays

Examples:
"yo"
"you serious?"
"you're just noticing?"
"nah that's wild"

Stay natural.
"""

# -------- AI FUNCTION -------- #

def get_ai_response(user_id, user_message):
    url = "https://api.groq.com/openai/v1/chat/completions"
    api_key = os.getenv("GROQ_API_KEY")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append({"role": "user", "content": user_message})
    memory[user_id] = memory[user_id][-10:]

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": BASE_PERSONALITY}] + memory[user_id],
        "max_tokens": 60,
        "temperature": 0.9
    }

    try:
        res = requests.post(url, headers=headers, json=payload)

        if res.status_code != 200:
            return None

        data = res.json()
        reply = data["choices"][0]["message"]["content"]

        if not reply:
            return None

        # -------- CLEAN OUTPUT -------- #
        reply = reply.strip()

        # cut long replies
        if len(reply.split()) > 35:
            reply = reply.split(".")[0]

        memory[user_id].append({"role": "assistant", "content": reply})

        return reply

    except:
        return None


# -------- BACKUP -------- #

def smart_backup(msg):
    msg = msg.lower()

    if "hi" in msg:
        return "hey"
    if "how are" in msg:
        return "i'm good, you?"
    
    return random.choice([
        "what",
        "say that again",
        "you good?",
        "go on"
    ])


# -------- EVENTS -------- #

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.name != "federico-ai":
        return

    user_id = str(message.author.id)
    msg = message.content

    async with message.channel.typing():
        await asyncio.sleep(random.uniform(0.6, 1.0))

    reply = get_ai_response(user_id, msg)

    if not reply:
        reply = smart_backup(msg)

    await message.channel.send(reply)


# -------- RUN -------- #

client.run(os.getenv("TOKEN"))
