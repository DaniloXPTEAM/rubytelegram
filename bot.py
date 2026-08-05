#!/usr/bin/env python3
"""
Bot da RubyFox (Ruby, Crystal e Scarlet) - Telegram PROFISSIONAL
- Botões inline (menus guiados)
- Saudação com foto + confirmação 18+
- Escolher garota
- Menu principal: Packs, Grupo (acesso a fotos/vídeos), Vídeo unitário, Amostra de voz, Pagamento
- Conversa natural usando os áudios
- Webhook Flask + Telegram
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

if CONFIG_FILE.exists():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        CONFIG = json.load(f)
else:
    CONFIG = {"telegram_token": os.getenv("TELEGRAM_TOKEN", "SEU_TOKEN"), "admin_id": 0}

TELEGRAM_TOKEN = CONFIG.get("telegram_token", os.getenv("TELEGRAM_TOKEN"))
ADMIN_ID = CONFIG.get("admin_id", int(os.getenv("ADMIN_ID", 0)))
TABELA = CONFIG.get("tabela", {})
GAROTAS = CONFIG.get("garotas", {})
TOPICS = CONFIG.get("topics", [])
CHAVE_PIX = CONFIG.get("chave_pix_global", "crystalrae.ai@gmail.com")
VIDEO_UNITARIO = CONFIG.get("video_unitario", {"preco": 3.0})
VIDEO_UNITARIO["chave_pix"] = CHAVE_PIX
GRUPOS = CONFIG.get("grupos", {})          # nome -> link de convite
FOTO_SAUDACAO = CONFIG.get("foto_saudacao", "")  # caminho da foto (opcional)
TEXTOS = CONFIG.get("textos", {})

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, MessageHandler, CallbackQueryHandler,
        filters, ContextTypes,
    )
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
pedidos_pendentes = {}
user_state = {}            # chat_id -> {garota, etapa}
perguntas = {}
ultimo_contato = {}
followup_enviado = {}

# ============ HELPERS ============
def resolver_audio(nome):
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
    mapa = {"á":"a","à":"a","ã":"a","â":"a","ä":"a","é":"e","è":"e","ê":"e","ë":"e",
            "í":"i","ì":"i","î":"i","ï":"i","ó":"o","ò":"o","õ":"o","ô":"o","ö":"o",
            "ú":"u","ù":"u","û":"u","ü":"u","ç":"c"}
    return "".join(mapa.get(ch, ch) for ch in (texto or "").lower())

def montar_tabela_texto():
    linhas = ["💎 **Nossa Tabela (mesma para as 3 garotas):**\n"]
    for chave, info in TABELA.items():
        linhas.append(
            f"• {info.get('nome', chave)} — {info.get('descricao', '')} — R$ {info.get('preco', 0):.2f}\n"
            f"  Comando: /comprar {chave}\n"
        )
    return "\n".join(linhas)

def btn(texto, data):
    return InlineKeyboardButton(texto, callback_data=data)

def keyboard(botoes_linhas):
    return InlineKeyboardMarkup(botoes_linhas)

# ============ BOTÕES / MENUS ============
def menu_18():
    return keyboard([[btn("✅ Sou maior de 18", "18ok")]])

def menu_garotas():
    linhas = []
    for g, info in GAROTAS.items():
        linhas.append([btn(f"✨ {info.get('nome', g)}", f"garota:{g}")])
    return keyboard(linhas)

def menu_principal(garota_nome):
    return keyboard([
        [btn("🔥 Ver Packs", "packs"), btn("👥 Grupo VIP", "grupo")],
        [btn("🎬 Vídeo (R$3)", "video"), btn("🎙️ Amostra de voz", "amostra")],
        [btn("💳 Pagamento", "pix"), btn("❓ Ajuda", "ajuda")],
    ])

def menu_packs():
    linhas = []
    for chave, info in TABELA.items():
        linhas.append([btn(f"💖 {info.get('nome', chave)} — R$ {info.get('preco', 0):.2f}", f"comprar:{chave}")])
    linhas.append([btn("⬅️ Voltar", "menu")])
    return keyboard(linhas)

def menu_voltar():
    return keyboard([[btn("⬅️ Voltar ao menu", "menu")]])

# ============ HANDLERS ============
async def start(update, context):
    chat_id = update.effective_chat.id
    user = update.effective_user
    ultimo_contato[chat_id] = time.time()
    user_state[chat_id] = {"etapa": "18"}

    texto = (
        f"✨ Oi, {user.first_name}! 😈\n"
        "Bem-vinda ao nosso cantinho exclusivo...\n\n"
        "Aqui você encontra as garotas **Ruby, Crystal e Scarlet** com "
        "packs exclusivos, vídeo e acesso a grupos VIP.\n\n"
        "🔞 **Antes de continuar, confirme que você é maior de 18 anos:**"
    )
    if FOTO_SAUDACAO and os.path.exists(FOTO_SAUDACAO):
        try:
            with open(FOTO_SAUDACAO, "rb") as f:
                await update.message.reply_photo(photo=f, caption=texto, reply_markup=menu_18())
            return
        except Exception as e:
            logger.error(f"Erro foto saudação: {e}")
    await update.message.reply_text(texto, reply_markup=menu_18())

async def callback_handler(update, context):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    data = query.data
    ultimo_contato[chat_id] = time.time()
    user_state.setdefault(chat_id, {})

    if data == "18ok":
        user_state[chat_id]["etapa"] = "garotas"
        await query.message.reply_text(
            "✅ Confirmado! Agora me conta: **qual garota você quer conhecer?** 😉",
            reply_markup=menu_garotas(),
        )
        return

    if data.startswith("garota:"):
        g = data.split(":", 1)[1]
        if g in GAROTAS:
            user_state[chat_id]["garota"] = g
            user_state[chat_id]["etapa"] = "menu"
            nome = GAROTAS[g].get("nome", g)
            # envia áudio de boas-vindas da garota se houver
            await query.message.reply_text(
                f"✨ Perfeito! Você escolheu a **{nome}**.\n\n"
                "Agora escolha o que você quer:",
                reply_markup=menu_principal(nome),
            )
            arquivo = resolver_audio(GAROTAS[g].get("audio_boasvindas", ""))
            if arquivo:
                try:
                    with open(arquivo, "rb") as a:
                        await query.message.reply_voice(voice=a)
                except Exception as e:
                    logger.error(f"Erro áudio boas-vindas: {e}")
        return

    if data == "menu":
        g = user_state[chat_id].get("garota") or "crystal"
        nome = GAROTAS.get(g, {}).get("nome", g)
        await query.message.reply_text(
            f"✨ Você está com a **{nome}**. O que deseja?",
            reply_markup=menu_principal(nome),
        )
        return

    if data == "packs":
        await query.message.reply_text(montar_tabela_texto(), reply_markup=menu_packs())
        return

    if data == "grupo":
        g = user_state[chat_id].get("garota") or "crystal"
        link = GRUPOS.get(g) or GRUPOS.get("geral") or ""
        if link:
            await query.message.reply_text(
                f"👥 **Grupo VIP da {GAROTAS.get(g, {}).get('nome', g)}!**\n\n"
                "Entre no grupo e tenha acesso a **várias fotos e vídeos exclusivos**! 🔥\n\n"
                f"👉 [Entrar no grupo VIP]({link})",
                reply_markup=menu_voltar(),
            )
        else:
            await query.message.reply_text(
                "👥 O link do grupo VIP ainda não foi configurado. Em breve! 😉",
                reply_markup=menu_voltar(),
            )
        return

    if data == "video":
        g = user_state[chat_id].get("garota") or "crystal"
        pedidos_pendentes[chat_id] = {"garota": g, "pacote": "video_unit", "status": "pendente", "valor": VIDEO_UNITARIO["preco"]}
        await query.message.reply_text(
            f"🎬 Te mando um vídeo da **{GAROTAS.get(g, {}).get('nome', g)}** por **R$ {VIDEO_UNITARIO['preco']:.2f}** 😉\n\n"
            f"💳 Chave Pix: `{CHAVE_PIX}`\n\n"
            "Assim que confirmar o pagamento, te envio! 🔥",
            reply_markup=menu_voltar(),
        )
        return

    if data == "amostra":
        g = user_state[chat_id].get("garota") or "crystal"
        arquivo = resolver_audio(GAROTAS.get(g, {}).get("audio_amostra", "") or CONFIG.get("audio_amostra", ""))
        if arquivo:
            try:
                with open(arquivo, "rb") as a:
                    await query.message.reply_voice(voice=a, caption="🎙️ Uma amostrinha da minha voz... 😏")
            except Exception as e:
                logger.error(f"Erro amostra: {e}")
        else:
            await query.message.reply_text("🎙️ Escolha a garota para ouvir a amostra de voz!", reply_markup=menu_garotas())
        return

    if data == "pix":
        await query.message.reply_text(
            f"💳 **Pagamento via Pix**\n\n"
            f"Chave: `{CHAVE_PIX}`\n\n"
            "Escolha um pack e me avise quando pagar! 😉",
            reply_markup=menu_voltar(),
        )
        return

    if data == "ajuda":
        await query.message.reply_text(
            "❓ **Como funciona:**\n\n"
            "• Escolha a garota\n"
            "• Escolha um pack ou entre no grupo VIP\n"
            "• Pague via Pix e receba o conteúdo\n\n"
            "Comandos: /start, /garotas, /pacotes",
            reply_markup=menu_voltar(),
        )
        return

    if data.startswith("comprar:"):
        pacote = data.split(":", 1)[1]
        info = TABELA.get(pacote)
        if not info:
            await query.message.reply_text("Pack não encontrado.")
            return
        g = user_state[chat_id].get("garota") or "crystal"
        pedidos_pendentes[chat_id] = {"garota": g, "pacote": pacote, "status": "pendente"}
        await query.message.reply_text(
            f"💖 Você escolheu: **{info.get('nome', pacote)}** — {info.get('descricao', '')}\n"
            f"Valor: **R$ {info.get('preco', 0):.2f}**\n\n"
            f"💳 **Pague via PIX:**\nChave: `{CHAVE_PIX}`\n\n"
            "Assim que confirmar, te envio tudo aqui mesmo! 🔥",
            reply_markup=menu_voltar(),
        )
        return

# ============ MENSAGENS DE TEXTO (conversa + áudios) ============
async def handle_message(update, context):
    texto = update.message.text or ""
    texto_lower = texto.lower()
    chat_id = update.effective_chat.id
    ultimo_contato[chat_id] = time.time()

    # confirmação verbal de pagamento
    if any(p in texto_lower for p in ["paguei", "feito", "mandei o pix", "pix feito", "pix enviado", "paguei o pix"]):
        pedido = pedidos_pendentes.get(chat_id, {})
        if pedido.get("status") == "pendente":
            await update.message.reply_text("Assim que o pagamento confirmar, te envio tudo aqui mesmo! 🔥")
        else:
            await update.message.reply_text("Estou aguardando a confirmação do pagamento 😉")
        return

    # tópicos: 1ª vez texto, 2ª vez áudio
    t = normalizar(texto_lower)
    for topico in TOPICS:
        for g in topico.get("gatilhos", []):
            if normalizar(g) in t:
                nome = topico["nome"]
                cont = perguntas.setdefault(chat_id, {}).get(nome, 0) + 1
                perguntas[chat_id][nome] = cont

                # preço -> tabela + botões
                if nome == "preco":
                    await update.message.reply_text(TEXTOS.get("preco", "Aqui está nossa tabela 😉"), reply_markup=menu_packs())
                    return
                if nome == "video":
                    g = user_state.get(chat_id, {}).get("garota") or "crystal"
                    pedidos_pendentes[chat_id] = {"garota": g, "pacote": "video_unit", "status": "pendente"}
                    await update.message.reply_text(
                        f"🎬 Vídeo por R$ {VIDEO_UNITARIO['preco']:.2f} 😉\nChave: `{CHAVE_PIX}`",
                        reply_markup=menu_voltar(),
                    )
                    return

                if cont == 1:
                    await update.message.reply_text(topico.get("texto", ""), reply_markup=menu_voltar())
                    return
                arquivo = resolver_audio(topico.get("audio", ""))
                if arquivo:
                    try:
                        with open(arquivo, "rb") as a:
                            await update.message.reply_voice(voice=a, caption="🎙️")
                        return
                    except Exception as e:
                        logger.error(f"Erro áudio: {e}")
                await update.message.reply_text(topico.get("texto", ""), reply_markup=menu_voltar())
                return

    # resposta padrão
    await update.message.reply_text(
        TEXTOS.get("padrao", "Que bom falar com você... 😏 Me conta o que deseja: fotos, vídeos, grupo?"),
        reply_markup=menu_principal(user_state.get(chat_id, {}).get("garota") or "crystal"),
    )

# ============ COMANDOS ============
async def garotas_cmd(update, context):
    chat_id = update.effective_chat.id
    user_state.setdefault(chat_id, {})
    await update.message.reply_text(
        "✨ Escolha uma garota:",
        reply_markup=menu_garotas(),
    )

async def pacotes_cmd(update, context):
    await update.message.reply_text(montar_tabela_texto(), reply_markup=menu_packs())

async def comprar(update, context):
    args = context.args
    chat_id = update.effective_chat.id
    if not args:
        await update.message.reply_text("Uso: /comprar <bronze|prata|ouro>", reply_markup=menu_packs())
        return
    pacote = args[0].lower()
    info = TABELA.get(pacote)
    if not info:
        await update.message.reply_text("Pack não encontrado. Disponíveis: bronze, prata, ouro")
        return
    g = user_state.get(chat_id, {}).get("garota") or "crystal"
    pedidos_pendentes[chat_id] = {"garota": g, "pacote": pacote, "status": "pendente"}
    await update.message.reply_text(
        f"💖 {info.get('nome', pacote)} — {info.get('descricao', '')} — R$ {info.get('preco', 0):.2f}\n"
        f"💳 Pix: `{CHAVE_PIX}`",
        reply_markup=menu_voltar(),
    )

async def ajuda(update, context):
    await update.message.reply_text(
        "❓ **Como funciona:**\n\n• Escolha a garota\n• Pack ou grupo VIP\n• Pague via Pix e receba\n\nComandos: /start, /garotas, /pacotes",
        reply_markup=menu_principal(user_state.get(update.effective_chat.id, {}).get("garota") or "crystal"),
    )

# ============ FOLLOW-UP 3 DIAS ============
def rodar_followup(app_telegram):
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
                    caminho = resolver_audio(audios_followup[len(followup_enviado) % len(audios_followup)])
                    if caminho:
                        try:
                            with open(caminho, "rb") as a:
                                app_telegram.bot.send_voice(chat_id=chat_id, voice=a)
                            logger.info(f"Follow-up enviado para {chat_id}")
                        except Exception as e:
                            logger.error(f"Erro follow-up: {e}")
                    followup_enviado[chat_id] = True
        except Exception as e:
            logger.error(f"Erro follow-up: {e}")
        time.sleep(1800)

# ============ FLASK / WEBHOOKS ============
app_flask = Flask(__name__)

@app_flask.route("/", methods=["GET"])
def index():
    return "Bot da RubyFox rodando. Webhooks: /telegram/webhook e /webhook/pagamento"

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
        followup_enviado[chat_id] = True
        logger.info(f"Pagamento confirmado: chat {chat_id}, pacote {pacote}")
        try:
            import requests
            token = TELEGRAM_TOKEN
            nome_pacote = TABELA.get(pacote, {}).get("nome", pacote)
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat_id, "text": f"🎉 **Pagamento confirmado!** Você recebeu: **{nome_pacote}**\nAqui estão seus arquivos:"})
            garota = pedidos_pendentes[chat_id].get("garota") or "crystal"
            if pacote in ("video_unit", "video"):
                aud = resolver_audio("audios/to deitada na minha cama, vou te mandar um video.ogg")
                if aud:
                    with open(aud, "rb") as f:
                        requests.post(f"https://api.telegram.org/bot{token}/sendVoice",
                                      data={"chat_id": chat_id}, files={"voice": f})
                pasta = Path(__file__).parent / GAROTAS.get(garota, {}).get("pastas", {}).get("vip", f"pacotes/{garota}/vip/")
                videos = [x for x in pasta.iterdir() if x.is_file()] if pasta.exists() else []
                if videos:
                    with open(videos[0], "rb") as f:
                        requests.post(f"https://api.telegram.org/bot{token}/sendVideo",
                                      data={"chat_id": chat_id}, files={"video": f})
            else:
                arquivos = listar_arquivos_pacote(pacote, garota)
                for arq in arquivos:
                    with open(arq, "rb") as f:
                        nome = os.path.basename(arq)
                        requests.post(f"https://api.telegram.org/bot{token}/sendDocument",
                                      data={"chat_id": chat_id, "caption": f"📁 {nome}"}, files={"document": f})
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat_id, "text": "🔥 Aproveite! Se quiser mais, fale comigo. 😈"})
        except Exception as e:
            logger.error(f"Erro ao enviar arquivos: {e}")
            return jsonify({"erro": f"Erro: {e}"}), 500
        return jsonify({"status": "liberado", "chat_id": chat_id, "pacote": pacote}), 200

    pedidos_pendentes[chat_id]["status"] = status
    return jsonify({"status": status, "chat_id": chat_id}), 200

def listar_arquivos_pacote(pacote_nome, garota=None):
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
    app_telegram.add_handler(CommandHandler("garotas", garotas_cmd))
    app_telegram.add_handler(CommandHandler("pacotes", pacotes_cmd))
    app_telegram.add_handler(CommandHandler("comprar", comprar))
    app_telegram.add_handler(CommandHandler("ajuda", ajuda))
    app_telegram.add_handler(CallbackQueryHandler(callback_handler))
    app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    Thread(target=rodar_followup, args=(app_telegram,), daemon=True).start()

    # ============ ARQUITETURA: loop dedicado + Flask em thread ============
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def iniciar_bot():
        await app_telegram.initialize()
        await app_telegram.start()
        logger.info("✅ Application do Telegram inicializada e iniciada.")
        try:
            RENDER_URL = os.getenv("RENDER_URL", "https://rubytelegram.onrender.com")
            url = f"{RENDER_URL}/telegram/webhook"
            ok = await app_telegram.bot.set_webhook(url)
            logger.info(f"✅ Webhook Telegram configurado: {url} -> {ok}")
        except Exception as e:
            logger.error(f"Falha ao configurar webhook: {e}")

    try:
        loop.run_until_complete(iniciar_bot())
    except Exception as e:
        logger.error(f"Falha ao iniciar bot: {e}")
        import traceback; traceback.print_exc()
        app_telegram.run_polling(allowed_updates=Update.ALL_TYPES)
        return

    @app_flask.route("/telegram/webhook", methods=["POST"])
    def telegram_webhook():
        if not FLASK_AVAILABLE:
            return "Flask indisponível", 500
        try:
            json_data = request.get_json(force=True)
            update = Update.de_json(json_data, app_telegram.bot)
            asyncio.run_coroutine_threadsafe(app_telegram.process_update(update), loop)
        except Exception as e:
            logger.error(f"Erro ao processar update: {e}")
            import traceback; traceback.print_exc()
        return "OK", 200

    def rodar_loop():
        loop.run_forever()
    Thread(target=rodar_loop, daemon=True).start()

    logger.info("Iniciando Flask (webhooks ativos)...")
    porta = int(os.getenv("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=porta)

if __name__ == "__main__":
    main()
