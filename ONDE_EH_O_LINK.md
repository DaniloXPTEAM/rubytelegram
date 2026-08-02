# Onde achar o link do webhook?

Se você rodar o bot no computador (python bot.py):
1. Abra outro terminal
2. Digite: ngrok http 5000
3. O ngrok mostra uma linha: Forwarding https://xxxx.ngrok.io → http://localhost:5000
4. Copie esse link (xxxx.ngrok.io) e adicione /webhook/pagamento

Se você subir no Render:
1. Acesse render.com
2. Seu serviço tem uma URL: https://seu-bot.onrender.com
3. Use essa URL + /webhook/pagamento

Você está rodando o bot agora no computador?
Se sim, posso te ajudar a instalar o ngrok.
Se não, me fala quando subir no Render que te passo a URL exata.
