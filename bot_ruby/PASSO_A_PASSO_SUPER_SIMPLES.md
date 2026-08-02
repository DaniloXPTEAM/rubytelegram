# 🌸 Guia Super Simples — De Zero até o Bot Funcionar

Não precisa saber programar. Só seguir os passos na ordem.

---

## O que é esse "bot"?

É uma conta no Telegram que responde mensagens sozinha. Você fala com ela pelo celular, e ela manda texto, áudio, fotos e vídeos automaticamente — como se fosse você.

---

## PASSO 1 — Criar o bot no Telegram (5 minutos)

### No celular:
1. Abra o Telegram e procure por **@BotFather**
2. Mande: `/newbot`
3. Ele pergunta o nome. Escreva algo como: `Ruby Fox Oficial`
4. Ele pergunta o usuário (username). Tem que terminar com `bot`. Exemplo: `@Ruby FoxBotOficial`
5. Ele te dá um **TOKEN**. É uma linha de letras e números. **Copie e guarde** (não mostre para ninguém).

> Se você já fez isso antes e só não sabe onde está o token, mande `/token` para o @BotFather.

---

## PASSO 2 — Onde estão os arquivos do bot (já prontos)

No computador onde estamos, já existe uma pasta:

```
bot_ruby/
```

Dentro dela estão:
- `bot.py` → o bot
- `config.json` → onde você coloca seu token e configura os pacotes
- `audios/` → onde você coloca seus áudios
- `pacotes/` → onde você coloca as fotos e vídeos

---

## PASSO 3 — Colocar o token no arquivo

1. Abra o arquivo `config.json`
2. Onde está escrito `"COLOQUE_SEU_TOKEN_AQUI"`, apague e cole o token que o @BotFather te deu.
3. Onde está `"admin_id": 123456789`, você pode deixar assim por enquanto.
4. Salve o arquivo.

---

## PASSO 4 — Colocar seus áudios (seus arquivos de voz)

1. Abra a pasta `audios/`
2. Coloque seus arquivos de áudio lá. Os nomes devem combinar com as palavras do `config.json`.

**Exemplo simples:**
Se você tem um arquivo chamado `oi.mp3`, ele já está configurado no `config.json` para tocar quando alguém falar "oi".

Se você ainda não tem os arquivos, não se preocupe. O bot ainda funciona com texto. Os áudios são só um extra.

---

## PASSO 5 — Colocar os pacotes (fotos e vídeos)

1. Abra a pasta `pacotes/`
2. Dentro dela tem `essencial/` e `vip/`.
3. Coloque as fotos e vídeos de cada pacote dentro da pasta certa.

Exemplo:
```
pacotes/
  essencial/
    foto1.jpg
    foto2.jpg
  vip/
    foto1.jpg
    video.mp4
```

---

## PASSO 6 — Como fazer o bot funcionar agora

Você tem duas opções simples:

### Opção A — No seu computador (teste rápido)

1. Abra o terminal (aquele preto que aparece no computador)
2. Vá até a pasta:
   ```
   cd bot_ruby
   ```
3. Instale o que precisa (só uma vez):
   ```
   pip install -r requirements.txt
   ```
4. Rode:
   ```
   python bot.py
   ```
5. Se aparecer "Bot da Ruby Fox iniciado!", está funcionando.

### Opção B — No Render (fica 24h online, de graça)

Se você quer que o bot fique ligado o tempo todo sem o seu computador ficar aberto:

1. Acesse [render.com](https://render.com) e crie uma conta
2. Clique em "New Web Service"
3. Escolha a opção de subir arquivos (ou conecte ao GitHub se tiver)
4. Coloque:
   - Build: `pip install -r requirements.txt`
   - Start: `python bot.py`
5. Adicione as variáveis:
   - Nome: `TELEGRAM_TOKEN` | Valor: seu token
   - Nome: `ADMIN_ID` | Valor: seu ID do Telegram
6. Clique em criar.

---

## PASSO 7 — Como funciona o PIX (parte simples)

No arquivo `config.json`, você vê uma parte chamada `pacotes`. Cada pacote tem uma `pix_key`. Essa é a chave PIX que você vai mostrar para o cliente.

Exemplo:
```json
"pix_key": "sua-chave-pix-vip@pix.com"
```

Quando alguém digita `/comprar vip` no Telegram, o bot envia uma mensagem com essa chave e o valor. O cliente paga pelo celular.

Para a liberação automática funcionar, você precisa de um serviço que avisa quando o PIX caiu (como Asaas ou Mercado Pago). Se você ainda não tem isso, pode começar de forma manual: quando o cliente te avisa que pagou, você roda o arquivo `test_webhook.py` e o bot envia os arquivos automaticamente.

---

## PASSO 8 — Testar se está funcionando

1. Abra o Telegram
2. Procure pelo bot que você criou (o nome que você deu no @BotFather)
3. Mande uma mensagem: `oi`
4. Se você colocou um áudio `oi.mp3`, ele responde com texto e envia o áudio.
5. Se não colocou, ele responde só com texto. Isso é normal.

---

## Resumo do que você precisa fazer AGORA (em ordem):

- [ ] Criar o bot no @BotFather (se ainda não criou)
- [ ] Copiar o token para `config.json`
- [ ] Colocar seus áudios em `audios/` (se tiver)
- [ ] Colocar seus pacotes em `pacotes/`
- [ ] Rodar `python bot.py` no terminal
- [ ] Testar no Telegram

---

## Se travar em algum passo...

Me fala exatamente onde parou. Por exemplo:
- "Não sei onde está o @BotFather"
- "Não sei como abrir o terminal"
- "O bot não responde quando mando mensagem"
- "Não entendi como colocar a chave PIX"

Não precisa fazer tudo de uma vez. A gente faz um passo por vez.
