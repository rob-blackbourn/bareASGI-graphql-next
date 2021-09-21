# GraphQL with bareASGI

GraphQL support for [bareASGI](https://bareasgi.readthedocs.io/en/latest).

Endpoints are provided for:

* graphql queries, mutations and subscriptions,
* A graphiql app (browse to /graphiql).

Note this uses the [graphql-core-next](https://github.com/graphql-python/graphql-core-next) GraphQL implementation.

There is also optional support for [graphene](https://github.com/graphql-python/graphene),
using a temporary [fork](https://github.com/rob-blackbourn/graphene/tree/feature/add_subscription)
which adds subscription support.