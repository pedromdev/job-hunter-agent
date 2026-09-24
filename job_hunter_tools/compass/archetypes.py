from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProjectArchetype:
    id: str
    name: str
    description: str
    skills_developed: list[str] = field(default_factory=list)
    difficulty: str = "intermediate"
    estimated_effort: str = ""
    tech_stack: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


ARCHETYPES: list[ProjectArchetype] = [
    # ── Cloud / DevOps ──────────────────────────────────────────────
    ProjectArchetype(
        id="k8s-deploy",
        name="Deploy de Aplicação com Kubernetes na AWS",
        description=(
            "Containerize uma aplicação Node.js/NestJS com Docker, crie um cluster EKS "
            "com managed node groups, configure Helm charts para deploy, Ingress Controller "
            "(nginx-ingress), auto-scaling (HPA + Cluster Autoscaler), health checks "
            "(liveness/readiness probes) e integre com CI/CD (GitHub Actions). "
            "Inclua observabilidade com Prometheus stack e dashboards Grafana."
        ),
        skills_developed=["Kubernetes", "Docker", "AWS", "Helm", "CI/CD", "Prometheus", "Grafana"],
        difficulty="advanced",
        estimated_effort="6-8 semanas",
        tech_stack=["NestJS", "TypeScript", "Docker", "EKS", "Helm", "GitHub Actions"],
        tags=["cloud", "devops", "aws"],
    ),
    ProjectArchetype(
        id="terraform-infra",
        name="Infraestrutura como Código com Terraform",
        description=(
            "Modele toda a infraestrutura de uma aplicação em nuvem usando Terraform: "
            "VPC com subnets públicas/privadas, ECS Fargate, RDS PostgreSQL, S3, CloudFront, "
            "IAM roles e policies. Use módulos reutilizáveis, workspaces (dev/staging/prod), "
            "remote state com S3 + DynamoDB locking e integre com GitHub Actions para "
            "deploy automatizado da infraestrutura."
        ),
        skills_developed=["Terraform", "AWS", "Cloud Computing", "CI/CD", "Docker"],
        difficulty="advanced",
        estimated_effort="4-6 semanas",
        tech_stack=["Terraform", "AWS", "Docker", "GitHub Actions", "PostgreSQL"],
        tags=["cloud", "devops", "iac"],
    ),
    ProjectArchetype(
        id="cicd-platform",
        name="Pipeline CI/CD Multiplataforma",
        description=(
            "Construa um pipeline CI/CD completo no GitHub Actions que: roda lint e testes "
            "unitários (Jest), executa testes E2E (Playwright) em paralelo, faz build de "
            "imagens Docker, escaneia vulnerabilidades (Trivy), faz push para ECR, deploy "
            "no ECS/EKS com zero-downtime, e envia notificação no Slack/Telegram. "
            "Inclua stages condicionais, cache inteligente e matriz de versões Node."
        ),
        skills_developed=["CI/CD", "GitHub Actions", "Docker", "Playwright", "AWS", "Testes automatizados"],
        difficulty="intermediate",
        estimated_effort="3-4 semanas",
        tech_stack=["GitHub Actions", "Docker", "AWS ECR", "AWS ECS", "Playwright", "Jest"],
        tags=["devops", "ci-cd", "testing"],
    ),
    ProjectArchetype(
        id="observability-stack",
        name="Stack de Observabilidade (Métricas + Logs + Tracing)",
        description=(
            "Implemente observabilidade completa em uma aplicação NestJS: exporte métricas "
            "com Prometheus client, logs estruturados com Winston/Pino, tracing distribuído "
            "com OpenTelemetry, configure Prometheus para coleta, Grafana para dashboards, "
            "Loki para agregação de logs, e Tempo para tracing. Crie alertas no Alertmanager "
            "e dashboards com SLOs/SLIs customizados."
        ),
        skills_developed=["Prometheus", "Grafana", "Docker", "Node.js", "NestJS", "Datadog"],
        difficulty="advanced",
        estimated_effort="4-6 semanas",
        tech_stack=["NestJS", "TypeScript", "Prometheus", "Grafana", "Loki", "Docker"],
        tags=["devops", "observability", "monitoring"],
    ),
    ProjectArchetype(
        id="serverless-migration",
        name="Migração de API REST para Arquitetura Serverless",
        description=(
            "Pegue uma API REST tradicional (NestJS/Express) e migre para serverless: "
            "API Gateway HTTP + Lambda functions com AWS SDK, Step Functions para "
            "orquestração de workflows, DynamoDB para dados de alta velocidade, S3 para "
            "documentos, e SQS para filas. Compare custos, latência (cold start), e "
            "complexidade operacional entre as versões."
        ),
        skills_developed=["Serverless", "AWS Lambda", "AWS", "REST API", "Cloud Computing"],
        difficulty="intermediate",
        estimated_effort="3-5 semanas",
        tech_stack=["AWS Lambda", "API Gateway", "Node.js", "TypeScript", "DynamoDB", "S3"],
        tags=["cloud", "serverless", "aws"],
    ),
    ProjectArchetype(
        id="gitops-argocd",
        name="GitOps com ArgoCD e Flux",
        description=(
            "Configure um fluxo GitOps completo: cluster EKS, instale ArgoCD, defina "
            "aplicações declarativas em um repo Git, configure auto-sync, sync waves, "
            "PR-based deploy previews, e integre com Kustomize ou Helm. Adicione Flux "
            "para image update automation. Inclua políticas de rollback e health checks."
        ),
        skills_developed=["Kubernetes", "Docker", "Git", "CI/CD", "Helm", "GitHub Actions"],
        difficulty="advanced",
        estimated_effort="4-6 semanas",
        tech_stack=["Kubernetes", "ArgoCD", "Helm", "Kustomize", "Docker", "Git"],
        tags=["devops", "gitops", "kubernetes"],
    ),
    ProjectArchetype(
        id="cloud-security",
        name="Segurança em Nuvem AWS (IAM, VPC, WAF, Secrets)",
        description=(
            "Implemente um overlay de segurança em uma infraestrutura AWS existente: "
            "IAM policies com least privilege, roles cross-account, VPC endpoints, "
            "Security Groups restritos, WAF com regras customizadas (SQL injection, XSS), "
            "AWS Secrets Manager para rotação de credenciais, KMS para criptografia, "
            "e AWS Config para compliance monitoring. Documente a threat model."
        ),
        skills_developed=["AWS", "Cloud Computing", "Serverless"],
        difficulty="intermediate",
        estimated_effort="3-4 semanas",
        tech_stack=["AWS", "Terraform", "Docker", "PostgreSQL"],
        tags=["cloud", "security", "aws"],
    ),
    ProjectArchetype(
        id="local-dev-env",
        name="Ambiente de Desenvolvimento Local Replicando Produção",
        description=(
            "Crie um ambiente local com Docker Compose que replica a arquitetura de produção: "
            "múltiplos serviços Node.js/NestJS, nginx como reverse proxy + load balancer, "
            "PostgreSQL + Redis, filas RabbitMQ, e volumes para dados persistentes. "
            "Inclua Docker networks isoladas, health checks, init containers para migrations, "
            "e scripts de seed. Adicione perfis docker-compose.override para dev vs prod-like."
        ),
        skills_developed=["Docker", "Nginx", "Redis", "RabbitMQ", "PostgreSQL"],
        difficulty="intermediate",
        estimated_effort="2-3 semanas",
        tech_stack=["Docker", "Docker Compose", "Nginx", "PostgreSQL", "Redis", "RabbitMQ"],
        tags=["devops", "docker", "local-dev"],
    ),
    # ── Arquitetura ───────────────────────────────────────────────────
    ProjectArchetype(
        id="ddd-cqrs-es",
        name="Sistema de Catálogo com DDD + CQRS + Event Sourcing",
        description=(
            "Modele e implemente um sistema de catálogo de produtos usando DDD: "
            "identifique bounded contexts (catálogo, estoque, preço), agregados, value objects "
            "e domain events. Separe reads (queries otimizadas com views materializadas) "
            "de writes (commands com validação de domínio). Implemente event sourcing com "
            "event store em PostgreSQL. Use NestJS com módulos por contexto delimitado."
        ),
        skills_developed=["DDD", "CQRS", "Event Sourcing", "Arquitetura hexagonal", "Design Patterns"],
        difficulty="advanced",
        estimated_effort="6-8 semanas",
        tech_stack=["NestJS", "TypeScript", "PostgreSQL", "Redis", "Docker"],
        tags=["architecture", "backend", "ddd"],
    ),
    ProjectArchetype(
        id="microservices-platform",
        name="Plataforma de Microserviços com API Gateway",
        description=(
            "Projete e implemente uma plataforma com 3-4 microserviços independentes "
            "(usuários, pedidos, pagamentos, notificações), cada um com seu próprio banco. "
            "Configure API Gateway para roteamento, autenticação centralizada (JWT), "
            "rate limiting, e versionamento. Use comunicação síncrona (REST) e assíncrona "
            "(RabbitMQ/Kafka). Inclua service discovery, circuit breaker e health checks."
        ),
        skills_developed=["Microserviços", "API Gateway", "Docker", "Message Queue", "RabbitMQ"],
        difficulty="advanced",
        estimated_effort="6-8 semanas",
        tech_stack=["NestJS", "TypeScript", "PostgreSQL", "RabbitMQ", "Docker", "Redis"],
        tags=["architecture", "backend", "microservices"],
    ),
    ProjectArchetype(
        id="event-driven-kafka",
        name="Sistema Event-Driven com Apache Kafka",
        description=(
            "Implemente um sistema de processamento de eventos usando Apache Kafka: "
            "produza eventos de domínio (pedido criado, pagamento confirmado, envio "
            "iniciado), consuma em múltiplos grupos com processamento idempotente, "
            "use Kafka Streams para agregações em tempo real, configure tópicos com "
            "particionamento por chave, retenção e compactação. Inclua schema registry "
            "com Avro e dead-letter queue para eventos com falha."
        ),
        skills_developed=["Apache Kafka", "Event Sourcing", "Microserviços", "Message Queue", "Node.js"],
        difficulty="advanced",
        estimated_effort="5-7 semanas",
        tech_stack=["Node.js", "TypeScript", "Apache Kafka", "Docker", "PostgreSQL"],
        tags=["architecture", "backend", "messaging"],
    ),
    ProjectArchetype(
        id="api-gateway-bff",
        name="API Gateway com BFF Pattern e Rate Limiting",
        description=(
            "Construa um BFF (Backend for Frontend) que centraliza chamadas para "
            "múltiplos microsserviços: autenticação JWT, cache com Redis (TTL por rota), "
            "rate limiting distribuído (sliding window no Redis), agregação de respostas "
            "paralelas, fallback com circuit breaker, e logging estruturado. Inclua "
            "Swagger/OpenAPI para documentação automatizada."
        ),
        skills_developed=["API Gateway", "REST API", "Node.js", "Redis", "JWT", "Swagger"],
        difficulty="intermediate",
        estimated_effort="3-4 semanas",
        tech_stack=["Node.js", "TypeScript", "Redis", "Docker", "Nginx"],
        tags=["architecture", "backend", "api"],
    ),
    ProjectArchetype(
        id="hexagonal-arch",
        name="Aplicação Node.js com Arquitetura Hexagonal",
        description=(
            "Implemente uma aplicação NestJS seguindo Arquitetura Hexagonal (Ports & Adapters): "
            "domínio puro sem dependências externas, portas como interfaces, adaptadores "
            "para banco (TypeORM/Prisma), API (REST), e fila (RabbitMQ). Use inversão de "
            "dependência, teste o domínio isoladamente com mock dos adaptadores, e valide "
            "que a troca de banco (PostgreSQL → MongoDB) não afeta o core."
        ),
        skills_developed=["Arquitetura hexagonal", "DDD", "Clean Architecture", "SOLID", "TDD"],
        difficulty="intermediate",
        estimated_effort="4-5 semanas",
        tech_stack=["NestJS", "TypeScript", "PostgreSQL", "Prisma", "Docker", "RabbitMQ"],
        tags=["architecture", "backend", "design"],
    ),
    ProjectArchetype(
        id="saga-pattern",
        name="Transações Distribuídas com Saga Pattern",
        description=(
            "Implemente orquestração de transações distribuídas usando Saga Pattern: "
            "modele um fluxo de e-commerce (reserva de estoque → pagamento → envio) "
            "com compensações em caso de falha (estorno, liberação de estoque). "
            "Implemente coreografia com eventos (RabbitMQ) e orquestração com Step Functions. "
            "Inclua idempotência, retry com backoff exponencial e tabela saga log."
        ),
        skills_developed=["Saga", "Message Queue", "Event Sourcing", "Microserviços", "Node.js"],
        difficulty="advanced",
        estimated_effort="5-7 semanas",
        tech_stack=["NestJS", "TypeScript", "RabbitMQ", "PostgreSQL", "Docker"],
        tags=["architecture", "backend", "distributed-systems"],
    ),
    ProjectArchetype(
        id="feature-flags",
        name="Plataforma de Feature Flags com A/B Testing",
        description=(
            "Construa uma plataforma de feature flags com: dashboard para criar/alternar "
            "flags, SDK cliente (npm package) para consumo, cache Redis para baixa latência, "
            "segmentação por usuário/percentual, integração com A/B testing (métricas de "
            "conversão), audit logging, e webhooks para sincronização em tempo real. "
            "Inclui frontend React + backend NestJS."
        ),
        skills_developed=["Design Patterns", "Redis", "Node.js", "MongoDB", "React", "REST API"],
        difficulty="intermediate",
        estimated_effort="4-6 semanas",
        tech_stack=["React", "TypeScript", "NestJS", "Redis", "PostgreSQL", "Docker"],
        tags=["architecture", "fullstack", "platform"],
    ),
    # ── Backend Engineering ───────────────────────────────────────────
    ProjectArchetype(
        id="high-perf-api",
        name="API REST com Cache Multinível e Alta Performance",
        description=(
            "Otimize uma API REST para alta performance: cache em memória (in-process), "
            "cache distribuído (Redis), compression (gzip/brotli), paginação cursor-based, "
            "connection pooling, query optimization (N+1, eager loading), response "
            "streaming, e HTTP caching (ETags, Last-Modified). Compare performance "
            "antes/depois com k6 e flamegraphs. Inclui teste de carga com relatório."
        ),
        skills_developed=["REST API", "Redis", "PostgreSQL", "Node.js", "NestJS", "Testes automatizados"],
        difficulty="advanced",
        estimated_effort="4-6 semanas",
        tech_stack=["NestJS", "TypeScript", "PostgreSQL", "Redis", "Docker", "k6"],
        tags=["backend", "performance", "api"],
    ),
    ProjectArchetype(
        id="rate-limiter",
        name="Sistema de Rate Limiting Distribuído",
        description=(
            "Implemente um sistema de rate limiting distribuído usando Redis: "
            "algoritmo sliding window log, token bucket, e fixed window counter. "
            "Crie um middleware express/nestjs configurável, dashboard de monitoramento "
            "com métricas de requests blocked/allowed, alertas para padrões anormais "
            "(possível DDoS), e suporte a diferentes planos (gratuito: 100 req/h, pro: 1000 req/h). "
            "Comparação de desempenho entre algoritmos."
        ),
        skills_developed=["Redis", "API Gateway", "Node.js", "Design Patterns", "REST API"],
        difficulty="intermediate",
        estimated_effort="3-4 semanas",
        tech_stack=["Node.js", "TypeScript", "Redis", "NestJS", "Docker"],
        tags=["backend", "api", "security"],
    ),
    ProjectArchetype(
        id="load-testing",
        name="Suite de Testes de Carga com k6 e Relatórios",
        description=(
            "Crie uma suíte completa de testes de carga usando k6: scripts de teste "
            "para cenários realísticos (usuário navegando, pico de acesso, stress test, "
            "soak test), thresholds de SLO (p95 < 500ms, erro < 1%), execução em CI/CD "
            "com GitHub Actions, relatórios HTML com gráficos, e comparação entre "
            "versões da API. Inclua dashboard Grafana para métricas em tempo real."
        ),
        skills_developed=["Testes automatizados", "CI/CD", "Node.js", "Docker", "Grafana", "Prometheus"],
        difficulty="intermediate",
        estimated_effort="2-3 semanas",
        tech_stack=["k6", "JavaScript", "Docker", "GitHub Actions", "Grafana"],
        tags=["testing", "performance", "devops"],
    ),
    ProjectArchetype(
        id="realtime-platform",
        name="Plataforma de Comunicação em Tempo Real com WebSocket",
        description=(
            "Construa uma plataforma de chat/notificações em tempo real: WebSocket "
            "(Socket.IO ou ws), salas/canais com Redis pub/sub para escala horizontal, "
            "mensagens persistentes (PostgreSQL), status online/offline, typing indicators, "
            "entregas com confirmação (ACK), e histórico com paginação. Inclui frontend "
            "React com preview de mensagens e notificações push."
        ),
        skills_developed=["WebSocket", "Redis", "Node.js", "Docker", "API Gateway", "PostgreSQL"],
        difficulty="intermediate",
        estimated_effort="4-6 semanas",
        tech_stack=["Node.js", "TypeScript", "Socket.IO", "Redis", "PostgreSQL", "React"],
        tags=["backend", "realtime", "fullstack"],
    ),
    ProjectArchetype(
        id="search-engine",
        name="Motor de Busca com Elasticsearch e Custom Scoring",
        description=(
            "Implemente um motor de busca全文 para um catálogo de produtos: "
            "indexação no Elasticsearch com mapping customizado, analyzers em português, "
            "custom scoring (function score query com recência, popularidade, relevância), "
            "autocomplete/suggest, faceted search (filtros por categoria/preço), "
            "highlighting, e synonyms. Sincronização via CDC com PostgreSQL (logical replication)."
        ),
        skills_developed=["Elasticsearch", "Node.js", "PostgreSQL", "NestJS", "Docker"],
        difficulty="advanced",
        estimated_effort="5-7 semanas",
        tech_stack=["NestJS", "TypeScript", "Elasticsearch", "PostgreSQL", "Docker"],
        tags=["backend", "search", "performance"],
    ),
    ProjectArchetype(
        id="graphql-federation",
        name="API GraphQL Federada com Apollo Federation",
        description=(
            "Implemente uma arquitetura GraphQL federada: múltiplos serviços "
            "(usuários, produtos, pedidos) cada um expondo seu próprio subgraph, "
            "Apollo Gateway como supergraph unificando os schemas, entities com "
            "@key/@extends para referência entre serviços, e query complexity analysis. "
            "Inclua federação de mutations e subscription em tempo real."
        ),
        skills_developed=["GraphQL", "Apollo GraphQL", "Node.js", "TypeScript", "Microserviços"],
        difficulty="advanced",
        estimated_effort="4-6 semanas",
        tech_stack=["Node.js", "TypeScript", "Apollo Server", "Apollo Gateway", "PostgreSQL", "Docker"],
        tags=["backend", "graphql", "api"],
    ),
    ProjectArchetype(
        id="auth-platform",
        name="Sistema de Autenticação e Autorização RBAC + ABAC",
        description=(
            "Construa um sistema de autenticação completo: registro/login com JWT + refresh "
            "tokens, OAuth2 social (Google/GitHub), RBAC (roles: admin, manager, user), "
            "ABAC (attribute-based: policy engine com regras dinâmicas), 2FA (TOTP), "
            "session management com Redis, rate limiting por usuário, e audit log "
            "de todas as ações sensíveis (login, mudança de papel, deleção)."
        ),
        skills_developed=["JWT", "OAuth", "Node.js", "PostgreSQL", "Redis", "Design Patterns"],
        difficulty="intermediate",
        estimated_effort="4-5 semanas",
        tech_stack=["NestJS", "TypeScript", "PostgreSQL", "Redis", "Docker"],
        tags=["backend", "security", "api"],
    ),
    ProjectArchetype(
        id="batch-pipeline",
        name="Pipeline de Processamento em Lote com SQS e Lambda",
        description=(
            "Implemente um pipeline de processamento em lote serverless: SQS como fila "
            "de eventos, Lambda para processamento em paralelo (com reserved concurrency), "
            "S3 para armazenamento de resultados, Step Functions para orquestração com "
            "retry e fallback, DynamoDB para checkpoint de progresso, e CloudWatch "
            "para monitoramento. Processe 10k+ itens com custo controlado."
        ),
        skills_developed=["AWS Lambda", "AWS SQS", "AWS S3", "Serverless", "Python", "Docker"],
        difficulty="intermediate",
        estimated_effort="3-4 semanas",
        tech_stack=["Python", "AWS Lambda", "AWS SQS", "AWS S3", "DynamoDB", "Docker"],
        tags=["backend", "serverless", "data-processing"],
    ),
    ProjectArchetype(
        id="webhook-gateway",
        name="Gateway de Webhooks com Retry e Observabilidade",
        description=(
            "Construa um gateway de webhooks para integrações: recebimento de eventos "
            "via POST, fila interna (RabbitMQ) para processamento assíncrono, entrega "
            "para múltiplos destinatários configuráveis, retry com backoff exponencial "
            "(3 tentativas + dead-letter), idempotência (idempotency key), validação de "
            "assinatura HMAC, dashboard de entregas (sucesso/falha/latência), e "
            "webhook logs com replay manual."
        ),
        skills_developed=["REST API", "Redis", "PostgreSQL", "Message Queue", "Node.js", "NestJS"],
        difficulty="intermediate",
        estimated_effort="3-5 semanas",
        tech_stack=["NestJS", "TypeScript", "Redis", "RabbitMQ", "PostgreSQL", "Docker"],
        tags=["backend", "api", "integration"],
    ),
]
