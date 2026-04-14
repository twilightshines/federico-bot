import discord
import os
import asyncio
from groq import Groq

# =======================
# CONFIG
# =======================

TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = discord.Client(intents=discord.Intents.all())
groq_client = Groq(api_key=GROQ_API_KEY)

memory = {}

# =======================
# MEMORY (CLEANED)
# =======================

def add_message(cid, role, content):
    if cid not in memory:
        memory[cid] = []

    # ❌ ignore bad/garbage replies
    if content.lower() in ["huh?", "what?", "say that again?"]:
        return

    memory[cid].append({"role": role, "content": content})

    # keep last 10 only
    if len(memory[cid]) > 10:
        memory[cid] = memory[cid][-10:]


def get_messages(cid):
    return memory.get(cid, [])

# =======================
# AI RESPONSE
# =======================

async def generate_reply(cid, user_input):
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Federico, a real human chatting on Discord.\n"
                    "Reply naturally like a normal person.\n"
                    "Keep replies short (1 sentence).\n"
                    "Be slightly sarcastic and casual.\n\n"
                    "Rules:\n"
                    "- If user says 'hi' → reply like 'hey' or 'yo'\n"
                    "- If user asks 'how are you' → reply like 'im good, you?'\n"
                    "- NEVER reply with just 'huh?' or 'what?'\n"
                    "- If confused, ask a proper question\n"
                    "- Do NOT act like an AI\n"
                )
            }
        ] + get_messages(cid)

        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            temperature=0.8,
            max_tokens=80
        )

        content = response.choices[0].message.content.strip()

        return content if content else None

    except Exception as e:
        print("GROQ ERROR:", e)
        return None

# =======================
# EVENTS
# =======================

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # 🚫 ignore bots (prevents binod loop)
    if message.author.bot:
        return

    if not message.content:
        return

    cid = message.channel.id
    user_input = message.content.strip().lower()

    print(f"[MSG] {message.author}: {user_input}")

    # =======================
    # SMART DIRECT HANDLING
    # =======================

    if user_input in ["hi", "hello", "hey"]:
        await message.channel.send("hey")
        return

    if "how r u" in user_input or "how are you" in user_input:
        await message.channel.send("im good, you?")
        return

    if len(user_input) <= 2:
        await message.channel.send("say something real")
        return

    # =======================
    # NORMAL FLOW
    # =======================

    add_message(cid, "user", user_input)

    try:
        async with message.channel.typing():
            await asyncio.sleep(0.4)

            reply = await generate_reply(cid, user_input)

            # ✅ SINGLE CLEAN FALLBACK
            if not reply:
                reply = "say that again?"

            add_message(cid, "assistant", reply)

            await message.channel.send(reply)

    except Exception as e:
        print("ON_MESSAGE ERROR:", e)
        await message.channel.send("…something broke.")

# =======================
# RUN
# =======================

client.run(TOKEN)
