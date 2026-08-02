# Configurar Webhook Automático (Asaas — Gratuito)

1. Crie conta em asaas.com (gratuito)
2. Vá em "Integrações" → "Webhooks"
3. Adicione a URL: https://SEU-DOMINIO.onrender.com/webhook/pagamento
4. Selecione os eventos: "Pagamento confirmado"
5. No painel, crie uma cobrança PIX para cada pacote
6. Quando o cliente pagar, o Asaas avisa o bot automaticamente

Se você preferir começar sem isso:
- Use uma chave PIX simples no bot
- Quando o cliente te avisar que pagou, você roda:
  python test_webhook.py
- O bot libera os arquivos na mesma hora
