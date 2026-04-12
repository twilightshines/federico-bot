import discord
import requests
import os
import time

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# -------- SETTINGS -------- #

PERSONALITY = """
You are Federico Vitale.

Talk like a normal Discord user.
No roleplay, no narration, no actions.

Be:
- casual
- slightly witty
- short replies (1–2 lines)

Never say you're an AI.
"""

# memory per user
memory = {}

# cooldown per user
last_used = {}

# -------- AI FUNCTION -------- #

def get_ai_response(user_id, user_message):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    # store memory
    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append(user_message)
    memory[user_id] = memory[user_id][-5:]  # last 5 messages

    messages = [{"role": "system", "content": PERSONALITY}]

    for msg in memory[user_id]:
        messages.append({"role": "user", "content": msg})

    payload = {
        "model": "mistralai/mistral-7b-instruct",  # cheap model
        "messages": messages,
        "max_tokens": 80  # saves money
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print(e)
        return "bruh something broke"

# -------- EVENTS -------- #

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_id = str(message.author.id)
    now = time.time()

    # cooldown (5 sec per user)
    if user_id in last_used and now - last_used[user_id] < 5:
        return

    last_used[user_id] = now

    msg = message.content.lower()

    # -------- COMMANDS -------- #

    if msg == "!ping":
        await message.channel.send("pong 🏓")
        return

    if msg == "!help":
        await message.channel.send("commands: !ping, !help, !ai <message>")
        return

    if msg.startswith("!ai "):
        prompt = message.content[4:]

        reply = get_ai_response(user_id, prompt)
        await message.channel.send(reply)
        return

# -------- RUN -------- #

client.run(os.getenv("TOKEN"))
