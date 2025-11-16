"""GraphQL API module"""
from app.graphql.schema import create_graphql_router, schema

__all__ = ["create_graphql_router", "schema"]
