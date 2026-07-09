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

TZ = ZoneInfo("America/Sao_Paulo")  # crava horário de Brasília

# ⚠️ AJUSTE PARA O DIA DA SENHA ⚠️
HORA_ALVO = 20
MINUTO_ALVO = 36
SEGUNDO_ALVO = 0

# Começa a martelar a porta um pouco antes do horário.
ANTECIPACAO_S = 0.0

# Espaçamento entre disparos sobrepostos do PIPELINE.
# 0.04 (~25/s). Se aparecer "🛑 FLOOD", aumente.
LAUNCH_INTERVAL = 0.035

DESISTIR_APOS_S = 120

CONTAS = [
    
        #  20h45 Senha Grupo Preferencial -1003552682244
    {
        "nome": "Jake",
        "secret_name": "SESSION_JAKE",
        "chat_id": -5291105956,
        "msg": "Jakeline x Daniel raio 3"
    },

]


def _refere_canal(update, canal_id):
    """True se o update fala do nosso grupo — cobre grupo básico (chat) e supergrupo (channel)."""
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
    """Reconhece qualquer bloqueio de envio como 'grupo ainda fechado'."""
    s = str(e).lower()
    return ('plain' in s) or ('forbidden' in s and 'send' in s) \
        or ('write' in s and 'forbidden' in s)


async def disparar(client, peer, msg, nome, vencido, origem, contador, random_id):
    """Um envio isolado. Não bloqueia os outros (pipelining)."""
    if vencido.is_set():
        return
    contador['n'] += 1
    idx = contador['n']
    t0 = time.monotonic()
    try:
        # mesmo random_id em todos os tiros -> Telegram deduplica, posta UMA só
        await client(SendMessageRequest(peer=peer, message=msg, random_id=random_id))
        if not vencido.is_set():
            vencido.set()
            rtt = (time.monotonic() - t0) * 1000
            agora = datetime.now(TZ).strftime('%H:%M:%S.%f')
            print(f"🏆 {nome} ENVIOU via {origem}! tiro #{idx} "
                  f"({agora}) rtt~{rtt:.0f}ms")
    except ChatWriteForbiddenError:
        pass  # ainda fechado; outro tiro pega
    except FloodWaitError as e:
        print(f"🛑 {nome} FLOOD {e.seconds}s -> aumente o LAUNCH_INTERVAL")
        await asyncio.sleep(e.seconds)
    except SlowModeWaitError as e:
        print(f"🐌 {nome} slowmode {e.seconds}s")
    except Exception as e:
        if _eh_fechado(e):
            pass  # outro tipo de bloqueio = ainda fechado, silencioso
        else:
            print(f"⚠️ {nome} erro: {e}")
            await asyncio.sleep(0.3)


async def sniper(conta, alvo):
    session = os.environ.get(conta['secret_name'])
    if not session:
        print(f"⚠️ {conta['nome']}: secret não encontrado.")
        return

    client = TelegramClient(StringSession(session), API_ID, API_HASH)
    nome = conta['nome']
    msg = conta['msg']
    on_update = None
    try:
        await client.connect()
        await client.get_dialogs()
        if not await client.is_user_authorized():
            print(f"❌ {nome}: login falhou.")
            return

        peer = await client.get_input_entity(conta['chat_id'])
        canal_id, _ = utils.resolve_id(conta['chat_id'])
        random_id = random.randrange(-(2**63), 2**63 - 1)  # fixo por rodada
        print(f"✅ {nome} pronto | DC {client.session.dc_id} | canal {canal_id}")

        vencido = asyncio.Event()
        janela = {'on': False}
        contador = {'n': 0}
        pendentes = []

        def fire(origem):
            pendentes.append(asyncio.create_task(
                disparar(client, peer, msg, nome, vencido, origem, contador, random_id)
            ))

        # --- OUVINTE (desligado para o modo SÓ PIPELINE) ---
        async def on_update(update):
            if vencido.is_set() or not janela['on']:
                return
            try:
                if _refere_canal(update, canal_id):
                    fire('LISTENER')
            except Exception:
                pass
        # client.add_event_handler(on_update, events.Raw)   # <- descomente p/ voltar o listener

        # Espera econômica até faltar 15s.
        while (alvo - datetime.now(TZ)).total_seconds() > 15:
            await asyncio.sleep(1)
        try:
            await client.get_me()   # esquenta o socket
        except Exception:
            pass

        inicio = alvo - timedelta(seconds=ANTECIPACAO_S)
        deadline = alvo + timedelta(seconds=DESISTIR_APOS_S)
        while datetime.now(TZ) < inicio:
            await asyncio.sleep(0.01)

        # --- PIPELINE martelando ---
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

    await asyncio.gather(*(sniper(c, alvo) for c in CONTAS))


if __name__ == '__main__':
    asyncio.run(main())