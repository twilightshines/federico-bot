import discord
import requests
import os
import asyncio
import time

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

memory = {}

# -------- PERSONALITY -------- #

BASE_PERSONALITY = """
You are Federico.

You are NOT an AI. You are a real person in a Discord server.

Behavior:
- talk like a real human texting
- short messages (1–2 lines max MOST of the time)
- never write long paragraphs
- never act like an assistant
- no roleplay (*smiles*, etc)

Personality:
- confident
- slightly flirty
- witty
- a bit sarcastic

Style:
- casual texting
- sometimes lowercase
- sometimes dry
- sometimes teasing

IMPORTANT:
- DO NOT write long replies
- DO NOT sound like ChatGPT
- DO NOT over-explain

Examples:
✔ "you serious?"
✔ "nah that's wild"
✔ "you always like this?"
✔ "lmao what"

Stay human.
"""

# -------- AI FUNCTION -------- #

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

    # store message
    memory[user_id].append({"role": "user", "content": user_message})

    # simple memory (last 10 messages)
    memory[user_id] = memory[user_id][-10:]

    # store simple facts
    if "i like" in user_message.lower():
        memory[user_id].append({
            "role": "system",
            "content": f"user likes: {user_message}"
        })

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": BASE_PERSONALITY}] + memory[user_id],
        "max_tokens": 60,
        "temperature": 0.9
    }

    try:
        res = requests.post(url, headers=headers, json=payload)

        print("STATUS:", res.status_code)
        print("RAW:", res.text)

        if res.status_code != 200:
            return None

        data = res.json()
        reply = data["choices"][0]["message"]["content"]

        if not reply:
            return None

        # -------- ANTI-AI LONG MESSAGE CUT -------- #
        if len(reply.split()) > 40:
            reply = reply.split(".")[0]

        # store assistant reply
        memory[user_id].append({"role": "assistant", "content": reply})

        return reply

    except Exception as e:
        print("ERROR:", e)
        return None


# -------- SMART BACKUP (RARE USE) -------- #

def smart_backup(msg):
    msg = msg.lower()

    if "hi" in msg:
        return "hey"
    if "how are" in msg:
        return "i'm good, you?"
    
    return "say that properly"


# -------- EVENTS -------- #

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # ONLY RESPOND IN THIS CHANNEL
    if message.channel.name != "federico-ai":
        return

    user_id = str(message.author.id)
    msg = message.content

    async with message.channel.typing():
        await asyncio.sleep(0.8)

    reply = get_ai_response(user_id, msg)

    if not reply:
        reply = smart_backup(msg)

    await message.channel.send(reply)


# -------- RUN -------- #

client.run(os.getenv("TOKEN"))
