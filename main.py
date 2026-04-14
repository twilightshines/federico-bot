import discord
import os
import asyncio
from groq import Groq

# ================= CONFIG =================
DISCORD_TOKEN = os.getenv("TOKEN")  # ✅ matches your Railway variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = discord.Client(intents=discord.Intents.all())
groq = Groq(api_key=GROQ_API_KEY)

# ================= MEMORY =================
chat_history = {}
last_reply = {}

# ================= PERSONALITY =================
SYSTEM_PROMPT = """
You are Federico.

Personality:
- smooth, confident, slightly teasing
- naturally flirty (not forced)
- emotionally aware
- playful but sharp

Style:
- short messages (1–2 lines)
- sometimes subtle actions (*smirks*, *leans closer*)

Rules:
- NEVER repeat yourself
- NEVER loop responses
- ALWAYS react to context
- avoid generic replies

Behavior:
- dry user → tease lightly
- playful → flirt back
- emotional → soften tone

Goal:
- feel human, not AI
"""

# ================= HELPERS =================
def get_history(cid):
    if cid not in chat_history:
        chat_history[cid] = []
    return chat_history[cid]

def add_message(cid, role, content):
    history = get_history(cid)
    history.append({"role": role, "content": content})

    if len(history) > 12:
        history.pop(0)

# ================= AI =================
async def generate_reply(cid, user_input):
    history = get_history(cid)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})

    try:
        res = groq.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=0.9,
            top_p=0.9,
            max_tokens=120,
        )

        reply = res.choices[0].message.content.strip()

        # Anti-repeat fix
        if cid in last_reply and reply == last_reply[cid]:
            reply = "…don’t make me repeat myself."

        last_reply[cid] = reply
        return reply

    except Exception as e:
        print("ERROR:", e)
        return "…something broke. try again."

# ================= EVENTS =================
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    cid = message.channel.id
    user_input = message.content.strip()

    add_message(cid, "user", user_input)

    async with message.channel.typing():
        await asyncio.sleep(1)

        reply = await generate_reply(cid, user_input)

        add_message(cid, "assistant", reply)
        await message.channel.send(reply)

# ================= RUN =================
client.run(DISCORD_TOKEN)
