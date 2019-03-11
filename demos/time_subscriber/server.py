from bareasgi import Application
from bareasgi_graphql_next import add_graphql_next
import logging
from time_subscriber.time_schema import schema

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
import uvicorn

app = Application()
add_graphql_next(app, schema)

uvicorn.run(app, port=9009)
