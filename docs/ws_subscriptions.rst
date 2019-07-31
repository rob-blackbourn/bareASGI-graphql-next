WebSocket Subscriptions
=======================

Overview
--------

Subscriptions can be made over web sockets implementing the
`Apollo GraphQL <https://www.apollographql.com/>`_
transport
`protocol <https://github.com/apollographql/subscriptions-transport-ws/blob/master/PROTOCOL.md?source=post_page--------------------------->`_.
This seems to be the most widely supported and is ccompatibly with the majority of javascript front ends. It has been
tested with `@jetblack/graphql-client <https://www.npmjs.com/package/@jetblack/graphql-client>`_, the implementation
of which is discussed `here <https://medium.com/@rob.blackbourn/writing-a-graphql-websocket-subscriber-in-javascript-4451abb9cd60>`_,
and also by the inbuilt `GraphiQL IDE <https://github.com/graphql/graphiql>`_.
