@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # 🔥 ignore empty messages
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
                reply = "…you just said something weird, say that again."

            add_message(cid, "assistant", reply)

            await message.channel.send(reply)

    except Exception as e:
        print("ON_MESSAGE ERROR:", e)

        await message.channel.send("…something broke, try again.")
