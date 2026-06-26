import asyncio
import os
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from telethon import TelegramClient, events, utils
from telethon.sessions import StringSession
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
HORA_ALVO = 19
MINUTO_ALVO = 3
SEGUNDO_ALVO = 0

# Começa a martelar a porta um pouco antes do horário.
ANTECIPACAO_S = 0.0

# Espaçamento entre disparos sobrepostos do PIPELINE (a rede de segurança).
# Seu log mostrou ~21 tentativas/s sem flood, então 0.05 (~20/s) é seguro.
# Se aparecer "🛑 FLOOD", aumente. Para apertar, teste 0.04.
LAUNCH_INTERVAL = 0.04

DESISTIR_APOS_S = 120

CONTAS = [


    {
        "nome": "Thaina",
        "secret_name": "SESSION_THAINA",
        "chat_id": -1004431335449,   
        "msg": "Thaina X Daniel R2",
    },
    # Todas as contas são DC Miami -> rode tudo nesta VPS de Miami.
]


def _refere_canal(update, canal_id):
    """True se o update fala do nosso grupo — cobre grupo básico (chat) e supergrupo (channel)."""
    if getattr(update, 'channel_id', None) == canal_id:
        return True
    if getattr(update, 'chat_id', None) == canal_id:
        return True
    # alguns updates trazem o grupo em .peer (ex.: UpdateChatDefaultBannedRights)
    peer = getattr(update, 'peer', None)
    if peer is not None:
        if getattr(peer, 'chat_id', None) == canal_id:
            return True
        if getattr(peer, 'channel_id', None) == canal_id:
            return True
    # ou dentro de .message.peer_id
    msg = getattr(update, 'message', None)
    pid = getattr(msg, 'peer_id', None) if msg is not None else None
    if pid is not None:
        if getattr(pid, 'chat_id', None) == canal_id:
            return True
        if getattr(pid, 'channel_id', None) == canal_id:
            return True
    return False


async def disparar(client, peer, msg, nome, vencido, origem, contador):
    """Um envio isolado. Não bloqueia os outros (pipelining)."""
    if vencido.is_set():
        return
    contador['n'] += 1
    idx = contador['n']
    t0 = time.monotonic()
    try:
        await client.send_message(peer, msg)
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
        print(f"⚠️ {nome} erro: {e}")


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
        print(f"✅ {nome} pronto | DC {client.session.dc_id} | canal {canal_id}")

        vencido = asyncio.Event()
        janela = {'on': False}      # só reage a updates dentro da janela de disparo
        contador = {'n': 0}
        pendentes = []

        def fire(origem):
            pendentes.append(asyncio.create_task(
                disparar(client, peer, msg, nome, vencido, origem, contador)
            ))

        # --- OUVINTE: dispara no instante que o aviso de "grupo abriu" chega ---
        async def on_update(update):
            if vencido.is_set() or not janela['on']:
                return
            print(f"📨 update recebido: {type(update).__name__}")   # <-- ADICIONE
            try:
                if _refere_canal(update, canal_id):
                    fire('LISTENER')
            except Exception:
                pass
        #client.add_event_handler(on_update, events.Raw)

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

        # --- A partir daqui: ouvinte ativo + pipeline martelando ---
        janela['on'] = True
        print(f"⚔️ {nome} ATIVO (listener + pipeline)")
        while not vencido.is_set() and datetime.now(TZ) < deadline:
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