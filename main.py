import discord
import os
import asyncio
from groq import Groq

# =======================
# 🔑 ENV VARIABLES
# =======================
TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN:
    raise ValueError("TOKEN not found in environment variables")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found")

# =======================
# 🤖 GROQ CLIENT
# =======================
groq = Groq(api_key=GROQ_API_KEY)

# =======================
# 🧠 MEMORY
# =======================
memory = {}

def add_message(cid, role, content):
    if cid not in memory:
        memory[cid] = []

    memory[cid].append({"role": role, "content": content})

    # limit memory
    memory[cid] = memory[cid][-10:]


# =======================
# 💬 AI REPLY
# =======================
async def generate_reply(cid, user_input):
    messages = [
        {
            "role": "system",
            "content": (
                "You are Federico — a chill, slightly sarcastic, flirty guy. "
                "Keep replies short, human-like, and natural. "
                "Avoid repeating phrases. No long paragraphs."
            )
        }
    ]

    messages += memory.get(cid, [])

    try:
        response = groq.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            temperature=0.8,
            max_tokens=80
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("GROQ ERROR:", e)
        return None


# =======================
# ⚙️ DISCORD SETUP
# =======================
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


# =======================
# 🚀 READY EVENT
# =======================
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


# =======================
# 💬 MESSAGE EVENT
# =======================
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not message.content:
        return

    cid = message.channel.id
    user_input = message.content.strip()

    print(f"[MSG] {message.author}: {user_input}")

    add_message(cid, "user", user_input)

    try:
        async with message.channel.typing():
            await asyncio.sleep(0.5)

            reply = await generate_reply(cid, user_input)

            if not reply:
                reply = "…say that again."

            add_message(cid, "assistant", reply)

            await message.channel.send(reply)

    except Exception as e:
        print("ON_MESSAGE ERROR:", e)
        await message.channel.send("…something broke.")


# =======================
# ▶️ RUN
# =======================
client.run(TOKEN)
