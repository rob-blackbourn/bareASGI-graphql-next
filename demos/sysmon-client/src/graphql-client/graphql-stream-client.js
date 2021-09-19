/* global TransformStream */

import mergeDeep from './merge-deep'

function makeWriteableStream(onNext, onError, onComplete) {
  return new WritableStream({
    write(chunk, controller) {
      onNext(chunk)
    },
    close(controller) {
      onComplete()
    },
    abort(reason) {
      if (reason.name === 'AbortError') {
        onComplete()
      } else {
        onError(reason)
      }
    }
  })
}

function makeLineDecoder() {
  // eslint-disable-next-line no-undef
  return new TransformStream({
    start(controller) {
      controller.buf = ''
      controller.pos = 0
    },
    transform(chunk, controller) {
      controller.buf += chunk
      while (controller.pos < controller.buf.length) {
        if (controller.buf[controller.pos] === '\n') {
          const line = controller.buf.substring(0, controller.pos)
          if (line !== '') {
            controller.enqueue(line)
          }
          controller.buf = controller.buf.substring(controller.pos + 1)
          controller.pos = 0
        } else {
          ++controller.pos
        }
      }
    },
    flush(controller) {
      if (controller.pos !== 0) {
        controller.enqueue(controller.buf)
      }
    }
  })
}

/**
 * A GraphQL client using a streaming fetch. This can support Query, Mutation, and Subscription.
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
export default function graphqlStreamClient(
  url,
  init,
  query,
  variables,
  operationName,
  onNext,
  onError,
  onComplete
) {
  const abortController = new AbortController()

  init = mergeDeep(
    {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        accept: 'application/json',
        allow: 'POST'
      },
      body: JSON.stringify({
        query,
        variables,
        operationName
      }),
      signal: abortController.signal
    },
    init
  )

  fetch(url, init)
    .then(response => {
      if (response.status === 200) {
        // A streaming response is a subscription.
        const lineDecoder = makeLineDecoder()
        const writeableStream = makeWriteableStream(onNext, onError, onComplete)

        response.body
          // eslint-disable-next-line no-undef
          .pipeThrough(new TextDecoderStream())
          .pipeThrough(lineDecoder)
          // eslint-disable-next-line no-undef
          .pipeThrough(
            new TransformStream({
              transform(chunk, controller) {
                controller.enqueue(JSON.parse(chunk))
              }
            })
          )
          .pipeTo(writeableStream)
          .catch(() => {
            // Errors are handled in the writeable stream
          })
      } else {
        onError(new Error('Unhandled response'))
      }
    })
    .catch(error => {
      onError(error)
    })

  // Return a method to stop the request.
  return () => abortController.abort()
}
