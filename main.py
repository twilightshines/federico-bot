import discord
import requests
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

PERSONALITY = """
You are Federico Vitale, calm, witty, slightly mysterious.
You use playful teasing, smooth charm, and light dark humor.
You never insult or offend.
Keep replies short and natural like Discord chat.
Never say you are an AI.
"""

def get_ai_response(user_message):
    url = "https://api.ollama.ai/v1/chat"
    
    payload = {
        "model": "llama3",
        "messages": [
            {"role": "system", "content": PERSONALITY},
            {"role": "user", "content": user_message}
        ]
    }

    try:
        res = requests.post(url, json=payload)
        return res.json()["message"]["content"]
    except:
        return "…something seems off."

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
