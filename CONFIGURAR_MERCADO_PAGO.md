# Configurar Webhook no Mercado Pago (Mais Simples que Asaas)

Passo a passo:

1. Acesse o painel do Mercado Pago (https://www.mercadopago.com.br/developers)
2. Vá em "Suas integrações" → Crie uma integração se ainda não tiver
3. Na integração, vá em "Notificações" → "Webhooks"
4. Adicione a URL do seu bot:
   https://seu-app.onrender.com/webhook/pagamento
   (ou a URL que você usa no Render/ngrok)
5. Selecione os eventos:
   - "Pagamento confirmado" (payment.approved)
6. Salve e ative

Quando alguém pagar via PIX pelo Mercado Pago, 
eles enviam automaticamente uma notificação para essa URL.
O bot recebe e libera os arquivos.

Nota: Se você usa chave PIX simples (sem Mercado Pago), 
pode pular esse passo e usar o modo manual.
