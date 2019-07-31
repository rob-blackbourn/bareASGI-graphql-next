Server Sent Event Subscriptions
===============================

Overview
--------

As well as the more popular :doc:`WebSocket Subscription </ws_subscriptions>`, a mechanism using
`server sent events <https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events>`_
is also supported.

Usage
-----

Server sent events are paricularly simple to use from the browser. Here is some sample code
that can be used in the browser:

.. code-block:: js

    function fetchGraphQL(query, variables, operationName, onError, onSuccess) {
      fetch('https://www.example.com/graphql', {
        method: 'POST',
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
            eventSource.onmessage = function(event) {
              onSuccess(JSON.parse(event.data))
            }

          } else {
            onError(new Error("Unhandled response"))
          }
        })
        .catch(error => onError(error))

Note that we can use fetch for both the query and the subscription, with the only addition
being the event source.