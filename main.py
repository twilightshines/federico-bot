import discord
import requests
import os
import random

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 🔥 FINAL PROMPT (ANTI-LOOP + HUMAN STYLE)
BASE_PROMPT = """
You are Federico chatting on Discord.

DO NOT:
- use roleplay (*smirks*, *laughs*, etc)
- describe actions or scenes
- act like a character
- repeat phrases
- say things like "say that again" or "you got me thinking"

Talk like a real person texting.

Personality:
- calm, confident
- slightly teasing
- natural, not try-hard

Flirting:
- subtle and smooth
- never cringe or poetic

Style:
- 1–2 lines usually
- sometimes short, sometimes medium
- conversational

Behavior:
- respond directly to the message
- keep the convo moving
- don’t stall or loop
- don’t over-explain

If message is dry → tease a bit  
If emotional → respond simply, not dramatic  

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


# ✅ CLEANER (balanced, not over-aggressive)
def clean_response(text):
    lower = text.lower()

    banned = [
        "*", "smirk", "smiles", "laugh", "leans",
        "looks", "grins", "bursts into"
    ]

    loop_phrases = [
        "say that again",
        "you got me thinking",
        "you broke me"
    ]

    for word in banned + loop_phrases:
        if word in lower:
            return None

    if len(text.strip()) < 3:
        return None

    return text.strip()


# 🔁 AI CALL
def get_ai_response(user_id, user_message):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    fallbacks = [
        "wait what 😭",
        "nah say that again—properly this time",
        "you lost me there",
        "say something real",
        "huh?"
    ]

    for _ in range(3):
        data = {
            "model": "llama3-70b-8192",
            "messages": build_messages(user_id, user_message),
            "temperature": 0.9,
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

    # 🔥 HANDLE DRY INPUTS (NO LOOP)
    low_inputs = ["...", ".", "hi", "hii", "uhm", "what", "oye"]

    if user_input.lower() in low_inputs:
        await message.channel.send(random.choice([
            "that’s all you got?",
            "you always this quiet?",
            "say something real",
            "don’t go silent on me",
            "cmon, give me something better"
        ]))
        return

    reply = get_ai_response(user_id, user_input)

    save_history(user_id, user_input, reply)

    await message.channel.send(reply)


client.run(DISCORD_TOKEN)
