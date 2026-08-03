# Corrigir o erro do Render (requirements.txt não encontrado)

O arquivo requirements.txt existe no computador.
Se o Render não encontrou, é porque ele não está no GitHub.

Como corrigir no GitHub:
1. Acesse github.com e vá no seu repositório
2. Clique em "Add file" → "Upload files"
3. Selecione todos os arquivos da pasta bot_ruby no computador:
   - bot.py
   - requirements.txt
   - config.json
   - audios/
   - pacotes/
4. Clique em "Commit changes"

Depois disso, o Render vai encontrar o arquivo quando você fizer deploy.
