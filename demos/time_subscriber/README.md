Time Subscriber
===============

An example subscriber.

Ensure you have uvicorn installed, start server and browse to http:127.0.0.1:9009/graphiql

The only query that make sense with the schema is:

```graphql
subscription {
  time
}
```