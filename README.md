<p align="center">
  <img src="assets/logo-github.png" alt="ALSA Match Results" width="420">
</p>

# ALSA Match Results

Organize os resultados das suas partidas de Azure Latch e monte uma mensagem pronta para publicar no Discord, em poucos cliques.

O **Match Results ALSA** é um aplicativo gratuito para Windows feito por [kilinel](https://github.com/kilinel). Ele facilita o registro de amistosos, scrims e ranked, sem precisar montar a mensagem inteira à mão.

## O que você pode fazer

| Recurso | Como ajuda |
| --- | --- |
| **Amistoso** | Informe os times e o placar para gerar o resultado de amistosos e scrims. |
| **Ranked / Detalhe** | Registre até cinco partidas; quem vencer três ganha a série. |
| **Stats dos dois times** | Preencha gols, assistências, defesas/desarmes e saves, com posição, personagem e reservas. |
| **Stats por partida** | Preencha cada partida e deixe o aplicativo somar os totais por jogador, ou informe os totais diretamente. |
| **Destaques** | Inclua MOTM, MVP, MVA, MVD, GK, árbitro e HMs. |
| **Jogadores e cargos salvos** | Cadastre os IDs do Discord uma vez e selecione os nomes nas próximas partidas. |
| **Templates personalizados** | Salve um formato para Amistoso e outro para Ranked, incluindo as linhas de stats. |
| **Prévia editável** | Confira e ajuste a mensagem antes de copiar para o Discord. |

O app organiza as informações que você preenche. Ao clicar em **Copiar mensagem**, basta colar no canal da liga com **Ctrl+V**. A ajuda dentro do aplicativo explica como obter os IDs para mencionar jogadores e cargos.

## Versão web — sem instalação

A versão web está hospedada pelo GitHub Pages. Tem Amistoso, Ranked, cadastros, stats dos dois times, templates e prévia editável. Os dados ficam no navegador; **Exportar JSON** cria um backup e **Importar JSON** permite levá-lo a outro dispositivo ou carregar as preferências desktop.

para acessar basta entrar no link: https://kilinel.github.io/ResultLigaAlsa/ 

Na versão web, limpar os dados do site pode apagar o cadastro. Guarde um JSON de backup. Consulte a [privacidade da versão web](docs/PRIVACY.md).

## Alternativa: Versão Python - Como instalar e abrir

### 1. Instale o Python — somente na primeira vez

Python é o programa que executa esta versão do aplicativo.

1. Acesse o [site oficial do Python para Windows](https://www.python.org/downloads/windows/).
2. Baixe o **Python install manager** e siga as instruções de instalação.
3. Abra o menu Iniciar, procure **Terminal** e abra.
4. Cole este comando, pressione **Enter** e aguarde:

```powershell
py install 3.12
```

Se você já tem Python 3.12 ou mais recente com Tkinter instalado, pode passar para a próxima etapa. O guia [COMECE-AQUI.txt](COMECE-AQUI.txt) inclui a verificação da instalação e ajuda para dificuldades comuns.

### 2. Baixe o aplicativo

Na página de [Releases](https://github.com/kilinel/ResultLigaAlsa/releases), procure o pacote **ALSA-Python** nos arquivos da versão. Se ele ainda não estiver disponível, use **Code → Download ZIP** na página principal do repositório.

Clique com o botão direito no ZIP e escolha **Extrair Tudo**. Abra a pasta extraída e mantenha os arquivos juntos, incluindo a pasta `assets`.

### 3. Abra e use

Dê dois cliques em **Abrir-ALSA.bat**. Uma janela de terminal pode ficar aberta junto com o aplicativo; isso é normal.

Escolha **Amistoso** ou **Ranked / Detalhe**, preencha a partida, confira a prévia e clique em **Copiar mensagem**. Depois, cole no Discord.

Também é possível abrir diretamente pelo código Python. Na pasta extraída, clique na barra de endereço do Explorador de Arquivos, digite `powershell` e pressione Enter. Execute:

```powershell
py -3.12 resultado_app.py
```

Se sua instalação usa o comando `python`, execute `python resultado_app.py`.

### Alternativa: exe para Windows

Quando disponível na Release, **ResultadoDaLigaALSA.exe** abre o aplicativo sem precisar instalar Python. Essa opção pode exibir o aviso do SmartScreen explicado abaixo.

## Sobre as versões Python, BAT e EXE

O aplicativo é escrito em Python. O **BAT é um atalho de abertura**: ele procura uma instalação compatível do Python e executa o mesmo arquivo `resultado_app.py` que está neste repositório. Não instala programas, não baixa dependências e não altera as proteções do Windows.

Essa opção facilita abrir o código diretamente, sem depender do executável empacotado. Nos testes no computador do autor, tanto o BAT quanto a execução pelo Python abriram sem aviso do SmartScreen. O comportamento pode variar conforme as configurações de outros computadores.

O **EXE ainda não possui assinatura digital**. Por isso, o Windows pode apresentar “O Windows protegeu o computador” ao abrir o arquivo baixado. O SmartScreen considera a reputação do arquivo e do editor; esse aviso não é, por si só, uma detecção específica de vírus. Não é necessário desativar o antivírus para usar a versão Python.

O código usado pelo app está disponível em [resultado_app.py](resultado_app.py). A criação do EXE é automatizada pelo **GitHub Actions**: o [workflow](.github/workflows/windows.yml) executa os testes, gera o aplicativo e anexa o resultado às Releases criadas por tags. Quem quiser conferir pode consultar o código da versão e os registros em [Actions](https://github.com/kilinel/ResultLigaAlsa/actions), ou executar o fonte diretamente.

## Privacidade e dados salvos

O app funciona localmente, sem login do Discord, token de bot, webhook ou envio automático de mensagens. Ao copiar um resultado, o texto vai para a área de transferência do seu computador; você escolhe onde colar.

Jogadores, cargos, templates e preferências ficam em `%APPDATA%\ResultadoDaLiga`. Você pode abrir essa pasta pelo botão em **Cadastros**. As versões Python e EXE usam os mesmos dados, e trocar os arquivos do aplicativo preserva os cadastros.

Os dados da partida e os ajustes pontuais da prévia não ficam salvos ao fechar. Para conhecer os detalhes de armazenamento e exclusão, consulte a [Política de Privacidade](PRIVACY.md).

## Atualizações

Consulte o [histórico de alterações](CHANGELOG.md) para saber o que mudou em cada versão e a página de [Releases](https://github.com/kilinel/ResultLigaAlsa/releases) para os downloads disponíveis.

## Problemas e sugestões

Encontrou um problema ou tem uma ideia? Abra uma [Issue](https://github.com/kilinel/ResultLigaAlsa/issues). Informe a versão do app e explique o que aconteceu; screenshots e passos para reproduzir ajudam. Evite incluir informações pessoais, pois as Issues são públicas.

## Autoria e licença

Criado por **[kilinel](https://github.com/kilinel)** e distribuído sob a [licença MIT](LICENSE).

Este é um projeto independente para a comunidade. Não é um aplicativo oficial da liga ALSA, do Discord ou dos desenvolvedores de Azure Latch.

