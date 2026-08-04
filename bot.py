#!/usr/bin/env python3
"""
Bot da Ruby Fox (Crystal) - Telegram
Atendimento com áudio: 1ª vez que pergunta = responde por TEXTO;
2ª vez sobre o mesmo assunto = envia o ÁUDIO.
Venda de vídeo unitário (R$3), tabela de preços, follow-up de 3 dias.
"""
import os
import json
import logging
import time
from pathlib import Path
from threading import Thread

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).parent / "config.json"
AUDIO_FOLDER = Path(__file__).parent / "audios"
PACOTES_FOLDER = Path(__file__).parent / "pacotes"

if CONFIG_FILE.exists():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        CONFIG = json.load(f)
else:
    CONFIG = {
        "telegram_token": os.getenv("TELEGRAM_TOKEN", "SEU_TOKEN"),
        "admin_id": int(os.getenv("ADMIN_ID", 123456789)),
        "audio_map": {}, "pacotes": {}, "respostas_texto": {}, "topics": []
    }

TELEGRAM_TOKEN = CONFIG.get("telegram_token", os.getenv("TELEGRAM_TOKEN"))
ADMIN_ID = CONFIG.get("admin_id", int(os.getenv("ADMIN_ID", 0)))
TABELA = CONFIG.get("tabela", {})
CHAVE_PIX = CONFIG.get("chave_pix_global", "crystalrae.ai@gmail.com")
GAROTAS = CONFIG.get("garotas", {})
PACOTES = CONFIG.get("pacotes", {})
RESP_TEXT = CONFIG.get("respostas_texto", {})
TOPICS = CONFIG.get("topics", [])
VIDEO_UNITARIO = CONFIG.get("video_unitario", {"preco": 3.0})
VIDEO_UNITARIO["chave_pix"] = CHAVE_PIX

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("python-telegram-bot não instalado.")

try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

# ============ ESTADO ============
pedidos_pendentes = {}          # chat_id -> {pacote, status, ...}
perguntas = {}                  # chat_id -> {topico: contagem}
ultimo_contato = {}             # chat_id -> timestamp
followup_enviado = {}           # chat_id -> True/False

def resolver_audio(nome):
    """Retorna o caminho do áudio se existir (aceita sem extensão ou com)."""
    if not nome:
        return None
    candidatos = [nome]
    if not Path(nome).suffix:
        candidatos += [nome + ".ogg", nome + ".mp3", nome + ".opus"]
    for c in candidatos:
        p = Path(__file__).parent / c
        if p.exists():
            return str(p)
    return None

def normalizar(texto):
    """Remove acentos e normaliza para minúsculas (cliente pode digitar com/sem acento)."""
    mapa = {
        "á": "a", "à": "a", "ã": "a", "â": "a", "ä": "a",
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "í": "i", "ì": "i", "î": "i", "ï": "i",
        "ó": "o", "ò": "o", "õ": "o", "ô": "o", "ö": "o",
        "ú": "u", "ù": "u", "û": "u", "ü": "u",
        "ç": "c",
    }
    return "".join(mapa.get(ch, ch) for ch in (texto or "").lower())

def achar_topico(texto_lower):
    """Encontra o tópico que a mensagem do cliente corresponde (ignorando acentos)."""
    t = normalizar(texto_lower)
    for topico in TOPICS:
        for g in topico.get("gatilhos", []):
            if normalizar(g) in t:
                return topico
    return None

def montar_tabela(garota=None):
    """Tabela de preços ÚNICA (mesma para as 3 garotas)."""
    linhas = ["💎 **Nossa Tabela (mesma para as 3 garotas):**\n"]
    if garota and garota in GAROTAS:
        linhas = [f"💎 **{GAROTAS[garota].get('nome', garota)}** — nossa tabela:\n"]
    for chave, info in TABELA.items():
        linhas.append(
            f"• {info.get('nome', chave)} — {info.get('descricao', '')} — R$ {info.get('preco', 0):.2f}\n"
            f"  Comando: /comprar {chave}\n"
        )
    return "\n".join(linhas)

# ============ HANDLERS ============
async def start(update, context):
    user = update.effective_user
    mensagem = (
        f"✨ Oi, {user.first_name}... que bom que você chegou. 😈\n"
        "Eu sou a Crystal, sua influenciadora virtual preferida.\n\n"
        "Antes de prosseguir, confirme que você tem +18 anos: /confirmar"
    )
    await update.message.reply_text(mensagem)

async def confirmar(update, context):
    await update.message.reply_text(
        "✅ Confirmado! Agora me conta: quer ver meus packs, um vídeo ou algo mais? 💋"
    )
    arquivo = resolver_audio(CONFIG.get("audio_confirmar", ""))
    if arquivo:
        try:
            with open(arquivo, "rb") as a:
                await update.message.reply_voice(voice=a)
        except Exception as e:
            logger.error(f"Erro áudio confirmar: {e}")

async def garotas_cmd(update, context):
    """Lista as garotas disponíveis."""
    nomes = [info.get("nome", g) for g, info in GAROTAS.items()]
    await update.message.reply_text(
        f"Temos {', '.join(nomes)} 😊\n"
        "Digite o nome da que você quer (ex.: /garota crystal)"
    )

async def garota_cmd(update, context):
    """Seleciona uma garota."""
    args = context.args
    if not args:
        await update.message.reply_text("Escolha: ruby, crystal ou scarlet. Ex.: /garota crystal")
        return
    nome = args[0].lower()
    if nome not in GAROTAS:
        await update.message.reply_text("Garota não encontrada. Disponíveis: ruby, crystal, scarlet")
        return
    chat_id = update.effective_chat.id
    pedidos_pendentes.setdefault(chat_id, {})["garota"] = nome
    await update.message.reply_text(montar_tabela(nome))

async def comprar(update, context):
    args = context.args
    chat_id = update.effective_chat.id
    pedidos_pendentes.setdefault(chat_id, {})
    garota = pedidos_pendentes[chat_id].get("garota") or "crystal"

    if not args:
        await update.message.reply_text("Uso: /comprar <bronze|prata|ouro>. A tabela é a mesma pra todas 😉")
        return
    pacote = args[0].lower()
    info = TABELA.get(pacote)
    if not info:
        await update.message.reply_text("Pack não encontrado. Disponíveis: bronze, prata, ouro")
        return

    chave = CHAVE_PIX
    pedidos_pendentes[chat_id] = {"garota": garota, "pacote": pacote, "status": "pendente", "chave_pix": chave}
    texto = (
        f"💖 Você escolheu (da {GAROTAS.get(garota, {}).get('nome', garota)}): **{info.get('nome', pacote)}** — {info.get('descricao', '')}\n"
        f"Valor: **R$ {info.get('preco', 0):.2f}**\n\n"
        f"💳 **Pague via PIX:**\nChave: `{chave}`\n\n"
        f"Após a confirmação, você recebe tudo aqui mesmo! 🔥"
    )
    await update.message.reply_text(texto)

async def pacotes_cmd(update, context):
    await update.message.reply_text(montar_tabela())

async def ajuda(update, context):
    await update.message.reply_text(
        "Comandos:\n/start - início\n/confirmar - confirmar 18+\n"
        "/pacotes - tabela de preços\n/comprar <bronze|prata|ouro> - comprar"
    )

async def handle_message(update, context):
    texto = update.message.text or ""
    texto_lower = texto.lower()
    chat_id = update.effective_chat.id

    # registra contato (para follow-up de 3 dias)
    ultimo_contato[chat_id] = time.time()

    # ---------- REGRA GERAL: 1ª vez = texto, 2ª vez = áudio ----------
    topico = achar_topico(texto_lower)
    if topico:
        nome = topico["nome"]
        cont = perguntas.setdefault(chat_id, {}).get(nome, 0) + 1
        perguntas[chat_id][nome] = cont

        # ----- TÓPICO ESPECIAL: vídeo unitário (R$ 3) -----
        if nome == "video":
            if cont == 1:
                pedidos_pendentes[chat_id] = {"pacote": "video_unit", "status": "pendente", "valor": VIDEO_UNITARIO["preco"]}
                await update.message.reply_text(
                    f"Te mando um vídeo por **R$ {VIDEO_UNITARIO['preco']:.2f}** 😉\n"
                    f"Chave Pix: `{VIDEO_UNITARIO['chave_pix']}`\n"
                    f"Assim que confirmar o pagamento, te envio! 🔥"
                )
                return
            else:
                # 2ª vez: provoca com áudio
                arquivo = resolver_audio(topico.get("audio", ""))
                if arquivo:
                    try:
                        with open(arquivo, "rb") as a:
                            await update.message.reply_voice(voice=a)
                        return
                    except Exception as e:
                        logger.error(f"Erro áudio video: {e}")
                await update.message.reply_text("É só confirmar o vídeo por R$ 3,00 que eu te mando 😉")
                return

        # ----- TÓPICO ESPECIAL: preço -> manda a TABELA -----
        if nome == "preco":
            await update.message.reply_text(montar_tabela())
            return

        # ----- TÓPICO ESPECIAL: pix -> manda a chave -----
        if nome == "pix":
            await update.message.reply_text(
                f"Vou te mandar meu pix 😉\nChave: `{VIDEO_UNITARIO['chave_pix']}`"
            )
            return

        # ----- 1ª vez: TEXTO -----
        if cont == 1:
            await update.message.reply_text(topico.get("texto", ""))
            return

        # ----- 2ª vez+: ÁUDIO -----
        arquivo = resolver_audio(topico.get("audio", ""))
        if arquivo:
            try:
                with open(arquivo, "rb") as a:
                    await update.message.reply_voice(voice=a, caption="🎙️")
                return
            except Exception as e:
                logger.error(f"Erro áudio tópico {nome}: {e}")
        # sem áudio: repete o texto
        await update.message.reply_text(topico.get("texto", ""))

    # ---------- confirmação verbal de pagamento ----------
    if any(p in texto_lower for p in ["paguei", "feito", "mandei o pix", "pix feito", "paguei o pix", "pix enviado", "pix feito"]):
        if chat_id in pedidos_pendentes and pedidos_pendentes[chat_id]["status"] == "pendente":
            await update.message.reply_text("Assim que o pagamento confirmar, te envio tudo aqui mesmo! 🔥")
            return
        await update.message.reply_text("Estou aguardando a confirmação do pagamento 😉")
        return

    # ---------- sem tópico: resposta padrão ----------
    resposta = "Que bom falar com você... 😏 Me conta o que deseja: fotos, vídeos, preços?"
    for gatilho, resp in RESP_TEXT.items():
        if gatilho in texto_lower:
            resposta = resp
            break
    if any(p in texto_lower for p in ["preço", "preco", "pacote", "comprar", "pix"]):
        resposta += "\n\n" + montar_tabela()
    await update.message.reply_text(resposta)

# ============ FOLLOW-UP 3 DIAS ============
def rodar_followup(app_telegram):
    """A cada 30min, verifica chats sem pagamento e sem mensagem há 3 dias."""
    audios_followup = [
        "audios/nossa engraçado que depois que eu mandei minha tabelinha vc ja nao quis falar mais cmg.ogg",
        "audios/oi amor, voce so vizualiza minhas mensagens.ogg",
    ]
    while True:
        try:
            agora = time.time()
            for chat_id, ultimo in list(ultimo_contato.items()):
                if followup_enviado.get(chat_id):
                    continue
                pendente = pedidos_pendentes.get(chat_id, {}).get("status") != "pago"
                if pendente and (agora - ultimo) > 3 * 86400:
                    idx = len(followup_enviado) % len(audios_followup)
                    caminho = resolver_audio(audios_followup[idx])
                    if caminho:
                        try:
                            with open(caminho, "rb") as a:
                                app_telegram.bot.send_voice(chat_id=chat_id, voice=a)
                            logger.info(f"Follow-up enviado para {chat_id}")
                        except Exception as e:
                            logger.error(f"Erro follow-up {chat_id}: {e}")
                    followup_enviado[chat_id] = True
        except Exception as e:
            logger.error(f"Erro no follow-up: {e}")
        time.sleep(1800)  # 30 min

# ============ FLASK / WEBHOOKS ============
app_flask = Flask(__name__)

@app_flask.route("/", methods=["GET"])
def index():
    return "Bot da Crystal rodando. Webhooks: /telegram/webhook e /webhook/pagamento"

@app_flask.route("/webhook/pagamento", methods=["POST"])
def webhook_pagamento():
    if not FLASK_AVAILABLE:
        return jsonify({"error": "Flask indisponível"}), 500
    try:
        dados = request.get_json(force=True)
        chat_id = dados.get("chat_id") or dados.get("user_id") or dados.get("id")
        pacote = dados.get("pacote")
        status = dados.get("status", "pago")
    except Exception as e:
        logger.error(f"Erro ler webhook: {e}")
        return jsonify({"erro": "JSON inválido"}), 400
    if not chat_id:
        return jsonify({"erro": "chat_id obrigatório"}), 400
    chat_id = int(chat_id)
    pedidos_pendentes.setdefault(chat_id, {"pacote": pacote, "status": "pendente"})

    if status in ("pago", "confirmado", "aprovado"):
        pedidos_pendentes[chat_id]["status"] = "pago"
        logger.info(f"Pagamento confirmado: chat {chat_id}, pacote {pacote}")
        # follow-up não precisa mais
        followup_enviado[chat_id] = True
        try:
            import requests
            token = TELEGRAM_TOKEN
            nome_pacote = PACOTES.get(pacote, {}).get("nome", pacote)
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": f"🎉 **Pagamento confirmado!** Você recebeu: **{nome_pacote}**\nAqui estão seus arquivos:"}
            )
            # envia áudio + arquivos
            if pacote in ("video_unit", "video"):
                # vídeo unitário: áudio + 1 vídeo da pasta vip
                aud = resolver_audio("audios/to deitada na minha cama, vou te mandar um video.ogg")
                if aud:
                    with open(aud, "rb") as f:
                        requests.post(f"https://api.telegram.org/bot{token}/sendVoice",
                                      data={"chat_id": chat_id}, files={"voice": f})
                garota_vid = pedidos_pendentes.get(chat_id, {}).get("garota") or "crystal"
                pasta = Path(__file__).parent / GAROTAS.get(garota_vid, {}).get("pastas", {}).get("vip", f"pacotes/{garota_vid}/vip/")
                videos = [x for x in pasta.iterdir() if x.is_file()] if pasta.exists() else []
                if videos:
                    with open(videos[0], "rb") as f:
                        requests.post(f"https://api.telegram.org/bot{token}/sendVideo",
                                      data={"chat_id": chat_id}, files={"video": f})
            else:
                arquivos = listar_arquivos_pacote(pacote, pedidos_pendentes.get(chat_id, {}).get("garota"))
                for arq in arquivos:
                    with open(arq, "rb") as f:
                        nome = os.path.basename(arq)
                        requests.post(f"https://api.telegram.org/bot{token}/sendDocument",
                                      data={"chat_id": chat_id, "caption": f"📁 {nome}"}, files={"document": f})
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": "🔥 Aproveite! Se quiser mais, fale comigo. 😈"}
            )
        except Exception as e:
            logger.error(f"Erro ao enviar arquivos: {e}")
            return jsonify({"erro": f"Erro: {e}"}), 500
        return jsonify({"status": "liberado", "chat_id": chat_id, "pacote": pacote}), 200

    pedidos_pendentes[chat_id]["status"] = status
    return jsonify({"status": status, "chat_id": chat_id}), 200

def listar_arquivos_pacote(pacote_nome, garota=None):
    """Retorna arquivos do pack da garota escolhida (tabela é global)."""
    garota = garota or "crystal"
    if garota not in GAROTAS:
        return []
    pasta = GAROTAS[garota].get("pastas", {}).get(pacote_nome)
    if not pasta:
        return []
    dir_pacote = Path(__file__).parent / pasta
    if not dir_pacote.exists():
        return []
    return [str(x) for x in dir_pacote.iterdir() if x.is_file()]

def rodar_flask():
    porta = int(os.getenv("PORT", 5000))
    app_flask.run(host="0.0.0.0", port=porta)

# ============ MAIN ============
def main():
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "SEU_TOKEN":
        logger.error("TELEGRAM_TOKEN não configurado!")
        return
    if not TELEGRAM_AVAILABLE:
        logger.error("python-telegram-bot não instalado.")
        return

    app_telegram = Application.builder().token(TELEGRAM_TOKEN).build()

    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(CommandHandler("confirmar", confirmar))
    app_telegram.add_handler(CommandHandler("comprar", comprar))
    app_telegram.add_handler(CommandHandler("garotas", garotas_cmd))
    app_telegram.add_handler(CommandHandler("garota", garota_cmd))
    app_telegram.add_handler(CommandHandler("pacotes", pacotes_cmd))
    app_telegram.add_handler(CommandHandler("ajuda", ajuda))
    app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # follow-up em background
    Thread(target=rodar_followup, args=(app_telegram,), daemon=True).start()

    # WEBHOOK (em vez de polling - Render Free dorme)
    RENDER_URL = os.getenv("RENDER_URL", "https://rubytelegram.onrender.com")
    WEBHOOK_PATH = "/telegram/webhook"
    webhook_url = f"{RENDER_URL}{WEBHOOK_PATH}"
    try:
        ok = app_telegram.bot.set_webhook(webhook_url)
        logger.info(f"Webhook Telegram: {webhook_url} -> {ok}")
    except Exception as e:
        logger.error(f"Falha webhook: {e}")
        app_telegram.run_polling(allowed_updates=Update.ALL_TYPES)
        return

    @app_flask.route(WEBHOOK_PATH, methods=["POST"])
    def telegram_webhook():
        if not FLASK_AVAILABLE:
            return "Flask indisponível", 500
        json_data = request.get_json(force=True)
        app_telegram.process_update(Update.de_json(json_data, app_telegram.bot))
        return "OK", 200

    rodar_flask()

if __name__ == "__main__":
    main()
