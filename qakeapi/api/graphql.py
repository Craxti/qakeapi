from ariadne import QueryType, MutationType, SubscriptionType, make_executable_schema, graphql_sync, load_schema_from_path
from ariadne.asgi import GraphQL
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
import os

# SOLID: Single Responsibility — отдельный класс для GraphQL API
class QakeGraphQL:
    def __init__(self, type_defs, resolvers, playground: bool = True):
        self.schema = make_executable_schema(type_defs, *resolvers)
        self.app = GraphQL(self.schema, debug=True)

    def asgi_app(self):
        return self.app

# Пример схемы и резолверов
query = QueryType()
mutation = MutationType()
subscription = SubscriptionType()

@query.field("hello")
def resolve_hello(_, info):
    return "Hello from QakeAPI GraphQL!"

@mutation.field("echo")
def resolve_echo(_, info, message):
    return message

@subscription.source("countdown")
async def countdown_generator(obj, info, from_: int):
    for i in range(from_, 0, -1):
        yield i

@subscription.field("countdown")
def countdown_resolver(count, info):
    return count

def get_default_schema():
    type_defs = """
    type Query {
        hello: String!
    }
    type Mutation {
        echo(message: String!): String!
    }
    type Subscription {
        countdown(from_: Int!): Int!
    }
    """
    return type_defs, [query, mutation, subscription] 