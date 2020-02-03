# Usage

A utility function `add_graphql_next` is provided.

```python
from bareasgi import Application
from bareasgi_graphql_next import add_graphql_next
from star_wars.star_wars_schema import star_wars_schema

import uvicorn

app = Application()
add_graphql_next(app, star_wars_schema)

uvicorn.run(app, port=9009)
```
