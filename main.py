import discord
import requests
import os
import asyncio
import random

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

memory = {}

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

    # store message
    memory[user_id].append({"role": "user", "content": user_message})
    memory[user_id] = memory[user_id][-10:]

    # -------- RANDOM MOOD -------- #
    moods = ["normal", "dry", "playful", "flirty", "slightly rude"]
    mood = random.choice(moods)

    # -------- DYNAMIC PERSONALITY -------- #
    personality = f"""
You are Federico.

Current mood: {mood}

Talk like a real human in Discord.

Rules:
- short replies mostly (1–2 lines)
- sometimes 1 word replies
- sometimes dry
- sometimes teasing
- sometimes ignore parts of message

IMPORTANT:
- never sound like AI
- no long explanations
- no roleplay (*smiles*, etc)
- be slightly unpredictable

Examples:
user: hi → "yo" / "hm" / "you again?"
user: how are you → "alive" / "could be worse"
user: you interesting → "you just noticed?"

Stay human.
"""

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": personality}] + memory[user_id],
        "max_tokens": random.randint(20, 60),
        "temperature": 1.2
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

        # -------- ANTI-LONG REPLY -------- #
        if len(reply.split()) > 30:
            reply = reply.split(".")[0]

        # -------- RANDOM SHORT CUT -------- #
        if random.random() < 0.25:
            reply = reply.split("\n")[0]

        memory[user_id].append({"role": "assistant", "content": reply})

        return reply

    except Exception as e:
        print("ERROR:", e)
        return None


# -------- BACKUP -------- #

def smart_backup(msg):
    msg = msg.lower()

    if "hi" in msg:
        return "hey"
    if "how are" in msg:
        return "i'm fine, you?"
    
    return random.choice([
        "say that again",
        "what",
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

    # only respond in this channel
    if message.channel.name != "federico-ai":
        return

    user_id = str(message.author.id)
    msg = message.content

    async with message.channel.typing():
        await asyncio.sleep(random.uniform(0.5, 1.0))

    reply = get_ai_response(user_id, msg)

    if not reply:
        reply = smart_backup(msg)

    await message.channel.send(reply)


# -------- RUN -------- #

client.run(os.getenv("TOKEN"))
