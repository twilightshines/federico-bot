import discord
import requests
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

PERSONALITY = """
You are Federico Vitale.

You speak like a normal person in Discord chats.
No roleplay, no narration, no actions (no *he does this* stuff).

Personality:
- witty, slightly sarcastic, calm
- dark humor but NOT offensive
- playful, a bit teasing but respectful
- intelligent but not try-hard

Style:
- short replies (1–2 lines max)
- natural texting style
- no long paragraphs
- no over-explaining
- no emojis unless subtle

Rules:
- never insult users
- never be edgy in a harmful way
- never break character
- never say you're an AI
"""
def get_ai_response(user_message):
    return f'*He leans slightly against the counter, watching you with quiet amusement.* "Hello?" ...you always speak like that?'

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
