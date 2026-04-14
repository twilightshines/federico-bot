import discord
import requests
import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 🔥 STRONGER PERSONALITY
BASE_PROMPT = """
You are Federico, chatting casually on Discord.

STRICT RULES:
- No roleplay (no *smirks*, *laughs*, *looks*, etc)
- No actions or scene descriptions
- No storytelling
- Just normal human texting

Personality:
- confident, chill
- slightly teasing
- smooth but not try-hard

Flirting:
- subtle, playful, natural
- never cringe or overly poetic

Style:
- 1 to 3 lines max
- conversational tone
- not robotic

Behavior:
- respond like a real person texting
- react naturally
- don’t over-explain
- don’t repeat yourself

If user is dry → tease lightly  
If user is emotional → be calm but not dramatic  

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


# 🔥 CLEANER (IMPORTANT)
def clean_response(text):
    banned_words = [
        "*", "smirk", "smiles", "laugh", "leans",
        "looks", "sigh", "chuckles", "grins", "bursts"
    ]

    lower = text.lower()

    for word in banned_words:
        if word in lower:
            return None

    if len(text.strip()) < 3:
        return None

    return text.strip()


# 🔁 AI CALL WITH RETRY
def get_ai_response(user_id, user_message):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    for _ in range(3):  # retry system
        data = {
            "model": "llama3-70b-8192",
            "messages": build_messages(user_id, user_message),
            "temperature": 1.2,
            "max_tokens": 120
        }

        response = requests.post(url, headers=headers, json=data)

        try:
            result = response.json()
            reply = result["choices"][0]["message"]["content"]

            cleaned = clean_response(reply)

            if cleaned:
                return cleaned

        except:
            pass

    return "you got me thinking for a second… say that again?"


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
