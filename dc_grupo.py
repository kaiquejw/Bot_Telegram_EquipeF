import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.environ['TELEGRAM_API_ID'])
API_HASH = os.environ['TELEGRAM_API_HASH']
SESSION = os.environ['SESSION']
CHAT_ID = int(os.environ['CHAT'])

async def main():
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    await client.connect()
    ent = await client.get_entity(CHAT_ID)
    photo = getattr(ent, 'photo', None)
    dc = getattr(photo, 'dc_id', None)
    print(f"Grupo: {getattr(ent, 'title', '?')}")
    print(f"DC do grupo (via foto): {dc}")
    await client.disconnect()

asyncio.run(main())