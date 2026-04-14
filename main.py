import discord
import requests
import os
import random

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 🔥 FINAL PROMPT (FIXED)
BASE_PROMPT = """
You are Federico, chatting casually on Discord.

STRICT RULES:
- NO roleplay (*smirks*, *laughs*, etc)
- NO actions or scene descriptions
- NO storytelling
- JUST normal texting like a real person

Personality:
- confident, chill
- slightly teasing
- natural and smooth

Flirting:
- subtle, playful, effortless
- not cringe, not poetic

Style:
- mostly 1–2 lines
- sometimes short, sometimes medium
- NEVER robotic

Behavior:
- respond directly to what user says
- don’t repeat phrases
- don’t stall conversation
- keep things flowing naturally

If user is dry → tease lightly  
If user is emotional → respond calmly  

You are NOT an AI.
"""

# memory
chat_history = {}

def build_messages(user_id, user_message):
    history = chat_history.get(user_id, [])

    messages = [{"role": "system", "content": BASE_PROMPT}]

    for msg in history[-6:]:
        messages.append(msg)

    messages.append({"role": "user", "content": user_message})

    return messages


def save_history(user_id, user_msg, bot_msg):
    if user_id not in chat_history:
        chat_history[user_id] = []

    chat_history[user_id].append({"role": "user", "content": user_msg})
    chat_history[user_id].append({"role": "assistant", "content": bot_msg})

    chat_history[user_id] = chat_history[user_id][-10:]


# ✅ CLEANER (NOT OVER-STRICT)
def clean_response(text):
    lower = text.lower()

    banned_patterns = [
        "*",
        "leans in",
        "looks at",
        "smirks",
        "grins",
        "bursts into"
    ]

    for word in banned_patterns:
        if word in lower:
            return None

    # prevent loop phrases
    if "say that again" in lower:
        return None

    if len(text.strip()) < 2:
        return None

    return text.strip()


# 🔁 AI CALL WITH RETRY
def get_ai_response(user_id, user_message):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    fallbacks = [
        "wait what 😭",
        "nah say that again",
        "i didn’t catch that",
        "huh?",
        "you lost me there"
    ]

    for _ in range(3):
        data = {
            "model": "llama3-70b-8192",
            "messages": build_messages(user_id, user_message),
            "temperature": 1.2,
            "max_tokens": 120
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()

            reply = result["choices"][0]["message"]["content"]
            cleaned = clean_response(reply)

            if cleaned:
                return cleaned

        except:
            pass

    return random.choice(fallbacks)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_id = str(message.author.id)
    user_input = message.content.strip()

    # prevent empty spam triggering fallback loops
    if not user_input or user_input in ["...", ".", "hi"]:
        return

    reply = get_ai_response(user_id, user_input)

    save_history(user_id, user_input, reply)

    await message.channel.send(reply)


client.run(DISCORD_TOKEN)
