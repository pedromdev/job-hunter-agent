---
name: guided-interview
description: Entrevista guiada para construir o perfil profissional do usuário e gerar o RESUME.md
always: false
metadata:
  nanobot:
    emoji: "🎙️"
    category: career
---

# Entrevista Guiada — Construção de Perfil Profissional

Você vai conduzir uma entrevista passo a passo para construir o perfil completo do usuário.
Ao final, você deve gerar (ou atualizar) o arquivo `RESUME.md` com todos os dados coletados.

## Regras Gerais

- **Uma pergunta por vez.** Espere o usuário responder antes de fazer a próxima.
- **Seja amigável e encorajador.** O usuário está compartilhando informações pessoais.
- **Confirme cada resposta** antes de seguir ("Entendi, então você trabalhou como X na empresa Y por Z anos, correto?").
- **Salve o progresso incrementalmente.** A cada etapa concluída, registre em `MEMORY.md` o que já foi coletado.
- **Se o usuário pedir para pular uma etapa**, respeite e use dados vazios/placeholders.
- **Se o usuário disser algo como "vamos" ou "continuar"**, retome de onde parou (leia `MEMORY.md` para saber o progresso).

## Etapa 1 — Identificação

Pergunte:
"Qual seu **nome completo**?"

Após receber, registre em `## Information > Name` no RESUME.md.

Pergunte:
"Qual seu **telefone** para contato?" (opcional — pode pular)

Pergunte:
"Qual seu **e-mail** para contato?"

## Etapa 2 — Cargo

Pergunte:
"Qual **cargo** você deseja buscar? Pode ser seu cargo atual ou o último que ocupou.
Ex: 'Senior Software Engineer', 'Full Stack Developer'."

## Etapa 3 — Links

Pergunte:
"Me passe os links do seu **LinkedIn** e **GitHub/portfólio** (se tiver)."

Registre em `## Information > LinkedIn` e `## Information > GitHub`.

## Etapa 4 — Experiências (LOOP PRINCIPAL)

Pergunte:
"Agora vamos cadastrar suas **experiências profissionais**. Você pode:
- **Digitar** os dados de cada experiência uma a uma
- **Enviar um PDF** do seu currículo atual que eu extraio as informações

Qual prefere?"

### Se enviar PDF:
1. O arquivo será recebido pelo Telegram e salvo no workspace.
2. Use `exec` para extrair o texto:
   ```bash
   pdftotext <caminho_do_arquivo> -
   ```
3. Analise o texto extraído e identifique: empresa, cargo, período, descrição, destaques.
4. **Mostre o resultado para o usuário confirmar** antes de seguir.
5. Pergunte: "Tem mais alguma experiência além das que estavam no PDF?"

### Se digitar:
Para CADA experiência, faça as perguntas abaixo em sequência:

1. "Qual o nome da **empresa**?"
2. "Qual **cargo** você ocupou?"
3. "Qual **período** (mês/ano de início — mês/ano de fim)?"
4. "Quais **tecnologias** usava nesse cargo? (ex: React, Node.js, AWS)"
5. "**O que você fazia?** Descreva suas principais responsabilidades."
6. "**Quais resultados/entregas** você destaca? Pode ser economia de tempo, redução de custos, features entregues, etc. Se não tiver, pode pular."

Após cada experiência, pergunte:
"Tem **mais alguma experiência** para adicionar?"

Repita até o usuário dizer "não", "é só", "acabou" ou similar.

## Etapa 5 — Projetos (OPCIONAL)

Pergunte:
"Tem **projetos** (pessoais ou profissionais) que queira destacar no currículo?"

Se sim, para cada projeto:
1. "Qual o **nome** do projeto?"
2. "Qual a **descrição** — o que faz e qual foi seu papel?"
3. "Quais **tecnologias** usou?"

Pergunte: "Tem mais algum projeto?" até "não".

## Etapa 6 — Atividades Extracurriculares (OPCIONAL)

Pergunte:
"Participou de **atividades extracurriculares**, trabalhos voluntários, maratonas de programação, etc?"

Se sim, para cada atividade:
1. "Qual o **nome** da atividade?"
2. "Em que **ano** aconteceu?"
3. "**Descrição** — o que fez e qual seu papel?"
4. "Quais **tecnologias** usou (se aplicável)?"

Pergunte: "Tem mais alguma atividade?" até "não".

## Etapa 7 — Contexto das Empresas

Esta etapa é IMPORTANTE. Para CADA empresa que o usuário listou nas experiências, pergunte individualmente:

"Vamos contextualizar a [EMPRESA]. Descreva resumidamente:
- **O que a empresa faz/fez** (ramo, produto, mercado)?
- **Como seu trabalho se relacionava com o negócio** dela?
  Ex: 'Na ACME Corp, eu desenvolvia o sistema de pagamentos que processava R$ 2M/mês'
  ou 'Na StartupX, eu era o único desenvolvedor e construí o MVP do zero'."

**ATENÇÃO:** Esta descrição NÃO deve ir para a seção `## Companies` do RESUME.md.
Ela deve **complementar/atualizar a descrição da experiência** na seção `## Experience`.
Incorpore o contexto da empresa na descrição da experiência para dar mais impacto.

Exemplo de como deve ficar:
```
### ACME Corp — Senior Software Engineer
_Period: jan/2020 - present_

**Technologies:** React, Node.js, PostgreSQL

Na ACME Corp, uma fintech que processa pagamentos para 500+ lojas online, 
eu liderei o time de backend responsável pelo sistema de conciliação financeira.

- Reduzi o tempo de fechamento mensal de 5 dias para 2 horas
- Implementei detecção automática de discrepâncias, eliminando retrabalho manual
```

## Final — Gerar RESUME.md

Com TODOS os dados coletados e confirmados:

1. **Monte o RESUME.md** seguindo EXATAMENTE o formato do template abaixo:

```markdown
# My Resume

## Information

- **Name:** [nome coletado]
- **Phone:** [telefone]
- **Email:** [email]
- **LinkedIn:** [linkedin]
- **GitHub:** [github]

## About me

[Parágrafo profissional escrito por você com base na trajetória do usuário.
Destaque: anos de experiência, stack principal, tipos de empresa, impacto gerado.]

## Experience

### [Empresa] — [Cargo]
_Period: [início] - [fim]_

**Technologies:** [techs]

[Descrição enriquecida com contexto da empresa (Etapa 7) + responsabilidades]

- [destaque 1]
- [destaque 2]

## Projects

### [Nome do projeto]

[Descrição]

## Skills

- **Languages:** ...
- **Frameworks:** ...
- **Cloud & DevOps:** ...
- **Databases:** ...
- **Tools:** ...
- **Spoken Languages:** ...

## Education

### [Instituição] — [Curso]
_Period: [início] - [fim]_

## Extracurricular Activities

### [Atividade]
_Year: [ano]_

[Descrição]

## Companies

_Para cada empresa, descreva brevemente o ramo/negócio dela para que o agente_
_possa contextualizar as experiências nas candidaturas._

### [Empresa]
_Industry: [ramo]_

[Descrição do negócio da empresa]
```

2. Use a ferramenta de escrita de arquivo (`write` ou `edit_file`) para salvar em `RESUME.md`.

3. Informe ao usuário: "Seu perfil foi construído com sucesso! Você pode revisar e ajustar o arquivo RESUME.md manualmente quando quiser."

4. **Importante:** A seção `## Companies` deve conter APENAS a descrição do negócio de cada empresa (ramo, produto, mercado). NÃO inclua a relação do usuário com a empresa ali — isso já foi incorporado na descrição da experiência na Etapa 7.

## Regras de Skills

Ao montar a seção `## Skills`:
- **Languages:** Liste as linguagens mencionadas nas tecnologias das experiências
- **Frameworks & Runtimes:** Frameworks, bibliotecas, runtimes
- **Cloud & DevOps:** Ferramentas de cloud, deploy, infraestrutura
- **Databases:** Bancos de dados
- **Tools:** Ferramentas diversas (Git, Docker, etc.)
- **Spoken Languages:** Pergunte ao usuário se não foi mencionado

Agrupe e deduplique as tecnologias. Se o usuário mencionou "React" em 3 experiências diferentes, coloque uma vez só.
