#!/usr/bin/env python3
"""
Simulador de Webhook de Pagamento
Use este script para testar se o bot libera os arquivos corretamente
sem precisar de um serviço de PIX real.
"""

import requests
import json

# Configurações de teste
URL = "http://localhost:5000/webhook/pagamento"
# Se estiver no Render, substitua por:
# URL = "https://seu-app.onrender.com/webhook/pagamento"

# Simule um pagamento para o pacote VIP
payload = {
    "chat_id": 123456789,   # Substitua pelo chat_id real de um usuário de teste
    "pacote": "vip",        # Ou "essencial"
    "status": "pago"
}

print(f"Enviando webhook para {URL}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    resposta = requests.post(URL, json=payload, timeout=30)
    print(f"Status: {resposta.status_code}")
    print(f"Resposta: {resposta.text}")
except Exception as e:
    print(f"Erro: {e}")
    print("Verifique se o bot está rodando e se a porta está exposta.")
