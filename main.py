import discord
import requests
import os
import time
import asyncio

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

memory = {}

BASE_PERSONALITY = """
You are Federico.

Talk like a real human.

- casual
- natural
- slightly flirty
- witty

Never give boring replies.
Always respond properly.
"""

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
    memory[user_id] = memory[user_id][-6:]

    payload = {
        "model": "llama-3.1-8b-instant",  # ✅ FIXED MODEL
        "messages": [{"role": "system", "content": BASE_PERSONALITY}] + memory[user_id],
        "max_tokens": 120,
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

        memory[user_id].append({"role": "assistant", "content": reply})
        return reply

    except Exception as e:
        print("ERROR:", e)
        return None


def smart_backup(msg):
    msg = msg.lower()

    if "hi" in msg:
        return "hey."
    if "how are" in msg:
        return "i'm good. you?"
    
    return "say that again properly"


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
        await asyncio.sleep(1)

    reply = get_ai_response(user_id, msg)

    if not reply:
        reply = smart_backup(msg)

    await message.channel.send(reply)


client.run(os.getenv("TOKEN"))
