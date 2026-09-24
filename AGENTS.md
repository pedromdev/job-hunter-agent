# Job Hunter Agent — Assistente de Carreira com Nanobot

## Descrição

Este projeto implementa um assistente pessoal de **avaliação de processo seletivo** usando [Nanobot](https://github.com/HKUDS/nanobot).
O agente roda via Telegram, analisa a vaga que o usuário traz, gera currículos em PDF a partir de um template fixo
(HTML+Playwright), valida aderência ATS, escreve cartas e mensagens, pesquisa empresas e sugere projetos de desenvolvimento.

**Escopo:** o agente trabalha com a vaga que o usuário traz. Ele **não faz varredura de vagas** e não gerencia fila de candidaturas.

## Arquitetura

```
Telegram → Nanobot Gateway → Agent Loop → Tools (resume_generator, resume_editor, ats_validator,
                                        →        ats_format_check, cover_letter, company_researcher,
                                        →        career_compass)
                                        → Web search/fetch
                                        → File I/O (RESUME.md, templates, job_descriptions/, output/)
```

### Componentes

| Caminho | Função |
|---------|--------|
| `AGENTS.md` | Instruções para IA coders (este arquivo) |
| `config.json` | Config Nanobot: provider Gemini, canal Telegram, web tools |
| `Dockerfile` | Imagem Docker com nanobot + Playwright + Chromium + deps ATS |
| `docker-compose.yml` | Orquestração do gateway + CLI |
| `job_hunter_tools/` | Pacote Python com tools customizadas para Nanobot |
| `job_hunter_tools/ats/` | Motor ATS (parser, scorer, TF-IDF, keywords, formatação) |
| `job_hunter_tools/compass/` | Catálogo de arquétipos e skills por cargo |
| `templates/` | Templates Jinja2 de currículo (`.html` + `.txt`) e e-mail (pt-br e en) |
| `skills/job-hunter/SKILL.md` | Skill principal: identidade e workflows do agente |
| `skills/guided-interview/SKILL.md` | Entrevista guiada que constrói o perfil e preenche as partes fixas |
| `workspace_files/AGENTS.md` | Instruções carregadas em runtime pelo agente |
| `RESUME.md` | Currículo do usuário em markdown (fonte da verdade) |
| `USER.md` | Preferências de trabalho e comunicação do usuário |

## Comandos de Desenvolvimento

```bash
# Construir e rodar
docker compose build
docker compose up -d

# CLI (teste rápido)
docker compose run --rm job-hunter-cli agent -m "Olá"

# Logs
docker compose logs -f

# Parar
docker compose down
```

### Variáveis de Ambiente Necessárias

| Variável | Descrição |
|----------|-----------|
| `GEMINI_API_KEY` | Chave da API Gemini (provider padrão) |
| `DEEPSEEK_API_KEY` | Chave da API DeepSeek (opcional) |
| `GROQ_API_KEY` | Chave da API Groq (opcional) |
| `TELEGRAM_TOKEN` | Token do bot Telegram (via @BotFather) |
| `TELEGRAM_ALLOW_FROM` | User ID do Telegram permitido (opcional, default `*`) |

## Tools Customizadas

Cada tool é uma classe Python que estende `nanobot.agent.tools.base.Tool`,
registrada via entry-point `nanobot.tools` no `pyproject.toml`.

| Tool | Função |
|------|--------|
| `resume_generator` | Gera PDF do currículo e `.txt` para ATS. Aceita `resume_data` (`about` + `experiences`), `template_lang`, `job_title`, `ats_txt` |
| `resume_editor` | Escreve o conteúdo completo do `RESUME.md` (proposta de atualização) |
| `ats_validator` | Mede aderência do currículo a uma JD e classifica skills ausentes |
| `ats_format_check` | Checa formatação, dados pessoais, seções obsoletas e uso de bullets |
| `cover_letter` | Carta, e-mail e cold message (texto ou PDF) |
| `company_researcher` | Pesquisa estruturada de empresa |
| `career_compass` | Projetos para fechar gaps e desenvolvimento de competências |

## Convenções

- Templates Jinja2 em `templates/` com sufixo `.{lang}.html` e `.{lang}.txt`
- Parâmetro `template_lang`: `"pt-br"` ou `"en"`
- `JOB_HUNTER_TEMPLATES` aponta para os templates (default `/app/templates`)
- `RESUME.md` é a fonte da verdade do perfil — **nunca remova informações dele** sem pedido explícito e confirmação de risco

## Partes fixas vs dinâmicas do template

Os templates de currículo têm **partes fixas** (cabeçalho, contato, objetivo, formação, tecnologias, idiomas e habilidades)
e apenas **`{{ about }}` e `{{ experiences }}` são dinâmicos** (vêm do JSON a cada vaga).

- As partes fixas são preenchidas logo após a entrevista guiada (skill `guided-interview`), editando diretamente
  `resume.pt-br.html`, `resume.en.html`, `resume.pt-br.txt` e `resume.en.txt`.
- O diretório `templates/` é montado **read-write** no container para que as edições persistam.
- Atualizações posteriores: propor o texto, aplicar só após aprovação e **nunca** sobrescrever `{{ about }}` e `{{ experiences }}`.
