# AgentHub Documentation

Welcome to the AgentHub documentation. This guide helps you find the right documentation for your needs.

---

## Quick Navigation

| I want to... | Go to |
|--------------|-------|
| **Understand the architecture** | [developers/architecture/](developers/architecture/) |
| **Write or run tests** | [developers/testing/](developers/testing/) |
| **Learn implementation patterns** | [developers/guides/](developers/guides/) |
| **Set up development environment** | [operators/deployment/](operators/deployment/) |
| **Configure monitoring** | [operators/observability/](operators/observability/) |
| **Secure the application** | [operators/security/](operators/security/) |
| **View project roadmap** | [project/planning/](project/planning/) |
| **Read architecture decisions** | [project/decisions/](project/decisions/) |

---

## Documentation Map

```
docs/
├── developers/                  # For contributors and developers
│   ├── architecture/            # System design, layers, data flow
│   ├── testing/                 # TDD, test pyramid, fake adapters
│   ├── workflows/               # Git, CI/CD, automation hooks
│   └── guides/                  # Implementation recipes, patterns
│
├── operators/                   # For deployers and operators
│   ├── deployment/              # Installation, configuration, running
│   ├── observability/           # Logging, LLM tracking, metrics
│   └── security/                # Token auth, CORS, OAuth
│
└── project/                     # For project management
    ├── archive/                 # Completed phases, deprecated docs
    ├── decisions/               # Architecture Decision Records (ADR)
    └── planning/                # Roadmap, phase plans
```

---

## Quick Links

| Resource | Description |
|----------|-------------|
| [Installation Guide](operators/deployment/) | Set up AgentHub locally |
| [Architecture Overview](developers/architecture/) | Hexagonal architecture, domain model |
| [Contributing](project/) | Development process, code review |
| [Project Status](../README.md) | Current phase, coverage, next actions |

---

## By Audience

### Developers

New to the codebase? Start here:

1. **[Architecture](developers/architecture/)** - Understand the hexagonal layers
2. **[Testing](developers/testing/)** - Learn TDD with fake adapters
3. **[Guides](developers/guides/)** - Follow implementation recipes

### Operators

Setting up AgentHub? Start here:

1. **[Deployment](operators/deployment/)** - Install and configure
2. **[Security](operators/security/)** - Set up authentication
3. **[Observability](operators/observability/)** - Configure monitoring

### Project Managers

Tracking progress? Start here:

1. **[Planning](project/planning/)** - View roadmap and phases
2. **[Decisions](project/decisions/)** - Read ADRs
3. **[Archive](project/archive/)** - Review completed work

---

## Related Resources

- [Root README](../README.md) - Project overview and quick start
- [CLAUDE.md](../CLAUDE.md) - AI assistant instructions
- [Tests README](../tests/README.md) - Test configuration and execution

---

*Last Updated: 2026-02-05*
