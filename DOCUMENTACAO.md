# RetalhosApp — Documentação Técnica (v2.0)

Sistema desktop (Windows) para **controle de estoque de retalhos de chapas de MDF** integrado ao **Corte Certo Plus**. Ele:

- registra os retalhos num banco Access;
- mantém sincronizados os arquivos de retalho (`RETxxxxx.TAB`) que o Corte Certo usa;
- reserva retalhos por projeto e gera a planilha `PRJ_<projeto>.xlsx`;
- importa sobras a partir de planos de corte `.cutplanning`;
- dá baixa nos retalhos consumidos;
- atualiza a si mesmo a partir de um pacote na rede.

| | |
|---|---|
| Linguagem | Python 3.12 |
| Interface | PySide6 (Qt 6), telas construídas em código com tema próprio |
| Banco | Microsoft Access (`.accdb`) via `pyodbc`; SQLite para testes e desenvolvimento |
| Empacotamento | PyInstaller: `Retalhos.exe` (pasta) e `Update.exe` (arquivo único) |
| Instalador | Inno Setup 6: `instalador\Retalhos.iss`, gerado por `ferramentas\gerar_instalador.bat` → `dist\instalador\Retalhos_Setup_<versão>.exe` |
| Testes | pytest (rodam em SQLite e, opcionalmente, em Access real) |

---

## 1. Estrutura

```
RetalhosApp/
├── main.py                     # Entrada do Retalhos.exe
├── updater.py                  # Entrada do Update.exe
├── Settings.json               # Configuração (mesmo formato da v1)
├── Retalhos.spec / Update.spec # PyInstaller
├── requirements.txt            # Dependências de execução
├── requirements-dev.txt        # + pytest e pyinstaller
├── codigo para compilar EXE.txt# Passo a passo de build e distribuição
│
├── retalhos/                   # Código do aplicativo
│   ├── __init__.py             # Versão e nome do app
│   ├── paths.py                # Pasta do app, recursos (funciona empacotado), pasta de log
│   ├── config.py               # Settings: leitura/gravação do Settings.json
│   ├── models.py               # Chapa, Retalho, Sobra + conversões
│   ├── app.py                  # Inicialização: log, tema, tratamento global de erros
│   ├── updater_app.py          # Janela do atualizador (Update.exe)
│   │
│   ├── db/
│   │   ├── database.py         # Database/Session: conexão Access ou SQLite, transações
│   │   └── repositories.py     # ChapaRepository, RetalhoRepository (SQL parametrizado)
│   │
│   ├── services/               # Regras de negócio, sem nada de interface
│   │   ├── corte_certo.py      # Arquivos RET/PED do Corte Certo
│   │   ├── etiquetas.py        # Código de barras e leitura de .cutplanning
│   │   ├── estoque.py          # EstoqueService: retalhos, materiais, reservas, baixa
│   │   ├── consumo.py          # Consumo de chapas/retalhos de planos de corte (compras)
│   │   ├── capa_lote.py        # Capa do lote (novo layout do LOTE.xlsm), gerada pelo sistema
│   │   └── atualizacao.py      # Verificar, extrair e registrar a atualização
│   │
│   ├── ui/
│   │   ├── theme.py            # Temas claro/escuro (paletas) e folha de estilo
│   │   ├── widgets.py          # Mensagens, botões, tabela (modelo/filtro), BaseDialog, Worker
│   │   ├── columns.py          # Colunas e cores das tabelas de retalhos
│   │   ├── main_window.py      # Janela principal
│   │   └── dialogs/            # Configurações, Novo retalho, Materiais, Cadastro de cores,
│   │                           # Reserva, Baixa e Leitor de plano de corte
│   └── resources/              # Ícones
│
├── tests/                      # Testes automatizados
├── ferramentas/                # gerar_icone.py e gerar_instalador.bat
└── instalador/                 # Retalhos.iss (Inno Setup) e Settings.padrao.json
```

**Camadas.** A interface (`ui`) chama os serviços (`services`). Os serviços usam os repositórios (`db`) e os arquivos do Corte Certo. Nenhum serviço importa Qt, então as regras podem ser testadas sem abrir telas.

---

## 2. Configuração — `Settings.json`

O arquivo é procurado **ao lado do executável** e, se não estiver lá, na pasta atual. Na primeira execução sem o arquivo, a tela de Configurações abre para criá-lo. As chaves são as mesmas da v1, e chaves desconhecidas são preservadas ao salvar.

| Chave | Atributo (`Settings`) | Uso |
|---|---|---|
| `Directory_data_base` | `database_path` | Caminho do `.accdb` (`.db`/`.sqlite` abre como SQLite) |
| `Directory_cc` | `corte_certo_dir` | Pasta raiz do Corte Certo |
| `ret` / `ped` / `mat` | `ret_subdir` / `ped_subdir` / `mat_subdir` | Subpastas (`CHP\`, `PED\`, `MAT\`) |
| `Corte_certo` | `corte_certo_exe` | Executável usado para verificar a instalação |
| `UltimoLogin` | `last_login` | Último usuário que entrou nesta máquina (vem preenchido na tela de login) |
| ~~`User`, `Menu`, `Remover`, `ReservarManual`~~ | — | **Não são mais usadas.** Usuário e permissões vêm do login (`tblUsuarios`, seção 6.1). Podem ser apagadas do JSON |
| `Password` | `database_password` | Senha do Access (usada em **todas** as conexões) |
| `Largura` / `Altura` | `max_width` / `max_height` | Medida máxima (chapa inteira) |
| `Largura_min` / `Altura_min` | `min_width` / `min_height` | Medida mínima de um retalho |
| `local_zip` | `update_zip` | Pacote de atualização `Retalhos.zip` |
| `Projeto gerado` | `projects_dir` | Pasta dos lotes gerados (verifica se o corte do projeto já foi gerado) |
| `Sheet_proj` | `sheets_dir` | Pasta das planilhas `PRJ_*.xlsx` (criada se não existir) |
| `ultima_att` | `last_update` | Data do pacote instalado (`dd/mm/aaaa hh:mm:ss`) |
| `ConFolhaLote` | `conf_folha_lote` | Planilha com os projetos do lote (padrão `\\GDD02\sistema\ConFolhaLote.xlsx`), usada na capa do lote |
| `AtualizarMinutos` | `auto_refresh_minutes` | Intervalo da atualização automática da lista principal (padrão `3`; `0` desliga) |
| `Tema` | `theme` | `Claro`, `Escuro` ou `Automático` (segue o Windows); gravado ao trocar o tema no app |

---

## 3. Banco de dados

**`tblChapas`** guarda os materiais: `COD`, `MM` (espessura), `MDF` (descrição) e `Ativo`.

**`tblUsuarios`** guarda os usuários do sistema (seção 6.1).

**`tblRetalhos`** guarda os retalhos: `id` (autonumeração), `Setor`, `Cod_Material`, `Largura`, `Altura`, `DataEntrada`, `Reserva`, `DataReserva`, `Responsavel` (quem lançou), **`ResponsavelReserva`** (quem reservou), **`DataBaixa`/`ResponsavelBaixa`** e **`DataExclusao`/`ResponsavelExclusao`**.

**Controles: quem fez o quê e quando**

| Ação | Onde fica registrado |
|---|---|
| Lançamento | `Responsavel` + `DataEntrada` e histórico (LANÇAMENTO / SOBRA LANÇADA) |
| Reserva (pedido, plano de corte ou manual) | `ResponsavelReserva` + `DataReserva` e histórico (RESERVA, com a origem) |
| Liberar / desfazer reserva | Histórico (LIBERAÇÃO / CANCELAMENTO), com de quem era a reserva |
| Baixa (consumo) | `DataBaixa` + `ResponsavelBaixa` e histórico (BAIXA) |
| Excluir | `DataExclusao` + `ResponsavelExclusao` e histórico (EXCLUSÃO). **Não apaga mais** |
| Restaurar (administrador) | Limpa baixa/exclusão e reserva; histórico (RESTAURAÇÃO, com o que era e quem tinha removido) |

**Retalhos removidos** (Produção › Retalhos removidos):
- Consulta sempre **por material**: a lista de materiais mostra só os que têm removidos, com a quantidade. Nada é listado antes de escolher.
- Filtros por motivo (Baixas/Exclusões) e por texto. Mostra data/hora, responsável, projeto da baixa e quem lançou.
- **Histórico…** (ou duplo clique) abre a movimentação completa do retalho, e **Exportar Excel…** salva o que está na tela.
- **Restaurar ao estoque** aparece só para administradores. O retalho volta **disponível** (sem reserva) e é incluído de novo no `RET` do Corte Certo. A data de lançamento e quem lançou continuam os originais.

**`tblHistorico`**: `id`, `RetalhoId`, `Acao`, `DataHora`, `Usuario`, `Detalhe`. Cada ação é gravada na **mesma transação** da alteração, então vale tudo ou nada. Na tela principal, o botão **Histórico** (`Ctrl+H`) mostra a movimentação do retalho selecionado, e a coluna **Reservado por** mostra quem fez a reserva atual.

**Baixa registrada (consumo):**
- A baixa **não apaga** o retalho: grava `DataBaixa` (data e hora) e `ResponsavelBaixa` (usuário logado).
- Todo o sistema só enxerga retalhos com `DataBaixa` **e** `DataExclusao` vazias: listas, reservas, consumo do plano, capa e arquivos RET. O registro fica no banco para consulta.
- As colunas novas e a `tblHistorico` são criadas automaticamente na primeira abertura da versão nova (`EstoqueService.preparar_banco`). Antes de alterar um banco Access, o app guarda uma cópia em `%LOCALAPPDATA%\Retalhos\backups`. A migração só **acrescenta** colunas vazias.

- Todo SQL usa parâmetros `?`.
- Cada operação roda numa **transação**: se a gravação do arquivo `.TAB` falhar, o registro no banco é desfeito.
- O ID do registro inserido vem de `SELECT @@IDENTITY` na mesma conexão (sem risco de pegar o ID de outra máquina).
- Retalho **disponível** é aquele com `Reserva` vazio ou nulo.

---

## 4. Arquivos do Corte Certo (`services/corte_certo.py`)

### `RETxxxxx.TAB` — um arquivo por material

O nome é `RET` + código com 5 dígitos + `.TAB`. Cada linha é CSV:

```
<id>,+,1,<largura>,<altura>,<reserva ou espaço>,<id>,
```

A coluna 6 (id) identifica a linha. Toda gravação é feita em arquivo temporário e depois substituída, para não deixar o arquivo pela metade. Adicionar um retalho nunca duplica o id.

### `PEDxxxxx.TAB` — pedido do projeto

Campos separados por espaço; a coluna 5 traz o código do material. O arquivo é **somente lido**. Na v1 ele era regravado para remover espaços duplos.

### Código de barras (21 caracteres)

`[0:7]` é o código do material, `[8:14]` a largura e `[14:21]` a altura.

### `.cutplanning`

XML do plano de corte. As sobras são os campos `...cut.data.field` com `name="160"` e valor de 21 caracteres.

### 4.1 Consumo de material (`services/consumo.py`)

No `.cutplanning`, cada `material` (atributo `id` = `tblChapas.COD`) tem vários `program`, e cada programa é um plano de corte executado `quantity` vezes:

| `iswaste` | Significado | Medidas |
|---|---|---|
| `false` | Corte em **chapa inteira** do estoque, que entra na contagem de compras | `lenght` × `width` = medida da chapa (ex.: 2740 × 1840) |
| `true` | Corte em **retalho** | `lenght` × `width` = medidas do retalho, as mesmas do `RET` |

Chapas de material **sem cadastro em `tblChapas`** (ex.: "MDF Retalho 6mm/15mm") **não entram** na lista de compras nem na capa. Elas aparecem num aviso ("Ignoradas") na tela, no Excel e no texto copiado.

**Projetos do plano (lote com vários projetos).** Um `.cutplanning` pode ter peças de vários projetos. O projeto de cada peça vem da etiqueta (template 1):

| Campo | Conteúdo | Exemplo |
|---|---|---|
| 172 | imagem da peça, com o projeto após `PLA` | `projects/DEBORA_BRUDNA-images/\PLA13825_00167.bmp` |
| 184 | cliente | `DEBORA BRUDNA` |
| 187 | pedido e ambiente | `5293 - DORMITORIO CASAL` |

- Cada chapa e cada retalho recebe os projetos com peças nele; um retalho compartilhado aparece como `13825, 13826`.
- Só se nenhuma peça tiver a imagem, o projeto vem do número no início do nome do arquivo.

O arquivo **não traz o ID do retalho**. Por isso o sistema o identifica no estoque por material e medidas (tolerância de 0,05 mm, aceitando medidas invertidas). Cada retalho do estoque só é atribuído uma vez, nesta prioridade:

1. reservado para o projeto do arquivo (número no início do nome, ex.: `13825_...`);
2. disponível;
3. reservado para outro projeto (aviso em laranja).

Se nada casar, a linha aparece como *Não encontrado no estoque* (vermelho). Em geral isso significa que o retalho já recebeu baixa ou que o plano é antigo.

### 4.2 Capa do lote (`services/capa_lote.py`)

É um `.xlsx` **sem macros, fórmulas ou vínculos externos**, em A4 retrato e pronto para imprimir. É gerado pela tela de Consumo com o que o sistema produz:

| Bloco | Origem |
|---|---|
| Lote e projetos (pedido, ambiente, cliente, entrega) | Todos os projetos do plano (sem limite). Dados do `ConFolhaLote.xlsx` quando o projeto está lá; senão, das etiquetas do plano (sem a data de entrega). O número do lote só é sugerido se algum projeto estiver no `ConFolhaLote` |
| Chapas inteiras (lista: material, espessura, medida, quantidade e total; aceita qualquer espessura) | Análise do plano de corte |
| Retalhos (setor, espessura, material, medida, projeto), um por linha | Análise do plano de corte; o não encontrado no estoque sai em vermelho |
| Observações | Digitadas ao gerar a capa |
| Controle de produção | Uma linha por projeto (18 pt; 16 pt no compacto), na frente |
| Controle de montagem | Um cartão por projeto, na aba **Verso** |

**Impressão frente e verso (medidas para não quebrar página)**

- A pasta tem duas abas, **Frente** e **Verso**, e cada uma é ajustada para caber em **exatamente 1 página A4** (`fitToHeight=1`). Por isso a montagem sempre cai no verso da folha.
- **Densidade automática**: o sistema calcula a altura do conteúdo. Se a face não couber no tamanho normal, ela é refeita no **modo compacto** (linhas e espaços menores; no verso, cartões compactos). Só depois disso o Excel reduz a escala.
- **Retalhos**: uma linha por retalho, sem coluna Qtd (cada retalho é único). A coluna Setor é estreita (setores de 1 a 20) e o espaço vai para **Material**, por causa dos nomes longos de MDF. Retalho não encontrado no estoque sai com setor "—", em vermelho, e com uma legenda.
- Se a escala estimada ficar abaixo de **70%**, o app avisa antes de gerar (`ESCALA_MINIMA_LEGIVEL`).
- Junto com o `.xlsx`, o app gera um **PDF** (página 1 = frente, página 2 = verso) pelo Excel instalado; é o jeito seguro de imprimir em duplex. Pelo Excel, é preciso usar "Imprimir Pasta de Trabalho Inteira".

### 4.3 Reserva a partir do plano de corte (`EstoqueService.reservar_do_plano`)

- **Um projeto por retalho:** um retalho usado por vários projetos do lote (`13956, 13958`) fica reservado para o **primeiro** (ordem numérica).
- **Medidas repetidas:** cada ocorrência no plano consome um retalho diferente do estoque. Se o plano usa 3 retalhos de 700 × 600 e há 2, os 2 são reservados e o 3º sai como "não encontrado".
- **Ao reservar:**
  - grava `Reserva` e `DataReserva`;
  - remove a linha do `RETxxxxx.TAB`, para outra otimização não escolher o mesmo retalho.
- **Conferência no banco no momento de gravar:**
  - retalho já reservado para um projeto do lote fica como está, então processar o mesmo plano de novo não duplica nada;
  - retalho reservado para outro projeto (inclusive por outra máquina depois da análise) **não é tomado** e é listado como conflito.
- Esse fluxo não gera `PRJ_<projeto>.xlsx`, porque a capa do lote cobre isso. A tela **Reserva por projeto** (pelo `PED`) continua disponível para exceções.

### 4.4 Sobras entre projetos do mesmo lote (cores)

Quando a sobra de um projeto do lote é usada no projeto seguinte, carregue os planos desses projetos juntos na tela de Consumo.

- **Sobras de cada plano:** vêm das etiquetas de sobra (template 2, campo 160).
- **Origem do retalho:** um retalho usado num plano que bate em **material + medida** (inclusive com a medida invertida) com uma sobra gerada por **outro** plano carregado recebe a origem daquele projeto. Cada sobra só é casada uma vez.
- **Retalho com setor nunca é sobra.** Se o retalho identificado no estoque tem setor, é um retalho guardado, mesmo com a medida igual a uma sobra. Nesse caso a sobra **não é consumida** e fica para outra ocorrência da mesma medida. Sobras lançadas pelo Leitor XML entram sem setor, então continuam sendo reconhecidas.
- **Uma cor por passagem (origem → destino)**, na ordem: AMARELO, VERDE, AZUL, LARANJA, LILÁS, ROSA, CINZA. As cores ficam em `CORES_SOBRAS`, no bloco de cores da capa.
  - **Capa:** a linha do retalho sai na cor da passagem. O significado das cores aparece **somente nas Observações**, que começam com "Retalho AMARELO: sobra do projeto X p/ Y" (uma linha por passagem); o texto é editável antes de gerar.
  - **Tela de Consumo:** mesmas cores (com tons escuros no tema escuro) e legenda no rodapé.
  - **Excel:** coluna "Sobra do projeto".

### `PRJ_<projeto>.xlsx`

Mesmo layout de colunas da v1: Setor, MM, MDF, 4 colunas vazias, Largura, `x`, Altura, Projeto, Responsável e Data de entrada.

---

## 5. Regras de negócio (`services/estoque.py` — `EstoqueService`)

| Método | O que faz |
|---|---|
| `listar_retalhos()` | Retalhos com dados do material |
| `lancar_retalho(cod, larg, alt, setor)` | Valida limites e material, grava no banco e no `RET` |
| `excluir_retalho(r)` | Recusa se reservado; remove do banco e do `RET` |
| `liberar_reserva(r)` | Exige `Remover=Ativado`; limpa **só** a reserva (Reserva e DataReserva) e devolve ao `RET`. Data de lançamento e responsável **não mudam** |
| `retalhos_para_projeto(proj)` | Materiais do `PED` → retalhos livres ou já reservados para o projeto |
| `corte_gerado(proj)` | Existe pasta em `Projeto gerado` começando com o número do projeto? |
| `reservar(proj, retalhos)` | Reserva (com data), remove do `RET` e gera a planilha |
| `cancelar_reservas(proj, retalhos)` | Desfaz a reserva **e devolve ao `RET`** |
| `retalhos_reservados(proj)` / `dar_baixa(proj)` | Lista os reservados do projeto / **baixa registrada**: grava data, hora e responsável, tira do `RET` e oculta do sistema, **sem apagar** |
| `lancar_sobras(sobras, proj)` | Lança sobras do plano de corte já reservadas para o projeto |
| `recriar_arquivos()` | Apaga os `RET*` e recria com os retalhos disponíveis do banco |
| `listar_materiais` / `buscar_material(es)` / `salvar_material` | Cadastro de materiais (insere ou atualiza) |

Todas as operações que escrevem no Corte Certo verificam **antes** se a pasta `CHP` está acessível. Erros de regra são lançados como `RegraDeNegocioError`, com a mensagem pronta para o usuário.

---

## 6. Interface

### Janela principal

- **Indicadores**: total em estoque, disponíveis, reservados e chapas inteiras.
- **Filtro** em todas as colunas (`Ctrl+F`, `Esc` limpa) e seletor *Todos / Disponíveis / Reservados*.
- **Tabela**: ordenação correta por número e data e cores por situação. A prioridade das cores é material inativo, depois chapa inteira, depois reservado (igual à v1).
- **Barra de status**: banco em uso, situação do Corte Certo, hora da última atualização e versão.
- **Atualização automática** (padrão a cada 3 min):
  - a consulta roda em segundo plano, sem travar a tela;
  - o ciclo é pulado se houver uma janela aberta (diálogo ou confirmação);
  - filtro, seleção e rolagem são mantidos;
  - se o banco falhar, o aviso aparece só na barra de status, sem janela de erro, e há nova tentativa no ciclo seguinte.
- Se o Corte Certo não for encontrado, *Novo*, *Excluir*, *Liberar* e *Recriar* ficam bloqueados.

| Menu / Botão | Atalho | Ação |
|---|---|---|
| Novo retalho | `Ctrl+N` | Diálogo de lançamento |
| Excluir | `Del` | Exclui o retalho selecionado (não reservado) |
| Liberar reserva / duplo clique em reservado | `Ctrl+L` | Devolve ao estoque |
| Reservar… (um ou vários selecionados, com Ctrl/Shift; exige `ReservarManual=Ativado`) | `Ctrl+Shift+R` | **Reserva manual** para um projeto ou identificação livre (ex.: projeto que ainda será feito). Não depende de PED nem de plano de corte e não gera `PRJ_*.xlsx`. O retalho sai do RET; para desfazer, use Liberar reserva |
| Atualizar | `F5` | Recarrega |
| Administração › Configurações (só admin) | | Caminhos e diagnóstico |
| Administração › Usuários (só admin) | | Cadastro de usuários e permissões |
| Arquivo › Trocar minha senha / Trocar usuário | | Senha própria; outro usuário entra na mesma janela |
| PCP › Leitor de plano de corte | | Importa sobras do `.cutplanning` |
| PCP › Consumo do plano de corte (compras) | `Ctrl+K` | Chapas inteiras por material e retalhos usados em um ou mais `.cutplanning` |
| PCP › Reserva por projeto | | Reserva retalhos para um pedido |
| PCP › Cadastro de cores | | Inclui ou edita materiais |
| Produção › Materiais | | Consulta de materiais |
| Produção › Baixa de reservas | | Remove do estoque os reservados de um projeto |
| Produção › Retalhos removidos | | Consulta por material dos baixados/excluídos; restauração (admin) |
| Ferramentas › Recriar arquivos do Corte Certo | `Ctrl+R` | Ressincroniza os `RET*.TAB` |
| Ferramentas › Atualizar sistema | | Abre o `Update.exe` |
| Exibir › Atualizar a lista automaticamente | | Liga/desliga a atualização periódica (a cada `AtualizarMinutos`) |
| Exibir › Tema (ou botão ☀/🌙 no topo) | `Ctrl+Shift+T` | Tema claro, escuro ou automático |
| Ferramentas › Atualizar o atualizador | `Ctrl+U` | Copia o `Update.exe` da rede |

### Diálogos (`ui/dialogs/`)

Todos os popups (diálogos e mensagens de confirmação, aviso e erro) usam `RoundedDialog` (`ui/widgets.py`): janela sem a moldura do Windows, com cantos arredondados, sombra suave, cabeçalho arrastável e botão ✕ (ou `Esc`) para fechar. As telas com tabela podem ser redimensionadas pelo canto inferior direito.


- **Novo retalho**
  - Lê o código de barras sozinho ao completar 21 caracteres.
  - `F4` ou `…` escolhe o material.
  - Valida as medidas na hora, aceitando vírgula ou ponto.
  - Depois de lançar, limpa os campos para a próxima etiqueta.
- **Configurações**: pastas com botão *Procurar…*, diagnóstico do Corte Certo e do banco, e aplicação **sem reiniciar**.
- **Reserva por projeto**: marcação com caixas, *Marcar todos*, contadores, aviso quando o corte não foi gerado e opção de abrir a planilha gerada.
- **Baixa de reservas**: mostra exatamente o que será removido antes de confirmar.
- **Leitor de plano de corte**
  - Lê o arquivo em segundo plano e busca os materiais numa única consulta.
  - Sobras de material não cadastrado ficam em vermelho e não podem ser marcadas.
  - As sobras lançadas saem da lista, evitando lançamento em duplicidade.
- **Consumo do plano de corte**
  - Abra ou arraste um ou mais `.cutplanning`; os totais são somados.
  - O resultado aparece em **duas listas separadas, lado a lado**, cada uma com total e botão *Copiar lista*:
    - *Chapas inteiras (compras)*: uma linha por material + medida da chapa, com a quantidade;
    - *Retalhos usados*: colunas Código, Setor, Espessura, Material, Medida, Projeto e ID no estoque, ordenadas por projeto (crescente) e material; retalho que não existe na base fica em **vermelho** (também no Excel).
  - *Exportar Excel* gera uma aba para cada lista (*Chapas inteiras* e *Retalhos usados*), mais a aba *Arquivos*.
  - Detalhes do cruzamento na seção 4.1.
  - **Gerar capa do lote** cria a capa de produção (substitui o `LOTE.xlsm`). Veja a seção 4.2.
  - **Reservar N retalho(s)** (painel de retalhos) reserva no estoque exatamente os retalhos que o plano vai cortar. Antes de gravar, uma conferência mostra o que será reservado. Veja a seção 4.3.
- **Cadastro de cores**: um único botão *Salvar*, que insere ou atualiza conforme o código.

### Atualizador (`Update.exe`)

1. Compara a data do `Retalhos.zip` com `ultima_att`.
2. Encerra **todos** os processos `Retalhos.exe`.
3. Extrai o pacote arquivo a arquivo, com progresso real. Ignora o próprio `Update.exe` e o `Settings.json` local.
4. Grava a nova `ultima_att` e oferece o botão *Abrir Retalhos*.

### Erros e log

- Erros esperados (regra de negócio, rede, banco) aparecem como aviso, sem detalhes técnicos.
- Erros inesperados mostram uma janela com detalhes e são registrados em `%LOCALAPPDATA%\Retalhos\retalhos.log`.

---

## 6.1 Login e usuários

- **Ao abrir:** configuração (se não houver `Settings.json`) → cria a `tblUsuarios` se faltar → **primeiro administrador** (só com a tabela vazia) → **login**. Se o banco não abrir, o app mostra o erro e oferece corrigir o caminho em Configurações.
- **Responsável** dos lançamentos = **nome do usuário logado**. **Liberar reserva** não altera o responsável nem a data de lançamento.
- **Arquivo › Trocar minha senha / Trocar usuário.** Cancelar a troca de usuário mantém quem já estava logado.
- **Administração › Usuários** (só admin): cadastrar (com senha temporária), editar nome/permissões, ativar/desativar e redefinir senha. Usuário novo e senha redefinida obrigam a cadastrar uma senha pessoal no próximo acesso.

| Permissão | Libera |
|---|---|
| Administrador | Tudo, mais Usuários, Configurações, Recriar arquivos do Corte Certo e Atualizar o atualizador |
| PCP | Menu PCP (plano de corte, consumo/compras, reserva por projeto, cadastro de cores) |
| Remover reserva | Liberar reserva |
| Reservar manual | Botão Reservar… |

**Regras de segurança:**
- **Senhas:** guardadas como hash PBKDF2-SHA256, com salt por usuário e 200 mil iterações; nunca em texto.
- **Login:** a mensagem de erro é a mesma para usuário inexistente e senha errada. O usuário desativado não entra.
- **Administradores:**
  - o sistema sempre mantém **pelo menos um administrador ativo**;
  - o admin não pode tirar o próprio acesso de administrador;
  - as ações de administração conferem no banco se quem age **ainda é** administrador, para o caso de ter sido rebaixado por outro admin com a sessão aberta.
- **Serviço:** as permissões também são conferidas no serviço (liberar reserva, reserva manual, recriar arquivos), não só escondendo botões.

### Estrutura da `tblUsuarios`

`id` (autonumeração), `Login` (único, maiúsculo), `Nome`, `SenhaHash`, `Admin`, `PCP`, `RemoverReserva`, `ReservarManual`, `Ativo`, `TrocarSenha`, `CriadoEm`, `UltimoAcesso`. Criada em 26/10/2026 no banco de produção. O backup anterior à criação está em `backup_banco/`, fora do git.

## 7. Desenvolvimento

```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python main.py
.venv\Scripts\python -m pytest
```

- **Testar contra Access real:** crie um `.accdb` vazio e defina `set RETALHOS_TEST_ACCDB=C:\caminho\vazio.accdb` antes do `pytest`.
- **Desenvolver sem a rede:** aponte `Directory_data_base` para um arquivo `.db` (SQLite) com as duas tabelas.
- **Build:** veja [codigo para compilar EXE.txt](codigo%20para%20compilar%20EXE.txt).
- **Ícone:** `.venv\Scripts\python ferramentas\gerar_icone.py` redesenha `retalhos/resources/icon_retalho.ico` em 9 tamanhos (16 a 256 px). Use `--previa` para só ver a imagem `ferramentas/icone_previa.png`. As cores ficam no início do script.

---

## 8. Mudanças em relação à v1

### Correções de bugs

1. **Dependência ausente**: `mysql.connector` era importado sem estar no `requirements.txt`. Foi removido, junto com os conectores SQL Server e MySQL, que não eram usados.
2. **Senha do banco**: três telas conectavam **sem** a senha configurada. Agora todas as conexões passam pelo mesmo `Database`.
3. **SQL**: era montado com f-string (risco de erro e de injeção). Agora é 100% parametrizado.
4. **ID do registro inserido**: `TOP 1 ... ORDER BY id DESC` podia pegar o ID de outra máquina. Agora usa `@@IDENTITY`.
5. **Banco × arquivo**: banco e `RET` podiam ficar dessincronizados. Agora há transação com rollback se o arquivo falhar, e a pasta é verificada antes.
6. **Desfazer reserva** não devolvia o retalho ao `RET`. Agora devolve.
7. **Baixa de reservas** não removia do `RET` as sobras lançadas pelo Leitor XML. Agora remove.
8. **Excluir retalho** falhava quando o `RET` não existia. Agora não falha.
9. **Arquivo `PED`**: era **modificado** pelo sistema. Agora é só lido.
10. **Leitor XML** travava (`TypeError`) com material não cadastrado. Agora marca a linha como inválida.
11. **Leitor XML** permitia lançar as mesmas sobras duas vezes. Agora as sobras lançadas saem da lista.
12. **`Settings.json`**: era lido pelo caminho relativo, o que falhava ao abrir por atalho com outra pasta de início. Agora é procurado ao lado do executável.
13. **Configurações** só valiam depois de reiniciar o app. Agora são aplicadas na hora.
14. **Ícone**: `PATH_ICON` apontava para um arquivo inexistente. Os recursos agora funcionam também empacotados.
15. **`del_files`** levantava uma string (`TypeError`). O código foi substituído.
16. **Atualizador**:
    - encerrava só o primeiro `Retalhos.exe` encontrado;
    - a barra de progresso era simulada;
    - sobrescrevia o `Settings.json` local se o pacote o contivesse.
17. **Enter** num campo de texto podia acionar o botão errado do diálogo.
18. **Erros sem tratamento** fechavam o app silenciosamente (`--noconsole`). Agora são exibidos e registrados em log.
19. **Reserva** não gravava `DataReserva`. Agora grava.
20. **Cor de chapa inteira** usava 2740 × 1840 fixos no código. Agora usa os valores do `Settings.json`.

### Organização

- Um pacote único (`retalhos/`) com camadas separadas, no lugar de `Functions/Gui/Interface` com lógica misturada nas telas.
- Telas feitas em código, sem `.ui` gerado e editado à mão nem `pictures_rc.py` com 3 mil linhas.
- Tabelas com modelo e filtro do Qt (`QAbstractTableModel` + `QSortFilterProxyModel`), em vez de `QTableWidget` preenchido célula a célula.
- 22 testes automatizados.
