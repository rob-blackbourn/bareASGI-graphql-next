GraphQL with bareASGI
=================================

GraphQL support for `bareASGI <https://bareasgi.readthedocs.io/en/latest>`_.

Endpoints are provided for:

* graphql queries, mutations and subscriptions,
* A graphiql app (browse to /graphiql).

Note this uses the `graphql-core-next <https://github.com/graphql-python/graphql-core-next>`_ GraphQL implementation.

Installation
------------

The package can be installed with pip.

.. code-block:: bash

    pip install bareasgi-graphql-next

This is a Python 3.7 and later package with dependencies on:

* bareASGI
* graphql-core-next

Usage
-----

A utility function `add_graphql_next` is provided.

.. code-block:: python

    from bareasgi import Application
    from bareasgi_graphql_next import add_graphql_next
    from star_wars.star_wars_schema import star_wars_schema

    import uvicorn

    app = Application()
    add_graphql_next(app, star_wars_schema)

    uvicorn.run(app, port=9009)

.. toctree::
    :maxdepth: 2
    :caption: Contents:

    api
    ws_subscriptions
    sse_subscriptions

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

