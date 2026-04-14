import discord
import os
import asyncio
import random
from groq import Groq

# =======================
# CONFIG
# =======================

TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = discord.Client(intents=discord.Intents.all())
groq_client = Groq(api_key=GROQ_API_KEY)

# memory per channel
memory = {}

# =======================
# MEMORY
# =======================

def add_message(cid, role, content):
    if cid not in memory:
        memory[cid] = []

    memory[cid].append({"role": role, "content": content})

    # keep last 15 messages
    if len(memory[cid]) > 15:
        memory[cid] = memory[cid][-15:]


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
                    "You are Federico, a human Discord user.\n"
                    "Reply short, natural, slightly sarcastic, a bit playful.\n"
                    "Never say 'huh?' repeatedly.\n"
                    "If user greets, greet back normally.\n"
                    "If confused, ask something meaningful.\n"
                    "Do NOT act like AI.\n"
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
    # ignore self
    if message.author == client.user:
        return

    # ignore bots (prevents loop)
    if message.author.bot:
        return

    if not message.content:
        return

    cid = message.channel.id
    user_input = message.content.strip().lower()

    print(f"[MSG] {message.author}: {user_input}")

    # =======================
    # SIMPLE HANDLING (IMPORTANT)
    # =======================

    if user_input in ["hi", "hello", "hey"]:
        await message.channel.send(random.choice(["hey", "yo", "what's up"]))
        return

    if user_input in ["wyd", "what are you doing"]:
        await message.channel.send("nothing much, you?")
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

            # 🔥 BETTER FALLBACK
            if not reply:
                reply = random.choice([
                    "say that again?",
                    "what do you mean?",
                    "you lost me there",
                    "hmm?"
                ])

            add_message(cid, "assistant", reply)

            await message.channel.send(reply)

    except Exception as e:
        print("ON_MESSAGE ERROR:", e)
        await message.channel.send("…something broke.")


# =======================
# RUN
# =======================

client.run(TOKEN)
