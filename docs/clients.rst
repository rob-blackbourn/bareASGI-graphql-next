*******
Clients
*******

Overview
########

GraphQL supports three types of *actions*:

- Queries
- Mutations
- Subscriptions


Queries & Mutations
###################

The controller exposes an endpoint ``/graphql``. There are a number of libraries that can be used
including `Facebook Relay <https://github.com/facebook/relay>`_
and `Apollo GraphQL <https://www.apollographql.com/>`_. These are feature rich, but the underlying
mechanism for queries and mutations is just a simple ``fetch`` request.

Here is a code snippet demonstrating a query.

.. code-block:: js

    const query = 'query { myQuery { someField otherField } }'
    const variables = null
    const operationName = null

    const url = 'http://www.exammple.com/graphql'

    // Invoke fetch as a POST with the GraphQL content in the body.
    fetch(url, {
      method: 'POST',
      body: JSON.stringify({
        query,
        variables,
        operationName
      })
    })
      .then(response => response.json())
      .then(data => console.log(data)
      .catch(error => console.log(error))

We might wrap this up in the following function:

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

    export function graphQLClient(url, query, variables, operationName, onError, onSuccess) {
      // Invoke fetch as a POST with the GraphQL content in the body.
      fetch(url, {
        method: 'POST',
        body: JSON.stringify({
          query,
          variables,
          operationName
        })
      })
        .then(response => {
          if (response.ok) {
            response.json()
              .then(json => {
                onSuccess(json)
              })
              .catch(error => onError(error))
          } else {
            onError(new FetchError(response, 'Failed to execute GraphQL'))
          }
        })
        .catch(error => onError(error))
    }

This can then be called like this:

.. code-block:: js

    const url = 'http://www.example.com/graphql'
    const query = 'query { someQuery { someField someOtherField } }'
    const variables = null
    const operationName = null

    graphQLClient(
      url,
      query,
      variables,
      operationName,
      error => console.error(error),
      data => console.log(data))


Subscriptions
#############

Two transport mechanisms are provided for GraphQL subscriptions:

* WebSockets
* Server Sent Events

WebSockets
**********

Subscriptions can be made over WebSockets implementing the 
`Apollo GraphQL transport protocol <https://github.com/apollographql/subscriptions-transport-ws/blob/master/PROTOCOL.md?source=post_page--------------------------->`_
using the ``/subscriptions`` endpoint. This seems to be the most widely used
mechanism and is compatible with the majority of javascript front libraries.

The implementation of the JavaScript WebSocket client is too complex to describe here, but
there is an implementation in `@jetblack/graphql-client <https://github.com/rob-blackbourn/jetblack-graphql-client`_,
the implementation of which is discussed `here <https://medium.com/@rob.blackbourn/writing-a-graphql-websocket-subscriber-in-javascript-4451abb9cd60>`_.

This is the protocol used by the inbuilt `GraphiQL IDE <https://github.com/graphql/graphiql>`_.

Server Sent Events
******************

As well as the more popular :doc:`WebSocket Subscription </ws_subscriptions>`, a mechanism using
`server sent events <https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events>`_
is also supported. While this is uncommon, it is a really good use of SSE, as all the communication
if from the server to the client.

The GraphQL controller exposes an endpoint: ``/sse-subscription?query=...&variables=...&operationName=...``

This can be called in the following manner:

.. code-block:: js

    const query = encodeURIComponent('subscription { mySubscription { name timestamp } }')
    const url = `http://www.example.com/sse-subscription?query=${query}`
    const eventSource = new EventSource(url)
    eventSource.onmessage = event => {
        data = JSON.parse(event.data)
        console.log(data)
    }

We could wrap this up in the following manner:

.. code-block:: js

    export function graphQLSubscriber(url, query, variables, operationName, onError, onSuccess) {
      let subscriptionUrl = url + '?query=' + encodeURIComponent(query)
      if (variables) {
        subscriptionUrl += '&variables=' + encodeURIComponent(JSON.stringify(variables))
      }
      if (operationName) {
        subscriptionUrl += '&operationName=' + encodeURIComponent(operationName)
      }

      const eventSource = new EventSource(subscriptionUrl)
      eventSource.onmessage = event => onSuccess(JSON.parse(event.data))
      eventSource.onerror = error => onError(error)
      // Return the close function to unsubscribe.
      return eventSource.close
    }

This can then be called like this:

.. code-block:: js

    const url = 'http://www.example.com/sse-subscription'
    const query = 'subscription { someSubscription { someField someOtherField } }'
    const variables = null
    const operationName = null

    graphQLSubscriber(
      url,
      query,
      variables,
      operationName,
      error => console.error(error),
      data => console.log(data))

Queries, Mutations & Subscriptions
##################################

In this implementation queries, mutations and subscriptions can **all** be made using the ``fetch`` api.
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
              const data = JSON.parse(event.data)
              onNext(data)
            }

            eventSource.onerror = error => {
              onError(error)
            }

            abortController.signal.onabort = () => {
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
        abortController.abort()
      }
    }
This can then be called like this:

.. code-block:: js

    const url = 'http://www.example.com/graphql'
    
    // This could be a query, mutation or subscription.
    const query = 'subscription { someSubscription { someField someOtherField } }'
    const variables = null
    const operationName = null

    const unsubscribe = graphQLClient(
      url,
      query,
      variables,
      operationName,
      data => console.log(data),
      error => console.log(error),
      () => console.log('complete'))

    // Later ...
    unsubscribe()


Observable
**********

Clearly the above code roles it's own *observable* pattern. We can wrap this up with rxjs
to provide a cleaner client.

.. code-block:: js

    import { Observable } from 'rxjs'

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

    export function observableGraphQL(url, query, variables, operationName) {
      return Observable.create(observer => {
        const abortController = new AbortController()

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
                  observer.next(json)
                  observer.complete()
                })
                .catch(error => observer.error(error))

            } else if (response.status === 201) {
              // A 201 is the response for a subscription.

              // The url for the event source is passed in the 'location' header.
              const location = response.headers.get('location')

              const eventSource = new EventSource(location)

              eventSource.onmessage = event => {
                observer.next(JSON.parse(event.data))
              }

              eventSource.onerror = error => {
                observer.error(error)
              }

              abortController.signal.onabort = () => {
                if (eventSource.readyState !== 2) {
                  eventSource.close()
                }
              }
            } else {
              observer.error(new FetchError(response, 'Failed to execute GraphQL'))
            }
          })
          .catch(error => observer.error(error))

        // Return the unsubscribe function.
        return () => {
          abortController.abort()
        }
      })
    }

This can then be called like this:

.. code-block:: js

    const url = 'http://www.example.com/graphql'

    // This could be a query, mutation or subscription.
    const query = 'subscription { someSubscription { someField someOtherField } }'
    const variables = null
    const operationName = null

    const subscription = observableGraphQL(
      url,
      query,
      variables,
      operationName)
      .subscribe({
        next: responses => console.log(response),
        error: error => console.log(error),
        complete: () => console.log('complete')
      })

    // Later ...
    subscription.unsubscribe()

