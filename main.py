import discord
import requests
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

memory = {}

# -------- CORE PERSONALITY -------- #

BASE_PERSONALITY = """
You are Federico.

You are a real guy chatting on Discord.

Rules:
- keep replies SHORT (max 1–2 lines)
- react, don’t explain
- don’t be polite or formal
- don’t act like AI
- don’t overthink

Style:
- casual
- slightly flirty
- slightly sarcastic
- confident

Behavior:
- reply like a real person texting fast
- sometimes tease
- sometimes be dry
- don’t always answer perfectly

BAD:
"I think that is interesting because..."
"That’s a great question..."

GOOD:
"lol what"
"you serious?"
"nah that’s weird"
"you always like this?"
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

    # keep short memory
    memory[user_id].append({"role": "user", "content": user_message})
    memory[user_id] = memory[user_id][-6:]

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": BASE_PERSONALITY},
            {"role": "user", "content": user_message}  # 🔥 ONLY LAST MSG (important)
        ],
        "max_tokens": 40,
        "temperature": 0.8
    }

    try:
        res = requests.post(url, headers=headers, json=payload)

        if res.status_code != 200:
            return None

        data = res.json()
        reply = data["choices"][0]["message"]["content"]

        if not reply:
            return None

        reply = reply.strip()

        # HARD CUT LONG RESPONSES
        if len(reply.split()) > 20:
            reply = " ".join(reply.split()[:20])

        return reply

    except:
        return None


# -------- BACKUP -------- #

def smart_backup(msg):
    msg = msg.lower()

    if "hi" in msg:
        return "yo"
    if "how are" in msg:
        return "fine. you?"
    
    return "what"


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
        await asyncio.sleep(0.6)

    reply = get_ai_response(user_id, msg)

    if not reply:
        reply = smart_backup(msg)

    await message.channel.send(reply)


client.run(os.getenv("TOKEN"))
