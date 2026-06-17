from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# Coloque seus dados aqui
API_ID = 31891041  # Seu API ID (número)
API_HASH = 'df20f87a534f0a73f437cb33985d1c95'

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("👇 COPIE O CÓDIGO ABAIXO E SALVE NOS SECRETS DO GITHUB 👇")
    print("")
    print(client.session.save())
    print("")
    print("👆 ESSE CÓDIGO É SUA CONTA. NÃO COMPARTILHE COM NINGUÉM!")