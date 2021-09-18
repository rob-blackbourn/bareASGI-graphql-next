import FetchError from './fetch-error'
import mergeDeep from './merge-deep'
import graphqlWsSubscriber from './graphql-ws-subscriber'

/**
 * A GraphQL client using web sockets for subscriptions. This can handle Query, Mutation and Subscription.
 * @param {string} url - The GraphQL url.
 * @param {Object} init - Additional parameters passed to fetch.
 * @param {string} query - The GraphQL query.
 * @param {Object} [variables] - Any variables required by the query.
 * @param {string} [operationName] - The name of the operation to invoke,
 * @param {function} onNext - The function called when data is provided.
 * @param {function} onError - The function called when an error occurs.
 * @param {function} onComplete - The function called when the operation has completed.
 * @returns {function} - A function that can be called to terminate the operation.
 */
export default function graphqlWsClient (url, init, query, variables, operationName, onNext, onError, onComplete) {
  const abortController = new AbortController()
  init = mergeDeep({
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      accept: 'application/json'
    },
    body: JSON.stringify({
      query,
      variables,
      operationName
    }),
    signal: abortController.signal
  }, init)

  // Invoke fetch as a POST with the GraphQL content in the body.
  fetch(url, init)
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
        const index = location.indexOf('?')
        const wsUrl = 'ws' + location.slice(4, index === -1 ? undefined : index)

        const unsubscribe = graphqlWsSubscriber(wsUrl, query, variables, operationName, onNext, onError, onComplete)

        abortController.signal.onabort = () => {
          unsubscribe()
        }
      } else {
        onError(new FetchError(response, 'Failed to execute GraphQL'))
      }
    })
    .catch(error => {
      onError(error)
    })

  // Return an unsubscribe function.
  return () => {
    abortController.abort()
  }
}
