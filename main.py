import discord
import requests
import os
import asyncio
import json

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MEMORY_FILE = "memory.json"

# -------- LOAD MEMORY -------- #

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

user_profiles = load_memory()

# -------- ANALYZER -------- #

def analyze_message(message):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
Analyze message and return JSON:

Message: "{message}"

Return:
{{"intent":"","emotion":"","tone":""}}
"""

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 50
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()
        return json.loads(data["choices"][0]["message"]["content"])
    except:
        return {"intent":"chat","emotion":"neutral","tone":"casual"}

# -------- USER PROFILE -------- #

def get_user_profile(user_id):
    if user_id not in user_profiles:
        user_profiles[user_id] = {
            "messages": 0,
            "vibe": "neutral"
        }

    profile = user_profiles[user_id]
    profile["messages"] += 1

    if profile["messages"] > 20:
        profile["vibe"] = "playful"
    elif profile["messages"] > 5:
        profile["vibe"] = "friendly"

    save_memory(user_profiles)

    return profile

# -------- PROMPT -------- #

def build_prompt(msg, analysis, profile):
    return f"""
You are Federico.

User vibe: {profile['vibe']}

Message: {msg}

Context:
intent: {analysis['intent']}
emotion: {analysis['emotion']}

Rules:
- short replies
- natural texting
- adapt to vibe
- no AI tone

Reply:
"""

# -------- RESPONSE -------- #

def get_ai_response(user_id, msg):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    analysis = analyze_message(msg)
    profile = get_user_profile(user_id)

    prompt = build_prompt(msg, analysis, profile)

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.85,
        "max_tokens": 60
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()
        return data["choices"][0]["message"]["content"].strip()
    except:
        return "what"

# -------- EVENTS -------- #

@client.event
async def on_ready():
    print("Ready")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.name != "federico-ai":
        return

    user_id = str(message.author.id)

    async with message.channel.typing():
        await asyncio.sleep(0.6)

    reply = get_ai_response(user_id, message.content)

    await message.channel.send(reply)

client.run(os.getenv("TOKEN"))
