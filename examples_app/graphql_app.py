from qakeapi import Application, Response
from qakeapi.api.graphql import QakeGraphQL, get_default_schema

app = Application(title="QakeAPI GraphQL Example", version="1.0.0")

type_defs, resolvers = get_default_schema()
gql = QakeGraphQL(type_defs, resolvers, playground=True)

# Монтируем GraphQL endpoint
app.mount("/graphql", gql.asgi_app())

@app.get("/")
async def root(request):
    return Response.json({
        "message": "QakeAPI GraphQL Example",
        "graphql": "/graphql",
        "docs": "/graphql (GraphQL Playground)",
        "features": ["Query", "Mutation", "Subscription"]
    })

if __name__ == "__main__":
    import uvicorn
    print("🚀 QakeAPI GraphQL Example running at http://localhost:8030/graphql")
    uvicorn.run(app, host="127.0.0.1", port=8030) 