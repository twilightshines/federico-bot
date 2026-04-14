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
    raise ValueError("TOKEN not found")

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

    # keep last 8 messages only
    memory[cid] = memory[cid][-8:]


# =======================
# 💬 AI GENERATION
# =======================
async def generate_reply(cid, user_input):
    messages = [
        {
            "role": "system",
            "content": (
                "You are Federico — a confident, chill, slightly sarcastic and flirty guy. "
                "Keep replies SHORT (1 sentence). Natural. Human. No repetition."
            )
        }
    ]

    messages += memory.get(cid, [])

    try:
        response = groq.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=messages,
            temperature=0.85,
            max_tokens=80
        )

        content = response.choices[0].message.content

        if not content or content.strip() == "":
            return "you just glitched… try again."

        return content.strip()

    except Exception as e:
        print("GROQ ERROR FULL:", repr(e))
        return f"ERROR: {str(e)}"
            

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

            add_message(cid, "assistant", reply)

            await message.channel.send(reply)

    except Exception as e:
        print("ON_MESSAGE ERROR:", repr(e))
        await message.channel.send("…something broke.")


# =======================
# ▶️ RUN
# =======================
client.run(TOKEN)
