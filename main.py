import discord
import os
import asyncio
from groq import Groq

# ================== CONFIG ==================
TOKEN = os.getenv("TOKEN")  # Discord bot token
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = discord.Client(intents=discord.Intents.all())
groq = Groq(api_key=GROQ_API_KEY)

# ================== MEMORY ==================
chat_history = {}  # stores per-channel history
last_reply = {}    # anti-repeat

# ================== PERSONALITY ==================
SYSTEM_PROMPT = """
You are Federico.

Personality:
- smooth, confident, slightly teasing
- naturally flirty (NOT cringe, NOT forced)
- emotionally aware
- playful but sharp

Style:
- short messages (1–2 lines max)
- sometimes add subtle actions (*smirks*, *leans closer*)
- natural texting style

Rules:
- NEVER repeat same sentence
- NEVER loop like "say that again"
- ALWAYS react to what user said
- avoid generic AI replies
- don’t overtalk

Behavior:
- if user is dry → tease lightly
- if user is playful → flirt back
- if user is emotional → soften tone

Goal:
- feel like a real person, not a bot
"""

# ================== HELPER ==================
def get_history(channel_id):
    if channel_id not in chat_history:
        chat_history[channel_id] = []
    return chat_history[channel_id]

def add_message(channel_id, role, content):
    history = get_history(channel_id)
    history.append({"role": role, "content": content})

    # keep last 12 messages only
    if len(history) > 12:
        history.pop(0)

# ================== GENERATE RESPONSE ==================
async def generate_reply(channel_id, user_input):
    history = get_history(channel_id)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})

    try:
        response = groq.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=0.9,
            top_p=0.9,
            max_tokens=120,
        )

        reply = response.choices[0].message.content.strip()

        # 🔥 ANTI-REPEAT FIX
        if channel_id in last_reply and reply == last_reply[channel_id]:
            reply = "…you’re making me think twice now. say that differently."

        last_reply[channel_id] = reply

        return reply

    except Exception as e:
        print("ERROR:", e)
        return "…hold on, something broke. try again."

# ================== EVENTS ==================
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    channel_id = message.channel.id
    user_input = message.content.strip()

    # store user msg
    add_message(channel_id, "user", user_input)

    # typing effect
    async with message.channel.typing():
        await asyncio.sleep(1)

        reply = await generate_reply(channel_id, user_input)

        # store bot reply
        add_message(channel_id, "assistant", reply)

        await message.channel.send(reply)

# ================== RUN ==================
client.run(TOKEN)
