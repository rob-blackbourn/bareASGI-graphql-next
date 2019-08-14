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

Server Sent Events
------------------

As well as the more popular :doc:`WebSocket Subscription </ws_subscriptions>`, a mechanism using
`server sent events <https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events>`_
is also supported. While this is uncommon, it is a really good use of SSE, as all the communication
if from the server to the client.

Usage
-----

The GraphQL controller exposes an endpoint: `/sse-subscription?query=...&variables=...&operationName=...`

This can be called in the following manner:

.. code-block:: js

    const query = encodeURIComponent('subscription { mySubscription { name timestamp } }')
    const url = `http://www.example.com/sse-subscription?query=${query}`
    const eventSource = new EventSource(url)
    eventSource.onmessage = event => {
        data = JSON.parse(event.data)
        console.log(data)
    }

In this implementation queries, mutations and subscriptions can all be made using the `fetch` api.
With a successful query or mutation the response status code is 200 (OK), and the body contains the
result. For a subscription the status code 201 (CREATED) is returned, and the `location` header contains
the url to be used to request server sent events through the
`EventSource <https://developer.mozilla.org/en-US/docs/Web/API/EventSource>`_ API.

This means we can provide a single client function to handle all three requests. Here is some sample code that does this.

.. code-block:: js

    export class FetchError extends Error {
      constructor(response, ...params) {
        super(...params)

        if (Error.captureStackTrace) {
          Error.captureStackTrace(this, FetchError)
        }

        this.name = 'FetchError'
        this.response = response
      }
    }

    export function graphQLClient(url, query, variables, operationName, onNext, onError, onComplete) {
      const abortController = new AbortController()

      // Invoke fetch as a POST with the GraphQL content in the body.
      fetch(url, {
        method: 'POST',
        signal: abortController.signal,
        body: JSON.stringify({
          query,
          variables,
          operationName
        })
      })
        .then(response => {
          if (response.status === 200) {
            // A 200 response is from a query or mutation.

            response.json()
              .then(json => {
                onNext(json)
                onComplete()
              })
              .catch(error => onError(error))

          } else if (response.status === 201) {
            // A 201 is the response for a subscription.

            // The url for the event source is passed in the 'location' header.
            const location = response.headers.get('location')
            
            const eventSource = new EventSource(location)

            eventSource.onmessage = event => {
              console.log('EventSource:onmessage', event)
              const data = JSON.parse(event.data)
              onNext(data)
            }

            eventSource.onerror = error => {
              console.log('EventSource:onerror', error)
              onError(error)
            }

            abortController.signal.onabort = () => {
              console.log('AbortController: onabort')
              if (eventSource.readyState !== 2) {
                eventSource.close()
              }
            }
          } else {
            onError(new FetchError(response, 'Failed to execute GraphQL'))
          }

        })
        .catch(error => onError(error))

      // Return an unsubscribe function.
      return () => {
        console.log('unsubscribing')
        abortController.abort()
      }
    }
