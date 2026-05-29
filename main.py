import asyncio
import os
import datetime
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import ChatWriteForbiddenError, FloodWaitError

# --- CONFIGURAÇÕES GERAIS ---
API_ID = int(os.environ.get('TELEGRAM_API_ID'))
API_HASH = os.environ.get('TELEGRAM_API_HASH')

# --- LISTA DE ATIRADORES (EXÉRCITO) ---
# ⚠️ MUDANÇA 1: JAQUELINE EM PRIMEIRO (PRIORIDADE MÁXIMA) ⚠️
CONTAS = [

        # 20h30 SENHA NORMAL 🚨 -1002704903786   
    {
        "nome": "Juliana", 
        "secret_name": "SESSION_JULIANA",
        "chat_id": -1002704903786,
        "msg": "Juliana/Jota/R3"
    },

        # 21h20 Grupo bate ( domingo ) -1003711333914
    #{
    #    "nome": "Giovana", 
    #    "secret_name": "SESSION_GIOVANA",
    #    "chat_id": -1003711333914,
    #    "msg": "Giovana - Branco/Raio 6"
    #},

]

# ⚠️ AJUSTE AQUI PARA O DIA DA SENHA ⚠️
HORA_ALVO = 20
MINUTO_ALVO = 30

async def sniper_individual(conta, alvo):
    """Função otimizada para VELOCIDADE MÁXIMA (Modo Turbo)"""
    
    session_str = os.environ.get(conta['secret_name'])
    if not session_str:
        print(f"⚠️ Pulei {conta['nome']}: Segredo não encontrado.")
        return

    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    chat_alvo_especifico = conta.get('chat_id')

    try:
        await client.connect()
        # Força atualização dos diálogos para garantir que encontra o ID -1002704903786
        await client.get_dialogs()
        
        if not await client.is_user_authorized():
            print(f"❌ {conta['nome']}: Falha no Login.")
            return

        print(f"✅ {conta['nome']} pronto. Alvo: {chat_alvo_especifico}")

        # --- FASE 1: ESPERA (Modo Econômico) ---
        # Fica dormindo até faltarem 30 segundos para não gastar CPU à toa
        while (alvo - datetime.datetime.now()).total_seconds() > 30:
            await asyncio.sleep(1)

        print(f"⚠️ {conta['nome']} entrou em ALERTA MÁXIMO (Faltam < 30s)")

        # --- FASE 2: AQUECIMENTO E DISPARO ---
        enviado = False
        tentativa = 0
        
        # Loop até enviar ou passar do tempo
        while not enviado:
            agora = datetime.datetime.now()
            diferenca = (alvo - agora).total_seconds()

            # Se já passou 2 minutos do horário, desiste.
            if diferenca < -120: 
                print(f"❌ {conta['nome']} Desistindo (Tempo esgotado).")
                break

            # ⚠️ MUDANÇA 2: ESPERA INTELIGENTE ⚠️
            # Se faltar mais de 2 segundos, dorme um pouco.
            # Isso evita que o robô tome FloodWait por tentar cedo demais.
            if diferenca > 0.0:
                await asyncio.sleep(0.01)
                continue

            # --- ZONA DE GUERRA (Faltam < 2 segundos ou já passou) ---
            try:
                # Tenta enviar!
                await client.send_message(chat_alvo_especifico, conta['msg'])
                
                # Se passou daqui, ENVIOU!
                enviado = True
                print(f"🏆 {conta['nome']} -> ENVIOU! TENTATIVA {tentativa} ({datetime.datetime.now().strftime('%H:%M:%S.%f')})")
                
            except ChatWriteForbiddenError:
                # ⚠️ MUDANÇA 3: REAÇÃO RÁPIDA ⚠️
                # O GRUPO AINDA ESTÁ FECHADO.
                tentativa += 1
                # Dorme APENAS 0.05s (50ms). Antes era 0.2s (200ms).
                # Isso faz ele tentar 4x mais rápido.
                await asyncio.sleep(0.010) 
                
            except FloodWaitError as e:
                print(f"🛑 {conta['nome']} FloodWait: {e.seconds}s (Esperando...)")
                await asyncio.sleep(e.seconds)
                
            except Exception as e:
                print(f"⚠️ Erro: {e}")
                await asyncio.sleep(0.1)

    except Exception as e:
        print(f"❌ Erro fatal {conta['nome']}: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()

async def main():
    agora = datetime.datetime.now()
    alvo = agora.replace(hour=HORA_ALVO, minute=MINUTO_ALVO, second=1, microsecond=0) 
    
    print(f"🔥 INICIANDO MODO TURBO ({len(CONTAS)} contas)")
    print(f"🎯 Alvo: {alvo.strftime('%H:%M:%S')}")

    # Espera inicial para não gastar GitHub Actions à toa
    while (alvo - datetime.datetime.now()).total_seconds() > 40:
        restante = int((alvo - datetime.datetime.now()).total_seconds())
        if restante % 30 == 0:
            print(f"💤 Aguardando... Falta {restante}s")
        await asyncio.sleep(5)

    print("⚔️ PREPARANDO ATAQUE... (Faltam < 40s)")
    
    tarefas = []
    for conta in CONTAS:
        tarefas.append(sniper_individual(conta, alvo))
    
    await asyncio.gather(*tarefas)

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())