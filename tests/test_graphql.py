import pytest
import httpx
import asyncio

GRAPHQL_URL = "http://127.0.0.1:8030/graphql"

@pytest.mark.asyncio
async def test_graphql_query():
    query = '{ hello }'
    async with httpx.AsyncClient() as client:
        resp = await client.post(GRAPHQL_URL, json={"query": query})
        data = resp.json()
        assert resp.status_code == 200
        assert data["data"]["hello"] == "Hello from QakeAPI GraphQL!"

@pytest.mark.asyncio
async def test_graphql_mutation():
    query = 'mutation { echo(message: "test") }'
    async with httpx.AsyncClient() as client:
        resp = await client.post(GRAPHQL_URL, json={"query": query})
        data = resp.json()
        assert resp.status_code == 200
        assert data["data"]["echo"] == "test"

# Для subscriptions нужен отдельный тест с websockets, если поддерживается 