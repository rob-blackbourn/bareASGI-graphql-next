# bareASGI-graphql-next

Graphql support for [bareASGI](http://github.com/rob-blackbourn/bareASGI) (read the [documentation](https://rob-blackbourn.github.io/bareASGI-graphql-next/))

The controller provides a GraphQL GET and POST route, a WebSocket subscription server, and a Graphiql view.

## Installation

Install from the pie shop.

```bash
pip install bareasgi-graphql-next
```

If you wish to install with the grapheme option:

```bash
pip install 'bareasgi-graphql-next[graphene]'
```

## Usage

You can register the graphql controller with the `add_graphql_next` function.

```python
from bareasgi import Application
from bareasgi_graphql_next import add_graphql_next
import graphql

# Get the schema ...
schema = graphql.GraphQLSchema( ... )

import uvicorn

app = Application()
add_graphql_next(app, schema)

uvicorn.run(app, port=9009)

```

## Development

To develop with the graphene optional package:

```bash
poetry install --extras graphene
```
