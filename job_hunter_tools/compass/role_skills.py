from __future__ import annotations

ROLE_SKILLS: dict[str, list[str]] = {
    "Tech Lead": [
        "Liderança", "Comunicação", "Mentoria",
        "Microserviços", "Clean Architecture", "Scrum", "DDD",
        "Tomada de decisão", "Gestão de tempo", "Comunicação escrita",
    ],
    "Staff Engineer": [
        "Arquitetura hexagonal", "DDD", "CQRS", "Event Sourcing",
        "Design Patterns", "Clean Architecture", "Mentoria",
        "Comunicação escrita", "SOLID", "Microserviços",
    ],
    "Cloud Architect": [
        "AWS", "Kubernetes", "Terraform", "Docker",
        "Cloud Computing", "Microserviços", "Serverless",
        "CI/CD", "Prometheus", "Grafana",
    ],
    "Engineering Manager": [
        "Liderança", "Comunicação", "Mentoria", "Scrum",
        "Gestão de tempo", "Tomada de decisão", "Negociação",
        "Ágil", "Kanban", "Trabalho em equipe",
    ],
    "Solutions Architect": [
        "Arquitetura hexagonal", "DDD", "Microserviços",
        "AWS", "Cloud Computing", "Design Patterns",
        "REST API", "GraphQL", "Comunicação", "Comunicação escrita",
    ],
    "Principal Engineer": [
        "Arquitetura hexagonal", "DDD", "CQRS", "Event Sourcing",
        "Design Patterns", "Clean Architecture", "Mentoria",
        "Comunicação escrita", "Microserviços", "Apache Kafka",
        "Saga", "Serverless", "Cloud Computing",
    ],
}
