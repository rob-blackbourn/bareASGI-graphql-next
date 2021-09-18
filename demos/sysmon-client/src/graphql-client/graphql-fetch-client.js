import FetchError from './fetch-error'
import mergeDeep from './merge-deep'

/**
 * A simple fetch-based GraphQL client. This can handle Query and Mutation.
 * @param {string} url - The GraphQL query endpoint.
 * @param {Object} init - Any additional parameters for fetch.
 * @param {string} query - The GraphQL query.
 * @param {Object} [variables] - Any GraphQL variables.
 * @param {string} [operationName] - The name of the operation to invoke.
 * @param {function} onError - The function called when an error has occurred.
 * @param {function} onSuccess - The function called when the query has been successfully invoked.
 * @returns {function} - A function that can be called to terminate the operation.
 */
export default function graphqlFetchClient (url, init, query, variables, operationName, onError, onSuccess) {
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
    signal: abortController.signal,
  }, init)

  fetch(url, init)
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

  // Return a function to abort the fetch.
  return () => {
    abortController.abort()
  }
}
