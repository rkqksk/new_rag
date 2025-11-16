# Services

Microservices for RAG Enterprise v10.0.0

## Structure

```
services/
├── rag/              # RAG engine service
├── collector/        # Data collection service
├── manufacturing/    # Manufacturing AI service
├── realtime/         # Realtime backend service
└── ml/               # MLflow experiment tracking
```

## Service Pattern

Each service follows this structure:

```
service-name/
├── package.json      # Service metadata
├── README.md         # Service documentation
├── src/             # Source code
├── tests/           # Service tests
└── config/          # Service configuration
```

## Development

```bash
# Install dependencies
pnpm install

# Run specific service
pnpm --filter @rag/service-name dev

# Build all services
pnpm build
```

## Integration

Services communicate via:
- **REST APIs**: FastAPI endpoints
- **Message Queue**: Kafka
- **Database**: PostgreSQL + Redis
- **Vector Store**: Qdrant

## Version

10.0.0 - Unified Maximum
