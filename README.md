# Job Hunter Agent

[![Nanobot](https://img.shields.io/badge/powered%20by-Nanobot-8B5CFE)](https://github.com/HKUDS/nanobot)

Um agente de IA no Telegram para caça a vagas de emprego — busca em múltiplas plataformas, gera currículos adaptados em PDF e escreve cartas de apresentação. Construído sobre o [Nanobot](https://github.com/HKUDS/nanobot).

## Arquitetura

```
Telegram → Nanobot Gateway → Agent Loop → job_scraper
                                         → resume_generator (Jinja2 + Playwright → PDF)
                                         → cover_letter (texto ou PDF)
                                         → web_search / web_fetch
```

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) + Compose
- Uma chave de API de um provedor de IA (veja o script `setup-model.sh`)
- Um token de bot do Telegram (criado via @BotFather)
- Um currículo preenchido em `RESUME.md`

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
DEEPSEEK_API_KEY=sk-sua-chave-aqui
# ou GROQ_API_KEY=gsk_sua-chave-aqui
# ou GEMINI_API_KEY=sua-chave-aqui

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
- **Groq** — grátis, sem cartão de crédito (Llama 3.3 70B)
- **Google Gemini** — grátis, sem cartão de crédito (Gemini 2.5 Flash)
- **DeepSeek** — pago por uso, ~$0.14/M tokens (DeepSeek V4 Flash)

### 3. Preencha seu perfil

Edite `RESUME.md` com suas informações profissionais completas — esta é a fonte da verdade do agente.

Opcional: edite `workspace/USER.md` com suas preferências.

### 4. Configure as plataformas de vaga

Edite `JOBS_PLATFORMS.md` para ativar/desativar plataformas. Suportadas atualmente:

| Plataforma | Chave | Tipo |
|------------|-------|------|
| Indeed (global) | `indeed` | RSS |
| Indeed Brasil | `indeed_br` | RSS |
| Remote OK | `remoteok` | API JSON |
| Programathor | `programathor` | HTML scraping |
| GeekHunter | `geekhunter` | HTML scraping |

### 5. Configure o Telegram

#### 5.1 Crie um bot no Telegram

1. Abra o Telegram e procure por **@BotFather**
2. Envie o comando `/newbot`
3. Escolha um nome (ex: "Meu Job Hunter")
4. Escolha um username único terminando em `bot` (ex: `MeuJobHunterBot`)
5. O @BotFather vai responder com um token. **Copie este token** — será seu `TELEGRAM_TOKEN`

#### 5.2 Descubra seu User ID

**Opção A — Pelo @userinfobot:**
1. Pesquise por **@userinfobot** no Telegram
2. Envie `/start`
3. O bot responderá com seu ID numérico

**Opção B — Pelo próprio Job Hunter Agent:**
1. Deixe o `TELEGRAM_ALLOW_FROM` como `*` temporariamente
2. Suba o bot com `docker compose up -d`
3. Envie qualquer mensagem para o bot no Telegram
4. Veja nos logs: `docker compose logs job-hunter | grep "from"`

#### 5.3 Configure no .env

```env
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklmNOPqrstUVwxyz
TELEGRAM_ALLOW_FROM=123456789    # seu user ID numérico
```

### 6. Construa e rode

```bash
docker compose build
docker compose up -d
```

O bot está no ar no Telegram. Envie qualquer mensagem para começar.

### 7. Teste via CLI

```bash
docker compose run --rm job-hunter-cli agent -m "Busque vagas de React developer"
```

## Exemplos de Uso

### Buscar vagas

Converse com o bot no Telegram: "Busque vagas de desenvolvedor Python remoto"

O agente vai:
1. Pesquisar em todas as plataformas configuradas
2. Pontuar cada vaga contra suas habilidades (RESUME.md)
3. Mostrar resultados ordenados por fit (🟢 ≥70% / 🟡 40-69% / 🔴 <40%)

### Gerar currículo adaptado

"Gere um currículo para a vaga de Senior Software Engineer na TechCorp"

O agente vai:
1. Ler a descrição da vaga
2. Selecionar suas experiências mais relevantes
3. Reordenar habilidades para os requisitos
4. Gerar um PDF com HTML+Tailwind via Playwright

### Escrever carta de apresentação

"Escreva uma carta de apresentação para a vaga de Full Stack Developer"

O agente retorna texto formatado (pronto para copiar) ou PDF formal.

## Tools Customizadas

O projeto inclui 3 tools Nanobot em `job_hunter_tools/`:

- **`job_scraper`** — busca no Indeed (RSS), RemoteOK (API JSON), Programathor e GeekHunter (HTML)
- **`resume_generator`** — renderiza template Jinja2 com Tailwind CSS, exporta para PDF via Playwright/Chromium
- **`cover_letter`** — gera cartas de apresentação personalizadas em texto ou PDF

Para adicionar uma nova tool:
1. Crie uma classe extendendo `nanobot.agent.tools.base.Tool`
2. Registre em `pyproject.toml` sob `[project.entry-points."nanobot.tools"]`
3. Reconstrua a imagem Docker

## Templates

Os templates estão em `templates/` usando Jinja2 + Tailwind CSS (carregado via CDN):

| Arquivo | Finalidade |
|---------|------------|
| `resume.pt-br.html` | Template de currículo — Português |
| `resume.en.html` | Template de currículo — Inglês |
| `email.pt-br.html` | Carta de apresentação — Português |
| `email.en.html` | Carta de apresentação — Inglês |

## Estrutura do Projeto

```
├── config.json                  Configuração do gateway Nanobot
├── docker-compose.yml           Serviços: gateway + CLI
├── Dockerfile                   Python 3.12 + nanobot + Playwright
├── pyproject.toml               Pacote Python com entry points
├── setup-model.sh               Script interativo de configuração do modelo
│
├── job_hunter_tools/            Tools Nanobot customizadas (Python)
│   ├── job_scraper.py
│   ├── resume_generator.py
│   └── cover_letter.py
│
├── templates/                   Templates HTML Jinja2
├── skills/job-hunter/SKILL.md   Skill Nanobot (persona + workflow do agente)
├── RESUME.md                    Seu currículo (fonte da verdade)
├── JOBS_PLATFORMS.md            Configuração das plataformas de vaga
│
├── workspace_files/             Montado como read-only no container
│   ├── AGENTS.md                Instruções do agente
│   └── SOUL.md                  Personalidade do agente
│
├── workspace/                   Dados de execução (persistidos)
│   ├── output/                  PDFs gerados
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
| `DEEPSEEK_API_KEY` | Não* | Chave da API DeepSeek |
| `GROQ_API_KEY` | Não* | Chave da API Groq (grátis) |
| `GEMINI_API_KEY` | Não* | Chave da API Google Gemini (grátis) |
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

## Adicionar uma Plataforma de Vaga

1. Adicione um handler em `job_hunter_tools/job_scraper.py` (dicionário `PLATFORM_HANDLERS`)
2. Adicione a plataforma em `JOBS_PLATFORMS.md`
3. Reconstrua: `docker compose build`

## Licença

MIT
