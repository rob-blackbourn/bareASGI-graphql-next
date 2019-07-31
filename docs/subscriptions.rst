Subscriptions
=============


Overview
--------

Two transport mechanisms are provided for GraphQL subscriptions:

* WebSockets
* Server Side Events

WebSockets
----------

Subscriptions can be made over web sockets implementing the
`Apollo GraphQL <https://www.apollographql.com/>`_
transport
`protocol <https://github.com/apollographql/subscriptions-transport-ws/blob/master/PROTOCOL.md?source=post_page--------------------------->`_.
This seems to be the most widely supported and is ccompatibly with the majority of javascript front ends. It has been
tested with `@jetblack/graphql-client <https://www.npmjs.com/package/@jetblack/graphql-client>`_, the implementation
of which is discussed `here <https://medium.com/@rob.blackbourn/writing-a-graphql-websocket-subscriber-in-javascript-4451abb9cd60>`_,
and also by the inbuilt `GraphiQL IDE <https://github.com/graphql/graphiql>`_.

Server Sent Event Subscriptions
-------------------------------

As well as the more popular :doc:`WebSocket Subscription </ws_subscriptions>`, a mechanism using
`server sent events <https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events>`_
is also supported. While this is uncommon, it is a really good use of SSE, as all the communication
if from the server to the client.

In this implementation queries, mutations and subscriptions are all made using the `fetch` api.
With a successful query or mutation the response status code is 200, and the body contains the
result. For a subscription the status code 201 is returned, and the `location` header contains
a unique url which is used to request server sent events through the
`EventSource <https://developer.mozilla.org/en-US/docs/Web/API/EventSource>`_ API.

Usage
-----

Server sent events are paricularly simple to use from the browser. Here is some sample code
that can be used in the browser:

.. code-block:: js

    function fetchGraphQL(query, variables, operationName, signal, onError, onSuccess) {
      fetch('https://www.example.com/graphql', {
        method: 'POST',
        signal,
        body: JSON.stringify({
          query,
          variables,
          operationName
        })
      })
        .then(response => {
          if (response.status == 200) {

            // This is a query result, so just show the data.
            response.json()
              .then(data => onSuccess(data))
              .catch(error => onError(error))

          } else if (response.status == 201) {

            // This is a subscription response. An endpoint is
            // returned in the "Location" header which we can
            // consume with an EventSource.
            var location = response.headers.get('location')
            eventSource = new EventSource(location)

            // Handle cancellation with AbortController.signal.onabort
            signal.onabort = function() {
              if (eventSource.readyState !== 2) {
                eventSource.close()
              }
            }

            // Consume the messages.
            eventSource.onmessage = function(event) {
              onSuccess(JSON.parse(event.data))
            }

          } else {
            onError(new Error("Unhandled response"))
          }
        })
        .catch(error => onError(error))

