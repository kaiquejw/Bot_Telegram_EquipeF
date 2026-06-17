import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession

# Lê tudo de variável de ambiente — NADA de segredo escrito no arquivo.
# Uso:  SESSION="sua_session" python pegar_id.py
API_ID = int(os.environ['TELEGRAM_API_ID'])
API_HASH = os.environ['TELEGRAM_API_HASH']
SESSION = os.environ['SESSION']


async def main():
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    await client.connect()

    me = await client.get_me()
    print(f"\n✅ Conta: {me.first_name} {me.last_name or ''}".strip())
    print(f"📱 +{me.phone}  |  DC {client.session.dc_id}")
    print("-" * 55)
    print(f"{'GRUPO':<32} | ID")
    print("-" * 55)
    async for d in client.iter_dialogs(limit=20):
        print(f"{d.name:<32} | {d.id}")
    print()

    await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())