<p align="center">
  <img src="assets/logo-github.png" alt="ALSA Match Results" width="420">
</p>

# Resultado da Liga ALSA

**Azure Latch South America League** — gere resultados de partidas prontos para colar no Discord.

Um aplicativo para Windows com interface escura, cadastros locais e dois modos: **Amistoso** e **Ranked / Detalhe**.

Tipografia: **Inter** na interface e **JetBrains Mono** na prévia. As fontes acompanham o aplicativo, com suas licenças SIL OFL, e são carregadas apenas para o processo. No Tkinter, o fallback usa as fontes do sistema (Segoe UI e Consolas no Windows), equivalente ao papel de `system-ui` e `ui-monospace` em CSS.

Fontes originais: [Inter](https://github.com/rsms/inter) e [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono). Licenças incluídas em `assets/fonts/`.

## Para quem joga na liga

1. Abra a seção **Releases** deste repositório.
2. Baixe `ResultadoDaLigaALSA.exe` da versão mais recente.
3. Abra o aplicativo, selecione o modo e preencha a partida.
4. Clique em **Copiar mensagem para o Discord** e cole no canal da liga.

O executável é gerado pelo GitHub Actions. Não exige Python, instalação ou arquivo `.bat`. As versões só ficam disponíveis depois que o fluxo de compilação termina com sucesso.

## Dois modos

| Amistoso | Ranked / Detalhe |
| --- | --- |
| Placar direto e vencedor automático | Melhor de 3 com resultado calculado pelos sets |
| MOTM, MVP, MVA, MVD e GK | MVP de cada set e destaques da série |
| Emojis, pings e HMs | Stats dos dois times, reservas, posições e REFS |
| Template original MATCH RESULT | Template RESULTADOS DA RANKED |

Em Ranked, preencha os sets em ordem. Quem vence dois sets ganha; em 2–0, deixe o terceiro set vazio. Estatísticas são totais da série preenchidos por você: **G** gols, **A** assistências, **D** defesas/desarmes e **S** saves. O aplicativo não coleta dados do jogo.

## Salve jogadores e cargos uma vez

Na aba **Jogadores e cargos**, informe um nome e o ID do Discord. O aplicativo transforma o ID em `<@ID>` para jogador ou `<@&ID>` para cargo. Depois basta selecionar o nome nos campos da partida.

Os dados ficam em `%APPDATA%\ResultadoDaLiga\preferencias.json`. Trocar o executável não apaga os cadastros. Para migrar da versão antiga, clique em **Importar cadastros da versão anterior** e escolha seu `preferencias.json`. O arquivo pessoal não deve ser enviado para o GitHub.

## Privacidade e distribuição

O app funciona localmente, sem login, token de bot, webhook ou envio automático. Copia a mensagem para sua área de transferência; você escolhe onde colar. Emojis personalizados precisam existir no servidor do Discord. Mensagens extensas podem precisar ser enviadas em partes.

O executável não possui assinatura digital. O código e o processo de compilação ficam públicos para inspeção. Este é um aplicativo comunitário; não representa o Discord ou os desenvolvedores de Azure Latch.

## Executar o código

Requer Python 3.12 com Tcl/Tk:

```sh
python resultado_app.py
```

Não há dependências externas para rodar o código.

## Gerar o .exe pelo GitHub

Em **Actions → Aplicativo Windows → Run workflow**, execute o fluxo. Quando terminar, baixe o artefato `ResultadoDaLigaALSA-Windows`.

Para publicar uma versão com download direto em Releases, crie uma tag `v1.0.0` (ou outra versão). O fluxo testa o app, compila o executável e anexa o arquivo à Release.

Também é possível compilar em um Windows com Python:

```sh
python -m pip install -r requirements-build.txt
python -m unittest discover -s tests -v
python -m PyInstaller --noconfirm --clean --onefile --windowed --icon assets/app.ico --add-data "assets;assets" --name ResultadoDaLigaALSA resultado_app.py
```

O arquivo final estará em `dist/ResultadoDaLigaALSA.exe`.
