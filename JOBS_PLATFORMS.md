# Plataformas de Emprego

Lista de plataformas onde o agente deve buscar vagas.
Use o `job_scraper` tool com os nomes das plataformas abaixo.
Para plataformas não listadas, use `web_search` para encontrar vagas.

---

## Indeed

Busca global de empregos. Suporta RSS.
- Busca: `job_scraper(query="...", platforms="indeed")`
- URL base: https://www.indeed.com

## Indeed Brasil

Indeed versão Brasil.
- Busca: `job_scraper(query="...", platforms="indeed_br")`
- URL base: https://br.indeed.com

## Remote OK

Vagas 100% remotas mundo todo. API JSON pública.
- Busca: `job_scraper(query="...", platforms="remoteok")`
- URL base: https://remoteok.com

## Programathor

Plataforma brasileira de tecnologia.
- Busca: `job_scraper(query="...", platforms="programathor")`
- URL base: https://programathor.com.br

## GeekHunter

Plataforma brasileira de tecnologia.
- Busca: `job_scraper(query="...", platforms="geekhunter")`
- URL base: https://www.geekhunter.com.br

---

*Nota: Para plataformas como LinkedIn, use `web_search` + `web_fetch`
já que exigem autenticação ou têm proteção anti-scraping.*
