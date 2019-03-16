# bareASGI-graphql-next

Graphql support for [bareASGI](http://github.com/rob-blackbourn/bareasgi) (read the [documentation](https://bareasgi-graphql-next.readthedocs.io/en/latest/))

The controller provides a GraphQL GET and POST route, a WebSocket subscription server, and a Graphiql view.

## Installation

Install from the pie shop.

```bash
pip install bareasgi-graphql-next
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

