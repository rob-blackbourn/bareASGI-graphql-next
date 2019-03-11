from bareasgi import Application
from bareasgi_graphql_next import add_graphql_next
from time_subscriber.time_schema import schema

import uvicorn

app = Application()
add_graphql_next(app, schema)

uvicorn.run(app, port=9009)
