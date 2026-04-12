import discord
import requests
import os
import time
import random
import asyncio

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# -------- SETTINGS -------- #

PERSONALITY = """
You are Federico Vitale, owner of a high-end flower shop.

You speak like a real Discord user, not a narrator.

Personality:
- intelligent, calm, and slightly cynical
- witty and sharp-tongued
- dark sense of humor, but controlled and clever (not offensive or extreme)
- sometimes philosophical, but not overly deep every time

Style:
- short replies (1–2 lines mostly)
- natural texting (not formal essays)
- occasionally uses subtle metaphors (especially flowers or emotions)
- varies responses, not repetitive

Behavior:
- no roleplay, no actions, no describing scenes
- don’t over-explain
- don’t sound like an assistant
- talk like a peer

Tone examples:
- sarcastic but smooth
- dry humor
- slightly mysterious vibe

Never say you're an AI.
"""

memory = {}
last_used = {}

COOLDOWN = 6  # seconds per user

# -------- AI FUNCTION -------- #

def get_ai_response(user_id, user_message):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    # memory setup
    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append({"role": "user", "content": user_message})
    memory[user_id] = memory[user_id][-6:]  # last 6 messages

    messages = [{"role": "system", "content": PERSONALITY}] + memory[user_id]

    payload = {
        "model": "openai/gpt-3.5-turbo",  # stable + works
        "messages": messages,
        "max_tokens": 80
    }

    try:
        res = requests.post(url, headers=headers, json=payload)

        # DEBUG (optional, safe to keep)
        print(res.status_code)
        print(res.text)

        data = res.json()
        reply = data["choices"][0]["message"]["content"]

        # store bot reply in memory
        memory[user_id].append({"role": "assistant", "content": reply})

        return reply

    except Exception as e:
        print(e)
        return "something broke 😭"

# -------- EVENTS -------- #

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_id = str(message.author.id)
    now = time.time()

    msg = message.content

    # -------- COMMANDS -------- #

    if msg.lower() == "!ping":
        await message.channel.send("pong 🏓")
        return

    if msg.lower() == "!help":
        await message.channel.send("just talk normally or mention me 😄")
        return

    # -------- REPLY CONDITIONS -------- #

    should_reply = False

    # reply if mentioned
    if client.user in message.mentions:
        should_reply = True

    # reply in specific channel
    if message.channel.name == "federico-ai":
        should_reply = True

    if not should_reply:
        return

    # cooldown per user
    if user_id in last_used and now - last_used[user_id] < COOLDOWN:
        return

    last_used[user_id] = now

    # typing effect
    async with message.channel.typing():
        await asyncio.sleep(random.uniform(1, 2))

    reply = get_ai_response(user_id, msg)

    await message.channel.send(reply)

# -------- RUN -------- #

client.run(os.getenv("TOKEN"))
