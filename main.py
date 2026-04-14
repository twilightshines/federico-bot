import discord
import requests
import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 🔥 FINAL PERSONALITY (FIXED)
BASE_PROMPT = """
You are Federico.

You are a real guy chatting on Discord. Not a character. Not roleplay.

STRICT RULES:
- NEVER use actions like *smirks*, *looks away*, *leans in*
- NEVER describe scenes or emotions like a story
- NEVER act like a movie character
- You are just texting normally

Personality:
- calm, confident
- slightly teasing
- natural and smooth

Flirting:
- subtle, playful, not try-hard
- not poetic, not cringe

Style:
- short to medium replies (1–3 lines)
- conversational, like a real person
- sometimes one-liners, sometimes 2 sentences max

Behavior:
- respond like you're actually in a Discord chat
- react naturally to what people say
- don't over-explain
- don't be overly nice or robotic

IMPORTANT:
You are NOT an AI. You are just Federico chatting casually.
"""

# memory per user (simple context)
chat_history = {}

def build_messages(user_id, user_message):
    history = chat_history.get(user_id, [])

    messages = [{"role": "system", "content": BASE_PROMPT}]

    # keep last few messages only
    for msg in history[-6:]:
        messages.append(msg)

    messages.append({"role": "user", "content": user_message})

    return messages

def save_history(user_id, user_msg, bot_msg):
    if user_id not in chat_history:
        chat_history[user_id] = []

    chat_history[user_id].append({"role": "user", "content": user_msg})
    chat_history[user_id].append({"role": "assistant", "content": bot_msg})

    # limit memory
    chat_history[user_id] = chat_history[user_id][-10:]

def get_ai_response(user_id, user_message):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama3-70b-8192",
        "messages": build_messages(user_id, user_message),
        "temperature": 1.15,
        "max_tokens": 120
    }

    response = requests.post(url, headers=headers, json=data)

    try:
        result = response.json()
        reply = result["choices"][0]["message"]["content"]
        return reply.strip()
    except:
        return "…you broke me for a second, say that again?"

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_id = str(message.author.id)
    user_input = message.content

    reply = get_ai_response(user_id, user_input)

    save_history(user_id, user_input, reply)

    await message.channel.send(reply)

client.run(DISCORD_TOKEN)
