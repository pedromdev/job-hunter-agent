# Job Hunter Agent

[![Nanobot](https://img.shields.io/badge/powered%20by-Nanobot-8B5CFE)](https://github.com/HKUDS/nanobot)

Um assistente de carreira no Telegram para **avaliação de processo seletivo** — analisa a vaga que você traz, gera currículos em PDF a partir de um template fixo, valida aderência ATS, escreve cartas e mensagens, pesquisa empresas e sugere projetos de desenvolvimento. Construído sobre o [Nanobot](https://github.com/HKUDS/nanobot).

> **Escopo:** o agente trabalha com a vaga que você traz. Ele **não faz varredura de vagas** nem gerencia fila de candidaturas.

## Arquitetura

```
Telegram → Nanobot Gateway → Agent Loop → resume_generator (Jinja2 + Playwright → PDF)
                                         → resume_editor
                                         → ats_validator / ats_format_check
                                         → cover_letter
                                         → company_researcher / career_compass
                                         → web_search / web_fetch
```

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) + Compose
- Uma chave de API de um provedor de IA (veja o script `setup-model.sh`)
- Um token de bot do Telegram (criado via @BotFather)

## Início Rápido

### 1. Clone e configure

```bash
git clone <seu-repositorio>
cd job-hunter-agent
cp .env.example .env
```

Edite `.env` com suas chaves:

```env
# Escolha UM provedor (veja setup-model.sh para mais opções)
GEMINI_API_KEY=sua-chave-aqui
# ou DEEPSEEK_API_KEY=sk-sua-chave-aqui
# ou GROQ_API_KEY=gsk_sua-chave-aqui

TELEGRAM_TOKEN=1234567890:ABCdefGHIjklmNOPqrstUVwxyz
TELEGRAM_ALLOW_FROM=*
```

### 2. Configure o modelo de IA

Use o script interativo para escolher e configurar o provedor:

```bash
chmod +x setup-model.sh
./setup-model.sh
```

Opções disponíveis:
- **Google Gemini** — grátis, sem cartão de crédito (Gemini 2.5 Flash)
- **Groq** — grátis, sem cartão de crédito (Llama 3.3 70B)
- **DeepSeek** — pago por uso, ~$0.14/M tokens (DeepSeek V4 Flash)

### 3. Construa e rode

```bash
docker compose build
docker compose up -d
```

O bot está no ar no Telegram. Envie qualquer mensagem para começar.

### 4. Monte seu perfil (entrevista guiada)

No primeiro contato, o agente conduz uma **entrevista guiada** que constrói o `RESUME.md` e, em seguida, preenche as **partes fixas do template** do currículo. Depois disso vem o onboarding, que calibra suas preferências.

### 5. Teste via CLI

```bash
docker compose run --rm job-hunter-cli agent -m "Olá"
```

## Exemplos de Uso

### Analisar uma vaga

"Analise esta vaga: <link ou texto>"

O agente salva a JD em `job_descriptions/`, separa requisitos obrigatórios de diferenciais, procura armadilhas, pesquisa a empresa, calcula o fit (🟢 ≥70% / 🟡 40-69% / 🔴 <40%) e dá um veredito explícito.

### Gerar currículo

"Gere um currículo para a vaga de Senior Software Engineer na TechCorp"

O agente monta `about` e `experiences` no Padrão Narrativo Permanente, renderiza o template fixo (pt-br ou en) via Playwright, gera o `.txt` para ATS e valida com `ats_validator` e `ats_format_check`.

### Carta e mensagens

"Escreva uma carta para essa vaga" — texto pronto para copiar ou PDF formal. Cold messages seguem o formato de 3 linhas (especificidade, prova em número, pedido pequeno).

### Pesquisar empresa

"Pesquise a empresa X" — dossiê estruturado com descrição, liderança, produtos, clientes, modelo de negócio e faixas salariais.

### Desenvolver competências

"Quero melhorar em Kubernetes e DDD" — o `career_compass` sugere projetos práticos que fecham os gaps.

## Tools Customizadas

O projeto inclui 7 tools Nanobot em `job_hunter_tools/`:

| Tool | Função |
|------|--------|
| `resume_generator` | Gera PDF do currículo e `.txt` para ATS (`about` + `experiences`) |
| `resume_editor` | Escreve o conteúdo completo do `RESUME.md` (proposta de atualização) |
| `ats_validator` | Mede aderência do currículo a uma JD e classifica skills ausentes |
| `ats_format_check` | Checa formatação, dados pessoais, seções obsoletas e bullets |
| `cover_letter` | Carta, e-mail e cold message (texto ou PDF) |
| `company_researcher` | Pesquisa estruturada de empresa |
| `career_compass` | Projetos para fechar gaps e desenvolvimento de competências |

Para adicionar uma nova tool:
1. Crie uma classe extendendo `nanobot.agent.tools.base.Tool`
2. Registre em `pyproject.toml` sob `[project.entry-points."nanobot.tools"]`
3. Reconstrua a imagem Docker

## Templates

Os templates estão em `templates/` (montados read-write no container):

| Arquivo | Finalidade |
|---------|------------|
| `resume.pt-br.html` / `resume.pt-br.txt` | Currículo — Português (PDF + ATS) |
| `resume.en.html` / `resume.en.txt` | Currículo — Inglês (PDF + ATS) |
| `email.pt-br.html` | Carta de apresentação — Português |
| `email.en.html` | Carta de apresentação — Inglês |

**Partes fixas vs dinâmicas:** cabeçalho, contato, objetivo, formação, tecnologias, idiomas e habilidades são **fixos** no template e preenchidos após a entrevista guiada. Apenas `{{ about }}` e `{{ experiences }}` são dinâmicos e mudam por vaga.

## Estrutura do Projeto

```
├── config.json                  Configuração do gateway Nanobot
├── docker-compose.yml           Serviços: gateway + CLI
├── Dockerfile                   Python 3.12 + nanobot + Playwright
├── pyproject.toml               Pacote Python com entry points
├── setup-model.sh               Script interativo de configuração do modelo
│
├── job_hunter_tools/            Tools Nanobot customizadas (Python)
│   ├── resume_generator.py
│   ├── resume_editor.py
│   ├── ats_validator.py
│   ├── ats_format_checker.py
│   ├── cover_letter.py
│   ├── company_researcher.py
│   ├── career_compass.py
│   ├── ats/                     Motor ATS (parser, scorer, TF-IDF, formatação)
│   └── compass/                 Catálogo de arquétipos e skills por cargo
│
├── templates/                   Templates Jinja2 (currículo + e-mail)
├── skills/                      Skills Nanobot (job-hunter + guided-interview)
├── RESUME.md                    Seu currículo (fonte da verdade)
│
├── workspace_files/             Montado como read-only no container
│   ├── AGENTS.md                Instruções do agente
│   └── SOUL.md                  Personalidade do agente
│
├── workspace/                   Dados de execução (persistidos)
│   ├── output/                  PDFs e .txt gerados
│   ├── job_descriptions/        Vagas salvas
│   ├── memory/MEMORY.md         Memória do agente
│   ├── USER.md                  Preferências do usuário
│   └── HEARTBEAT.md             Tarefas periódicas
│
└── sample/                      Arquivos de exemplo
    └── RESUME.example.md
```

## Variáveis de Ambiente

| Variável | Obrigatório | Descrição |
|----------|-------------|-----------|
| `GEMINI_API_KEY` | Não* | Chave da API Google Gemini (padrão) |
| `DEEPSEEK_API_KEY` | Não* | Chave da API DeepSeek |
| `GROQ_API_KEY` | Não* | Chave da API Groq |
| `TELEGRAM_TOKEN` | Sim | Token do bot Telegram |
| `TELEGRAM_ALLOW_FROM` | Não | Restringir a user IDs (separados por vírgula) ou `*` |

*Configure **um** provedor de IA. Use `setup-model.sh` para configurar automaticamente.

## Desenvolvimento

```bash
# Construir
docker compose build

# Rodar gateway (Telegram)
docker compose up -d

# Modo CLI
docker compose run --rm job-hunter-cli agent -m "seu comando"

# Ver logs
docker compose logs -f

# Parar
docker compose down
```

## Licença

MIT
