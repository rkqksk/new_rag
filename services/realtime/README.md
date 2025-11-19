# Realtime Service (Planned)

**Status**: 🚧 Scaffold Only - Not Production Ready

## Current State

This is a placeholder directory for future microservice extraction. The Realtime service is currently **not functional** and exists only as a structural placeholder.

## Actual Implementation

👉 **All realtime functionality currently lives in `apps/api/`**

- Socket.IO WebSocket integration (built into FastAPI)
- Redis Pub/Sub for horizontal scaling
- PostgreSQL LISTEN/NOTIFY for database events
- Room-based connection management
- Event broadcasting and messaging

## Planned Features (Future Extraction)

When extracted as a microservice, this service will handle:

- WebSocket connections via Socket.IO
- Redis Pub/Sub for scaling across multiple instances
- PostgreSQL LISTEN/NOTIFY for database-triggered events
- Room-based broadcasting and targeted messaging
- Connection pooling and state management
- Presence/activity tracking
- Message queuing and reliable delivery
- Namespace isolation for multi-tenant scenarios

## Roadmap

- **Phase 1**: Consolidate realtime logic in `apps/api/` (Current)
- **Phase 2**: Extract to standalone service (Post-v10.0.0)
- **Phase 3**: Scale with distributed broker (Redis Cluster)
- **Phase 4**: Deploy independently with load balancing

Estimated extraction: **Q2 2025** (After v10 stabilization)

See `docs/planning/MICROSERVICES_ROADMAP.md` for complete strategy.

## DO NOT USE

**This service is not functional and will return errors if deployed.**

- No implementation files
- No Socket.IO handlers
- No WebSocket endpoints
- No event broadcasting

## Related Documentation

- **Realtime Backend Architecture**: `docs/REALTIME_BACKEND_GUIDE.md`
- **Socket.IO Integration**: `apps/api/core/realtime/`
- **API Endpoints**: `docs/reference/API_DOCUMENTATION.md`

---

**Last Updated**: 2025-11-19  
**Target Extraction**: Post-v10.0.0
