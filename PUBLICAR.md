# Colocar o projeto no GitHub

1. Crie um repositório público chamado `resultado-da-liga-alsa` na sua conta.
2. Extraia o ZIP do projeto. Envie o conteúdo da pasta do projeto para a raiz do repositório, incluindo `.github/workflows/windows.yml` e `.gitignore` (arquivos ocultos).
3. Não envie `preferencias.json`: ele é seu cadastro pessoal. O pacote público não inclui esse arquivo.
4. Abra **Actions → Aplicativo Windows → Run workflow** para fazer a primeira compilação.
5. Para criar o download público, abra **Releases → Draft a new release**, crie a tag `v1.0.0` na branch principal e publique a Release. Aguarde o fluxo terminar: ele anexará `ResultadoDaLigaALSA.exe`.
6. Compartilhe a página de Releases com o pessoal da liga.

Alternativa: use GitHub Desktop para publicar a pasta. Ele também inclui os arquivos ocultos e facilita futuras atualizações.

## Mensagem para divulgar no Discord

> 🏆 **Resultado da Liga ALSA**
>
> Fizemos um app para facilitar os resultados da Azure Latch South America League!
> Escolha **Amistoso** ou **Ranked / Detalhe**, salve seus jogadores e times e selecione os pings sem precisar copiar tudo de novo.
> No Ranked, dá para informar os sets e as stats dos dois times: gols, assists, defesas/desarmes e saves.
> Depois é só clicar em **Copiar mensagem** e colar aqui no Discord.
>
> **Download para Windows:** [cole o link da página Releases]
> Código público no GitHub. Não precisa de Python ou arquivo .bat.

Use essa mensagem depois que o executável estiver disponível na Release.
