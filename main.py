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

NEVER give dry replies like "go on", "hmm", etc.
Always respond meaningfully.
"""

def get_ai_response(user_id, user_message):
    url = "https://api.groq.com/openai/v1/chat/completions"

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "API KEY MISSING"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append({"role": "user", "content": user_message})
    memory[user_id] = memory[user_id][-6:]

    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "system", "content": BASE_PERSONALITY}] + memory[user_id],
        "max_tokens": 120
    }

    try:
        res = requests.post(url, headers=headers, json=payload)

        print("STATUS:", res.status_code)
        print("RESPONSE:", res.text)

        if res.status_code != 200:
            return f"API ERROR: {res.status_code}"

        data = res.json()

        reply = data["choices"][0]["message"]["content"]

        if not reply:
            return "EMPTY RESPONSE FROM AI"

        memory[user_id].append({"role": "assistant", "content": reply})
        return reply

    except Exception as e:
        print("ERROR:", e)
        return f"EXCEPTION: {str(e)}"

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

    await message.channel.send(reply)

client.run(os.getenv("TOKEN"))
