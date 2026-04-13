import discord
import requests
import os
import asyncio
import json

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

memory = {}

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# -------- ANALYZER -------- #

def analyze_message(message):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
Analyze this Discord message and return JSON only.

Message: "{message}"

Return format:
{{
  "intent": "...",
  "emotion": "...",
  "tone": "..."
}}

Keep it short.
"""

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 60
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()
        content = data["choices"][0]["message"]["content"]

        return json.loads(content)

    except:
        return {
            "intent": "chat",
            "emotion": "neutral",
            "tone": "casual"
        }


# -------- PERSONALITY -------- #

def build_prompt(user_msg, analysis):
    return f"""
You are Federico.

User message: {user_msg}

Context:
- intent: {analysis['intent']}
- emotion: {analysis['emotion']}
- tone: {analysis['tone']}

Reply like a real human.

Rules:
- short (1–2 lines)
- natural
- slightly flirty sometimes
- slightly sarcastic sometimes
- DO NOT sound like AI
- DO NOT explain things

Good examples:
"lol what"
"you serious?"
"nah that’s wild"

Now reply:
"""


# -------- AI RESPONSE -------- #

def get_ai_response(user_id, user_message):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    analysis = analyze_message(user_message)

    prompt = build_prompt(user_message, analysis)

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 60
    }

    try:
        res = requests.post(url, headers=headers, json=payload)

        if res.status_code != 200:
            return None

        data = res.json()
        reply = data["choices"][0]["message"]["content"]

        if not reply:
            return None

        return reply.strip()

    except:
        return None


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

    msg = message.content
    user_id = str(message.author.id)

    async with message.channel.typing():
        await asyncio.sleep(0.7)

    reply = get_ai_response(user_id, msg)

    if not reply:
        reply = "what"

    await message.channel.send(reply)


client.run(os.getenv("TOKEN"))
