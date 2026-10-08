# Publicar a versão web

1. Envie a pasta `docs/` e as alterações do README ao repositório.
2. No GitHub, abra **Settings → Pages**.
3. Em **Source**, escolha **Deploy from a branch**.
4. Escolha **main** e **/docs** e clique **Save**.
5. Aguarde a implantação do Pages. O link será `https://kilinel.github.io/ResultLigaAlsa/`.

Para testar localmente, na pasta do projeto execute `python -m http.server 8765 --directory docs` e abra `http://localhost:8765`. Pare o servidor com Ctrl+C.

A publicação é estática: sem backend, login ou token. Dados são armazenados no navegador, e o backup é um arquivo JSON. O arquivo `docs/PRIVACY.md` contém a política da versão web.

Testes de lógica: `node tests/web.cjs`.
