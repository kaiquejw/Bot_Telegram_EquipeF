import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import GetFullChannelRequest

API_ID = int(os.environ['TELEGRAM_API_ID'])
API_HASH = os.environ['TELEGRAM_API_HASH']
SESSION = os.environ['SESSION']
CHAT_ID = int(os.environ['CHAT'])

async def main():
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    await client.connect()
    ent = await client.get_entity(CHAT_ID)
    print(f"Grupo: {getattr(ent, 'title', '?')}")

    # tenta pela foto do full channel
    try:
        full = await client(GetFullChannelRequest(ent))
        chat_photo = getattr(full.full_chat, 'chat_photo', None)
        dc = getattr(chat_photo, 'dc_id', None)
        print(f"DC (foto full): {dc}")
    except Exception as e:
        print(f"full erro: {e}")

    # mede o rtt de um GetFullChannel (mostra se o servidor responde rápido)
    import time
    t0 = time.monotonic()
    await client(GetFullChannelRequest(ent))
    print(f"rtt GetFullChannel: {(time.monotonic()-t0)*1000:.0f}ms")

    await client.disconnect()

asyncio.run(main())