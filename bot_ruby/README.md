# 🤖 Bot da Ruby Fox — Agente Virtual com Áudio, PIX e Liberação Automática

Este projeto foi construído do zero com **ferramentas 100% gratuitas** para você configurar "aqui comigo". Nenhum código é de terceiro pago.

---

## 📁 Estrutura do Projeto

```
bot_ruby/
├── bot.py                 # Código principal do bot
├── requirements.txt        # Dependências Python
├── config.json             # Configuração do bot (você cria)
├── config_example.json     # Modelo de configuração
├── audios/                 # Seus arquivos de áudio (gatilhos)
│   └── README_AQUI_COLOQUE_OS_AUDIOS.txt
├── pacotes/
│   ├── essencial/          # Arquivos liberados após PIX (fotos)
│   │   └── COLOQUE_AQUI_AS_FOTOS.txt
│   └── vip/                # Arquivos do pacote VIP (fotos + vídeos)
│       └── COLOQUE_AQUI_AS_FOTOS_E_VIDEOS.txt
└── assets/                 # Outras imagens/vídeos se quiser
```

---

## ⚡ O que este bot faz?

1. **Recebe mensagens no Telegram** (texto)
2. **Responde com texto** automaticamente
3. **Detecta palavras-chave (gatilhos)** e envia **arquivos de áudio** do seu banco como se fosse você mandando
4. **Oferece pacotes via comando `/comprar`**
5. **Gera instrução de PIX** para pagamento
6. **Recebe notificação automática de pagamento** via webhook (`/webhook/pagamento`)
7. **Libera automaticamente** todos os arquivos (fotos/vídeos) do pacote assim que o PIX é confirmado

---

## 🛠 Passo a Passo Completo

### 1. Criar o Bot no Telegram

- Abra o Telegram e fale com `@BotFather`
- Envie `/newbot`
- Escolha nome (ex: *Ruby Fox Oficial*) e usuário terminando em `bot` (ex: `@Ruby FoxOficialBot`)
- Copie o **token** (ex: `123456:ABC-DEF...`)

---

### 2. Configurar o `config.json`

Copie o arquivo de exemplo:

```bash
cp config_example.json config.json
```

Edite `config.json` e preencha:

- `telegram_token`: o token do BotFather
- `admin_id`: seu ID numérico do Telegram (descubra enviando `/start` para `@userinfobot`)
- `audio_map`: mapa de **palavra-chave → arquivo**. Exemplo:
  ```json
  "oi": "audios/oi.mp3",
  "preco": "audios/preco.mp3",
  "pacote": "audios/pacote.mp3"
  ```
- `pacotes`: defina seus pacotes, preços e a **chave PIX** que será mostrada ao comprador
- `respostas_texto`: respostas de texto para cada gatilho

---

### 3. Colocar seus arquivos de áudio (gatilhos)

Na pasta `audios/`, coloque seus arquivos MP3/OGG. O nome do arquivo deve corresponder ao que você colocou no `audio_map`.

**Exemplo prático:**

Se você quer que quando alguém fale "oi" o bot envie um áudio seu dizendo "Oi, amor...", faça:

```
audios/
  oi.mp3
  preco.mp3
  pacote.mp3
  fotos.mp3
```

No `config.json`:

```json
"audio_map": {
  "oi": "audios/oi.mp3",
  "preco": "audios/preco.mp3",
  "pacote": "audios/pacote.mp3",
  "fotos": "audios/fotos.mp3"
}
```

> **Dica:** Se você não tem um arquivo para cada palavra, o bot ainda responde por texto. O áudio é um bônus quando o gatilho é detectado.

---

### 4. Colocar os arquivos dos pacotes (liberação automática)

Na pasta `pacotes/`, organize por nome do pacote:

```
pacotes/
  essencial/
    foto_01.jpg
    foto_02.jpg
    ...
    foto_10.jpg
  vip/
    foto_01.jpg
    ...
    foto_30.jpg
    video_01.mp4
    video_02.mp4
    audio_especial.mp3
```

Quando o pagamento for confirmado via webhook, o bot envia **todos os arquivos** daquela pasta automaticamente para o usuário no Telegram.

---

### 5. Configurar o PIX e o Webhook Automático

Este é o ponto mais importante para você. O bot precisa saber quando o pagamento caiu.

Você tem **duas opções gratuitas**:

#### Opção A — Usar um serviço de PIX com webhook (recomendado)

Serviços como **Asaas**, **Mercado Pago** ou **Pagar.me** permitem gerar cobranças PIX e enviam uma notificação (webhook) quando o pagamento é confirmado.

**Como configurar:**

1. Crie uma conta no serviço escolhido (Asaas tem plano gratuito)
2. Gere uma cobrança PIX para cada pacote (ou uma chave PIX fixa)
3. Configure o webhook no serviço para apontar para:
   `https://SEU-DOMINIO-RENDER.com/webhook/pagamento`
4. No painel do serviço, configure o corpo do webhook para enviar:
   ```json
   {
     "chat_id": "123456789",
     "pacote": "vip",
     "status": "pago"
   }
   ```

> **Nota:** Se você usa uma chave PIX fixa (ex: uma chave PIX pessoal ou de empresa), você pode criar um serviço simples que monitora notificações de PIX e chama o webhook. Alguns bancos oferecem notificações via webhook também.

#### Opção B — Verificação manual (teste)

Se ainda não tem o webhook configurado, você pode simular um pagamento chamando o webhook manualmente (via Postman, curl ou script):

```bash
curl -X POST https://localhost:5000/webhook/pagamento \
  -H "Content-Type: application/json" \
  -d '{"chat_id": 123456789, "pacote": "vip", "status": "pago"}'
```

Isso faz o bot enviar todos os arquivos do pacote `vip` imediatamente para o usuário de `chat_id` 123456789.

---

### 6. Instalar as dependências

```bash
pip install -r requirements.txt
```

---

### 7. Rodar o bot (local, para teste)

```bash
python bot.py
```

Você verá no terminal:
- `Bot da Ruby Fox iniciado!`
- `Webhook de pagamento iniciado em background.`

O bot estará rodando em modo **polling** (consulta o Telegram a cada segundo) e o webhook Flask estará disponível na porta 5000.

**Para testar o webhook localmente**, você pode expor a porta com **ngrok** (gratuito):

```bash
# Em outro terminal
ngrok http 5000
```

O ngrok te dará uma URL pública (ex: `https://abc123.ngrok.io`). Use essa URL + `/webhook/pagamento` no serviço de PIX.

---

### 8. Rodar no Render (24h, gratuito)

1. Acesse [Render.com](https://render.com)
2. Crie um novo **Web Service**
3. Conecte ao seu GitHub (faça upload dos arquivos) ou use o deploy manual
4. Configure:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
5. Adicione as variáveis de ambiente:
   - `TELEGRAM_TOKEN` = seu token
   - `ADMIN_ID` = seu ID
   - `PORT` = 10000 (ou qualquer porta que o Render exija)

> **Atenção:** O Render derruba serviços gratuitos após 15 minutos de inatividade. Para manter o bot online 24h, use um serviço como **UptimeRobot** (gratuito) para pingar a URL do seu serviço a cada 5 minutos.

Se você quiser que o webhook funcione no Render, o Render já expõe a URL pública (`https://seu-app.onrender.com`). Configure o serviço de PIX para apontar para:

`https://seu-app.onrender.com/webhook/pagamento`

---

## 💬 Como funciona a conversa?

### Fluxo normal:

1. Usuário: "Oi"
2. Bot (texto): "Oi, amor... 😈 Que bom te ver por aqui. Quer meus pacotes?"
3. Bot (áudio, se `audios/oi.mp3` existir): envia áudio como voice note

### Fluxo de compra:

1. Usuário: "/comprar vip"
2. Bot: envia instruções de PIX com chave e valor
3. Usuário paga via PIX
4. Serviço de PIX envia notificação para `/webhook/pagamento`
5. Bot confirma automaticamente e envia todos os arquivos de `pacotes/vip/`
6. Bot envia mensagem final: "🔥 Aproveite! Se quiser mais, fale comigo."

---

## 🔧 Configuração Avançada (Prompts)

Se você quiser que o bot responda com mais personalidade, edite a função `handle_message` no `bot.py`. A resposta atual é simples e direta. Se quiser integrar uma IA (como Gemini, que tem cota gratuita) para gerar respostas dinâmicas, me avise que adiciono no código.

---

## 📋 Checklist Final

- [ ] Bot criado no Telegram e token copiado
- [ ] `config.json` criado e preenchido com token, admin e pacotes
- [ ] Arquivos de áudio colocados em `audios/` e mapeados no `config.json`
- [ ] Arquivos dos pacotes colocados em `pacotes/essencial/` e `pacotes/vip/`
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Bot rodando (`python bot.py`)
- [ ] Webhook configurado no serviço de PIX (Asaas, Mercado Pago, etc.) apontando para `/webhook/pagamento`
- [ ] Teste realizado: `/comprar vip` → pagamento simulado → recebimento dos arquivos

---

## ❓ Precisa de ajuda?

Se você quiser:
- **Integrar uma IA (Gemini)** para responder de forma mais inteligente e sedutora
- **Usar voz gerada na hora** (ElevenLabs) além dos arquivos locais
- **Criar um banco de dados** para lembrar usuários e pedidos
- **Personalizar os gatilhos de áudio** com mais palavras-chave

Me avise que eu adapto o código diretamente aqui. Este é o seu agente, construído do zero, com suas regras.
