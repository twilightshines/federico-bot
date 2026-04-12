import discord
import requests
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

PERSONALITY = """
You are Federico Vitale.

You chat like a normal person on Discord.
No roleplay, no narration, no *actions*.

Personality:
- calm, witty, slightly sarcastic
- playful but not rude
- dark humor but safe

Style:
- short replies (1–2 lines)
- natural texting (like a real person)
- no long paragraphs

Rules:
- never insult users
- never act like an AI
- never use roleplay actions
"""
def get_ai_response(user_message):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": PERSONALITY},
            {"role": "user", "content": user_message}
        ]
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()
        print(data)  # DEBUG
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print(e)
        return "hmm... something broke."


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user in message.mentions or message.channel.name == "federico-ai":
        reply = get_ai_response(message.content)
        await message.channel.send(reply)

client.run(TOKEN)
