# Subir o bot no Render (Gratuito — 24h online)

Passo a passo simples:

1. Acesse render.com e crie uma conta gratuita
2. Clique em "New Web Service"
3. Escolha: "Deploy from GitHub" (se tiver) ou "Upload files"
4. Se subir manualmente:
   - Build Command: pip install -r requirements.txt
   - Start Command: python bot.py
5. Adicione as variáveis de ambiente:
   - TELEGRAM_TOKEN = seu token
   - ADMIN_ID = seu ID do Telegram
6. Clique em "Create Web Service"
7. O Render te dá uma URL: https://seu-app.onrender.com
8. Essa é a URL que você coloca no webhook do Mercado Pago

Nota: O Render derruba o serviço após 15 minutos de inatividade.
Para manter online, use UptimeRobot (gratuito) para pingar a URL a cada 5 minutos.
