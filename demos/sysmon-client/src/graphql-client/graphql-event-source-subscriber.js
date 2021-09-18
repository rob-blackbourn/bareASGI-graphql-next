/**
 * A GraphQL subscription client using server sen events.
 * @param {string} url - The GraphQL url.
 * @param {string} query - The GraphQL query.
 * @param {Object} [variables] - Any GraphQL variables.
 * @param {string} [operationName] - The name of the operation to invoke,
 * @param {function} onNext - Called when the operation provides data.
 * @param {function} onError - Called when the operation has raised an error.
 * @param {function} onComplete - Called when the operation has completed.
 * @returns {function} - A function which can be called to terminate the operation.
 */
export default function graphqlEventSourceSubscriber (url, query, variables, operationName, onNext, onError, onComplete) {
  let subscriptionUrl = url + '?query=' + encodeURIComponent(query)
  if (variables) {
    subscriptionUrl += '&variables=' + encodeURIComponent(JSON.stringify(variables))
  }
  if (operationName) {
    subscriptionUrl += '&operationName=' + encodeURIComponent(operationName)
  }

  const eventSource = new EventSource(subscriptionUrl)

  eventSource.onmessage = event => {
    const data = JSON.parse(event.data)
    onNext(data)
  }

  eventSource.onerror = error => {
    onError(error)
  }

  const abortController = new AbortController()
  abortController.signal.onabort = () => {
    if (eventSource.readyState !== 2) {
      eventSource.close()
      onComplete()
    }
  }

  return abortController.abort
}
