#!/usr/bin/env python3
"""
Bot da Ruby Fox - Agente Virtual com Áudio Local, PIX e Liberação Automática
Ferramentas: Telegram (gratuito) + Python + Flask (gratuito)
"""

import os
import json
import logging
from pathlib import Path
from threading import Thread

# Configuração de logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============ CONFIGURAÇÕES ============
CONFIG_FILE = Path(__file__).parent / "config.json"
AUDIO_FOLDER = Path(__file__).parent / "audios"
PACOTES_FOLDER = Path(__file__).parent / "pacotes"

# Carrega configuração (se não existir, usa exemplo)
if CONFIG_FILE.exists():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        CONFIG = json.load(f)
else:
    CONFIG = {
        "telegram_token": os.getenv("TELEGRAM_TOKEN", "SEU_TOKEN"),
        "admin_id": int(os.getenv("ADMIN_ID", 123456789)),
        "audio_map": {},
        "pacotes": {},
        "respostas_texto": {}
    }

TELEGRAM_TOKEN = CONFIG.get("telegram_token", os.getenv("TELEGRAM_TOKEN"))
ADMIN_ID = CONFIG.get("admin_id", int(os.getenv("ADMIN_ID", 0)))
AUDIO_MAP = CONFIG.get("audio_map", {})
PACOTES = CONFIG.get("pacotes", {})
RESP_TEXT = CONFIG.get("respostas_texto", {})

# ============ BOT TELEGRAM ============
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, MessageHandler,
        filters, ContextTypes, CallbackQueryHandler
    )
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("python-telegram-bot não instalado. Instale com: pip install python-telegram-bot")

# ============ FLASK WEBHOOK ============
try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    logger.warning("Flask não instalado. Instale com: pip install flask")

# Estado simples em memória (em produção, use SQLite ou arquivo JSON)
pedidos_pendentes = {}  # chat_id -> {pacote, status, chave_pix}

# ============ FUNÇÕES DE ÁUDIO ============
def buscar_audio(texto: str) -> str | None:
    """Busca arquivo de áudio pelo mapa de gatilhos."""
    texto_lower = texto.lower()
    for gatilho, arquivo in AUDIO_MAP.items():
        if gatilho in texto_lower:
            caminho = Path(__file__).parent / arquivo
            if caminho.exists():
                return str(caminho)
    return None

def listar_arquivos_pacote(pacote_nome: str) -> list:
    """Retorna todos os arquivos de um pacote."""
    info = PACOTES.get(pacote_nome)
    if not info:
        return []
    dir_pacote = Path(__file__).parent / info.get("diretorio", f"pacotes/{pacote_nome}/")
    if not dir_pacote.exists():
        return []
    arquivos = []
    for item in dir_pacote.iterdir():
        if item.is_file():
            arquivos.append(str(item))
    return arquivos

# ============ FUNÇÕES DO BOT ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mensagem inicial."""
    user = update.effective_user
    mensagem = (
        f"✨ Oi, {user.first_name}... que bom que você chegou. 😈\n"
        "Eu sou a Ruby Fox, sua influenciadora virtual preferida.\n\n"
        "Antes de prosseguir, confirme que você tem +18 anos: /confirmar"
    )
    await update.message.reply_text(mensagem)

async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma maioridade."""
    await update.message.reply_text(
        "✅ Confirmado! Agora me conta: você quer ver meus pacotes, ouvir minha voz ou algo mais? 💋"
    )
    # Se quiser, envia um áudio de boas-vindas se existir
    arquivo = buscar_audio("confirmar")  # ou um gatilho específico
    if arquivo:
        await update.message.reply_voice(voice=open(arquivo, "rb"))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa mensagens e responde com texto + áudio (se gatilho detectado)."""
    texto = update.message.text or ""
    chat_id = update.effective_chat.id
    
    # 1. Detecta gatilho para áudio
    arquivo_audio = buscar_audio(texto)
    
    # 2. Monta resposta de texto baseada no conteúdo ou padrão
    resposta_texto = "Que bom falar com você... 😏 Me conta o que deseja: fotos, vídeos, preços?"
    
    # Se encontrou gatilho e tem resposta de texto configurada
    texto_lower = texto.lower()
    for gatilho, resp in RESP_TEXT.items():
        if gatilho in texto_lower:
            resposta_texto = resp
            break
    
    # Se mencionou pacotes/preços, adiciona link/explicação
    if any(p in texto_lower for p in ["preço", "preco", "pacote", "comprar", "pix"]):
        resposta_texto += "\n\n💎 **Meus Pacotes:**\n"
        for chave, info in PACOTES.items():
            resposta_texto += (
                f"• {info['nome']} — {info['descricao']} — R$ {info['preco']:.2f}\n"
                f"  Comando: /comprar {chave}\n"
            )
    
    # 3. Envia resposta por texto
    await update.message.reply_text(resposta_texto)
    
    # 4. Se detectou gatilho e arquivo existe, envia áudio
    if arquivo_audio:
        try:
            with open(arquivo_audio, "rb") as audio:
                await update.message.reply_voice(voice=audio, caption="🎙️ Ouça isso...")
        except Exception as e:
            logger.error(f"Erro ao enviar áudio {arquivo_audio}: {e}")

async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia o processo de compra. Uso: /comprar <nome_pacote>"""
    args = context.args
    if not args:
        await update.message.reply_text("Qual pacote você quer? Uso: /comprar vip")
        return
    
    pacote = args[0].lower()
    if pacote not in PACOTES:
        await update.message.reply_text(f"Pacote não encontrado. Disponíveis: {', '.join(PACOTES.keys())}")
        return
    
    chat_id = update.effective_chat.id
    info = PACOTES[pacote]
    
    # Registra pedido pendente
    pedidos_pendentes[chat_id] = {
        "pacote": pacote,
        "status": "pendente",
        "chave_pix": info.get("pix_key", "chave-pix@exemplo.com"),
        "nome": info.get("nome", pacote)
    }
    
    texto = (
        f"💖 Você escolheu: **{info['nome']}** — {info['descricao']}\n"
        f"Valor: **R$ {info['preco']:.2f}**\n\n"
        f"💳 **Pague via PIX:**\n"
        f"Chave: `{info['pix_key']}`\n\n"
        f"Após o pagamento ser confirmado automaticamente, você receberá tudo aqui mesmo! 🔥"
    )
    await update.message.reply_text(texto)

# Ajuda
async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "🎙️ **Comandos da Ruby Fox:**\n"
        "/start — Iniciar\n"
        "/confirmar — Confirmar +18\n"
        "/comprar <pacote> — Comprar (vip, essencial)\n"
        "/pacotes — Ver pacotes disponíveis\n"
        "/status — Ver status do seu pedido\n\n"
        "💬 Fale comigo normalmente — se reconhecer uma palavra-chave, envio áudio!"
    )
    await update.message.reply_text(texto)

async def pacotes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista pacotes."""
    texto = "✨ **Pacotes Disponíveis:**\n"
    for chave, info in PACOTES.items():
        texto += f"• **{chave}**: {info['nome']} — {info['descricao']} — R$ {info['preco']:.2f}\n"
    await update.message.reply_text(texto)

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra status do pedido."""
    chat_id = update.effective_chat.id
    pedido = pedidos_pendentes.get(chat_id)
    if not pedido:
        await update.message.reply_text("Você ainda não fez um pedido. Use /comprar <pacote>")
        return
    texto = (
        f"📋 Pedido: {pedido['nome']}\n"
        f"Status: {pedido['status']}\n"
        f"PIX: {pedido['chave_pix']}"
    )
    await update.message.reply_text(texto)

# ============ WEBHOOK DE PAGAMENTO (FLASK) ============
app_flask = Flask(__name__)

@app_flask.route("/", methods=["GET"])
def index():
    return "Bot da Ruby Fox rodando. Webhook de pagamento ativo em /webhook/pagamento"

@app_flask.route("/webhook/pagamento", methods=["POST"])
def webhook_pagamento():
    """
    Recebe notificação de pagamento de um serviço externo (Asaas, Mercado Pago, etc.).
    Espera JSON com: { "chat_id": 123456, "pacote": "vip", "status": "pago" }
    """
    if not FLASK_AVAILABLE:
        return jsonify({"error": "Flask não disponível"}), 500
    
    try:
        dados = request.get_json(force=True)
        chat_id = dados.get("chat_id") or dados.get("user_id") or dados.get("id")
        pacote = dados.get("pacote")
        status = dados.get("status", "pago")
    except Exception as e:
        logger.error(f"Erro ao ler webhook: {e}")
        return jsonify({"erro": "JSON inválido"}), 400
    
    if not chat_id or not pacote:
        return jsonify({"erro": "chat_id e pacote são obrigatórios"}), 400
    
    chat_id = int(chat_id)
    
    if status == "pago" or status == "confirmado" or status == "aprovado":
        # Atualiza pedido
        pedidos_pendentes[chat_id] = pedidos_pendentes.get(chat_id, {
            "pacote": pacote,
            "status": "pendente",
            "nome": PACOTES.get(pacote, {}).get("nome", pacote)
        })
        pedidos_pendentes[chat_id]["status"] = "pago"
        
        # Envia arquivos automaticamente
        arquivos = listar_arquivos_pacote(pacote)
        
        logger.info(f"Pagamento confirmado para chat {chat_id}, pacote {pacote}. Liberando {len(arquivos)} arquivos.")
        
        # Se temos a aplicação Telegram, enviamos os arquivos
        # Nota: se estiver rodando polling, precisamos acessar a aplicação global
        # Para simplificar, vamos enviar uma mensagem via uma função auxiliar que usa requests (se necessário)
        # Mas o ideal é que o webhook tenha acesso ao bot Telegram ativo.
        
        # Tentamos enviar via API do Telegram diretamente com requests (simples)
        try:
            import requests
            token = TELEGRAM_TOKEN
            msg_inicial = f"🎉 **Pagamento confirmado!**\nVocê recebeu: **{PACOTES.get(pacote, {}).get('nome', pacote)}**\nAqui estão seus arquivos:"
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": msg_inicial}
            )
            
            for arquivo in arquivos:
                nome_arquivo = os.path.basename(arquivo)
                # Envia como documento
                with open(arquivo, "rb") as f:
                    files = {"document": f}
                    data = {"chat_id": chat_id, "caption": f"📁 {nome_arquivo}"}
                    requests.post(
                        f"https://api.telegram.org/bot{token}/sendDocument",
                        data=data, files=files
                    )
            
            # Envia mensagem final
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "🔥 Aproveite! Se quiser mais, fale comigo. 😈"
                }
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar arquivos pelo webhook: {e}")
            return jsonify({"erro": f"Erro ao enviar: {e}"}), 500
        
        return jsonify({"status": "liberado", "chat_id": chat_id, "pacote": pacote, "arquivos": len(arquivos)}), 200
    
    # Se não for pago
    pedidos_pendentes[chat_id]["status"] = status
    return jsonify({"status": status, "chat_id": chat_id}), 200

def rodar_flask():
    porta = int(os.getenv("PORT", 5000))
    logger.info(f"Iniciando webhook Flask na porta {porta}")
    app_flask.run(host="0.0.0.0", port=porta)

# ============ MAIN ============
def main():
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "SEU_TOKEN":
        logger.error("TELEGRAM_TOKEN não configurado! Configure no config.json ou variável de ambiente.")
        return
    
    if not TELEGRAM_AVAILABLE:
        logger.error("python-telegram-bot não está instalado.")
        return
    
    # Inicia webhook Flask em thread separada (para receber pagamentos automaticamente)
    if FLASK_AVAILABLE:
        thread = Thread(target=rodar_flask, daemon=True)
        thread.start()
        logger.info("Webhook de pagamento iniciado em background.")
    
    # Configura aplicação Telegram
    app_telegram = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Handlers
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(CommandHandler("confirmar", confirmar))
    app_telegram.add_handler(CommandHandler("comprar", comprar))
    app_telegram.add_handler(CommandHandler("pacotes", pacotes_cmd))
    app_telegram.add_handler(CommandHandler("status", status_cmd))
    app_telegram.add_handler(CommandHandler("ajuda", ajuda))
    
    # Mensagens normais
    app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot da Ruby Fox iniciado! Pressione Ctrl+C para parar.")
    
    # Se estiver no Render, você pode precisar de webhook, mas polling funciona para testes.
    # No Render, se o serviço for Web Service, polling pode ser interrompido após inatividade.
    # Para produção, prefira webhook. Aqui deixamos polling para simplicidade.
    app_telegram.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
