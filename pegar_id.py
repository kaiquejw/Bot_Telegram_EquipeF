import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# --- PREENCHA SEUS DADOS AQUI ---
API_ID = 31891041  # Seu API ID
API_HASH = 'df20f87a534f0a73f437cb33985d1c95'
SESSION = '1AZWarzcBuzXz3NGIDmmszf_r_6tQP_qIgCdZqJ6Gxfr3oQpUgHSKLepGj5SKj7Pa7IQ_nX67F0BPlZUqvybyQLlG4GEhK1WctL_st8dGvJUyIGg3dToPj64v8b8sKV6_V7Q80ACBaIUbeZAGdow3916ZzkC0M5ZAcpLgdAXn0nuIH8YvOSOCQQD278aABb3uftuVygplOJiiBL8EMGB42ak7R3uhM8Zlny4H34x1-yTUDnXOBnjWt4oGKC_S8Mh0aBwAJVQZZkCwj8cApazUPAUxzf2BOluo-lveK8Uu6BIfsjnwy0T3vF2wge4rg_nK3nuxpir6WBzlAzQrP8bg17OkVhvfK6I='

async def main():
    print("Conectando...")
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    await client.connect()
    

# --- A PARTE QUE DESCOBRE O DONO DA SESSÃO ---
    me = await client.get_me()
    print("\n✅ SESSÃO AUTENTICADA COM SUCESSO!")
    print(f"👤 Nome da conta: {me.first_name} {me.last_name or ''}".strip())
    print(f"📱 Número: +{me.phone}")
    print("-" * 50)
    # ---------------------------------------------

    print("\n👇 AQUI ESTÃO SEUS ÚLTIMOS GRUPOS/CONVERSAS 👇\n")
    print(f"{'NOME DO GRUPO':<30} | {'ID PARA O GITHUB'}")
    print("-" * 50)
    
    # Pega as últimas 15 conversas
    async for dialog in client.iter_dialogs(limit=15):
        print(f"{dialog.name:<30} | {dialog.id}")
        
    print("\n👆 Copie o ID (número negativo) do grupo 'Teste' e coloque no GitHub.\n")

if __name__ == '__main__':
    asyncio.run(main())