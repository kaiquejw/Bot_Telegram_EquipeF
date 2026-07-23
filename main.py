import asyncio
import os
import time
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from telethon import TelegramClient, events, utils
from telethon.sessions import StringSession
from telethon.tl.functions.messages import SendMessageRequest
from telethon.errors import (
    ChatWriteForbiddenError,
    FloodWaitError,
    SlowModeWaitError,
)

# --- CONFIGURAÇÕES GERAIS ---
API_ID = int(os.environ.get('TELEGRAM_API_ID'))
API_HASH = os.environ.get('TELEGRAM_API_HASH')

TZ = ZoneInfo("America/Sao_Paulo")  


HORA_ALVO = 16
MINUTO_ALVO = 10
SEGUNDO_ALVO = 0

ANTECIPACAO_S = 0.0
LAUNCH_INTERVAL = 0.035
DESISTIR_APOS_S = 120



CONTAS = [

        #  20h30 Senha Grupo Normal -1003927816412
    {
        "nome": "Adrielli",
        "secret_name": "SESSION_ADRIELLI",
        "chat_id": -5176706740,
        "msg": "Adrielli x Carlos r1"
    },

        #  20h00 Grupo senha normal -1003601357589
    {
        "nome": "Ivete",
        "secret_name": "SESSION_IVETE",
        "chat_id": -5124583946,
        "msg": "Nega /erik R 5"
    },

        #  20h20 Senha normal -1003875645355
    {
        "nome": "Monica",
        "secret_name": "SESSION_MONICA",
        "chat_id": -4801139096,
        "msg": "Mônica x jaçanã G11"
    },

        #  20h30 Grupo da senha PREFERENCIAL Flórida Paulista -1002459968766
    {
        "nome": "Miriam",
        "secret_name": "SESSION_MIRIAM",
        "chat_id": -4992766314,
        "msg": "Miria/adriano raio 3"
    },

        #  20h00 Senha Grupo Normal -1003927816412
    {
        "nome": "Viviane",
        "secret_name": "SESSION_VIVIANE",
        "chat_id": -5107863814,
        "msg": "Viviane/coelho raio 3"
    },

        #  20h30 Senha Grupo Normal -1003927816412
    {
        "nome": "Juliana",
        "secret_name": "SESSION_JULIANA",
        "chat_id": -5108358245,
        "msg": "Juliana/Jota/R3"
    },

        #  20h00 Grupo da senha DOBRA Flórida Paulista -1002443109385
    {
        "nome": "JulianaGALAO",
        "secret_name": "SESSION_JULIANAGALAO",
        "chat_id": -5330759829,
        "msg": "Juliana x galão R5"
    },

        #  21h00 Senha Grupo Bate Volta -1003993735474
    #{
    #    "nome": "Kaique",
    #    "secret_name": "SESSION_KAIQUE",
    #    "chat_id": -5186073583,
    #    "msg": "teste "
    #},

        #  19h00 Senha Normal (Dobra) 19:00 HS -1004417252531
    {
        "nome": "Rafa",
        "secret_name": "SESSION_RAFA",
        "chat_id": -5230687258,
        "msg": "Rafaela X da morte r3"
    },

        #  19h00 Senha Normal (Dobra) 19:00 HS  | -1004417252531
    {
        "nome": "Isabella",
        "secret_name": "SESSION_ISABELLA",
        "chat_id": -5174570129,
        "msg": "Isa/ NK R3"
    },

]


def _refere_canal(update, canal_id):
    if getattr(update, 'channel_id', None) == canal_id:
        return True
    if getattr(update, 'chat_id', None) == canal_id:
        return True
    peer = getattr(update, 'peer', None)
    if peer is not None:
        if getattr(peer, 'chat_id', None) == canal_id:
            return True
        if getattr(peer, 'channel_id', None) == canal_id:
            return True
    msg = getattr(update, 'message', None)
    pid = getattr(msg, 'peer_id', None) if msg is not None else None
    if pid is not None:
        if getattr(pid, 'chat_id', None) == canal_id:
            return True
        if getattr(pid, 'channel_id', None) == canal_id:
            return True
    return False


def _eh_fechado(e):
    s = str(e).lower()
    return ('plain' in s) or ('forbidden' in s and 'send' in s) \
        or ('write' in s and 'forbidden' in s)


async def disparar(client, peer, msg, nome, vencido, origem, contador, random_id):
    if vencido.is_set():
        return
    contador['n'] += 1
    idx = contador['n']
    t0 = time.monotonic()
    try:
        await client(SendMessageRequest(peer=peer, message=msg, random_id=random_id))
        if not vencido.is_set():
            vencido.set()
            rtt = (time.monotonic() - t0) * 1000
            agora = datetime.now(TZ).strftime('%H:%M:%S.%f')
            print(f"🏆 {nome} ENVIOU via {origem}! tiro #{idx} "
                  f"({agora}) rtt~{rtt:.0f}ms")
    except ChatWriteForbiddenError:
        pass
    except FloodWaitError as e:
        print(f"🛑 {nome} FLOOD {e.seconds}s -> aumente o LAUNCH_INTERVAL")
        await asyncio.sleep(e.seconds)
    except SlowModeWaitError as e:
        if not vencido.is_set():
            vencido.set()
        print(f"🐌 {nome} slowmode {e.seconds}s (mensagem já enviada)")
    except Exception as e:
        if _eh_fechado(e):
            pass
        else:
            print(f"⚠️ {nome} erro: {e}")
            await asyncio.sleep(0.3)


# --- FASE 1: só conecta e valida ---
async def conectar(conta):
    session = os.environ.get(conta['secret_name'])
    if not session:
        print(f"❌ {conta['nome']}: SESSION não encontrada no .env")
        return None

    client = TelegramClient(StringSession(session), API_ID, API_HASH)
    try:
        await client.connect()
        await client.get_dialogs()
        if not await client.is_user_authorized():
            print(f"❌ {conta['nome']}: login falhou (não autorizado)")
            await client.disconnect()
            return None

        peer = await client.get_input_entity(conta['chat_id'])
        canal_id, _ = utils.resolve_id(conta['chat_id'])
        random_id = random.randrange(-(2**63), 2**63 - 1)
        print(f"✅ {conta['nome']} pronto | DC {client.session.dc_id} | canal {canal_id}")
        return (client, peer, canal_id, random_id, conta)

    except Exception as e:
        print(f"❌ {conta['nome']}: erro ao conectar — {e}")
        if client.is_connected():
            await client.disconnect()
        return None


# --- FASE 2: dispara com client já conectado ---
async def sniper(dados, alvo):
    client, peer, canal_id, random_id, conta = dados
    nome = conta['nome']
    msg = conta['msg']
    on_update = None
    try:
        vencido = asyncio.Event()
        janela = {'on': False}
        contador = {'n': 0}
        pendentes = []

        def fire(origem):
            pendentes.append(asyncio.create_task(
                disparar(client, peer, msg, nome, vencido, origem, contador, random_id)
            ))

        async def on_update(update):
            if vencido.is_set() or not janela['on']:
                return
            try:
                if _refere_canal(update, canal_id):
                    fire('LISTENER')
            except Exception:
                pass
        # client.add_event_handler(on_update, events.Raw)  # descomente p/ listener

        while (alvo - datetime.now(TZ)).total_seconds() > 15:
            await asyncio.sleep(1)
        try:
            await client.get_me()
        except Exception:
            pass

        inicio = alvo - timedelta(seconds=ANTECIPACAO_S)
        deadline = alvo + timedelta(seconds=DESISTIR_APOS_S)
        while datetime.now(TZ) < inicio:
            await asyncio.sleep(0.01)

        janela['on'] = True
        print(f"⚔️ {nome} ATIVO (só pipeline)")
        while not vencido.is_set() and datetime.now(TZ) < deadline:
            if not client.is_connected():
                print(f"🔌 {nome} reconectando...")
                try:
                    await client.connect()
                except Exception:
                    await asyncio.sleep(1)
                    continue
            fire('PIPELINE')
            await asyncio.sleep(LAUNCH_INTERVAL)

        await asyncio.gather(*pendentes, return_exceptions=True)
        if not vencido.is_set():
            print(f"❌ {nome} não conseguiu (tempo esgotado).")

    except Exception as e:
        print(f"❌ Erro fatal {nome}: {e}")
    finally:
        if on_update is not None:
            try:
                client.remove_event_handler(on_update, events.Raw)
            except Exception:
                pass
        if client.is_connected():
            await client.disconnect()


async def main():
    agora = datetime.now(TZ)
    alvo = agora.replace(hour=HORA_ALVO, minute=MINUTO_ALVO,
                         second=SEGUNDO_ALVO, microsecond=0)
    if alvo < agora:
        alvo += timedelta(days=1)

    print(f"🎯 Alvo: {alvo.strftime('%d/%m %H:%M:%S')} BRT | "
          f"agora {agora.strftime('%H:%M:%S')} | "
          f"faltam {(alvo - agora).total_seconds():.0f}s")
    print(f"⚙️  launch_interval={LAUNCH_INTERVAL}s | contas={len(CONTAS)}")
    print(f"\n🔌 FASE 1 — Conectando contas...\n")

    resultados = await asyncio.gather(*(conectar(c) for c in CONTAS))

    prontas = [r for r in resultados if r is not None]
    falhas  = [CONTAS[i]['nome'] for i, r in enumerate(resultados) if r is None]

    print(f"\n{'='*45}")
    print(f"✅ Prontas ({len(prontas)}): {', '.join(d[4]['nome'] for d in prontas) or '—'}")
    print(f"❌ Falharam ({len(falhas)}): {', '.join(falhas) or '—'}")
    if falhas:
        print(f"\n⚠️  {len(falhas)} conta(s) falharam!")
        print(f"   Ctrl+C pra cancelar, corrigir e reiniciar.")
    print(f"{'='*45}\n")

    if not prontas:
        print("❌ Nenhuma conta conectou. Encerrando.")
        return

    if falhas:
        print(f"🛑 ENCERRANDO — corrija as contas acima e reinicie o bot.")
        return

    print(f"🚀 FASE 2 — Disparando com {len(prontas)} conta(s)...\n")
    await asyncio.gather(*(sniper(d, alvo) for d in prontas))


if __name__ == '__main__':
    asyncio.run(main())