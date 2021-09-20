import { Observable } from 'rxjs'
import { graphqlStreamClient } from '@barejs/graphql-client'

export default function graphqlObservableStreamClient(
  url,
  init,
  query,
  variables,
  operation
) {
  return new Observable(subscriber => {
    return graphqlStreamClient(
      url,
      init,
      query,
      variables,
      operation,
      response => subscriber.next(response),
      error => subscriber.error(error),
      () => subscriber.complete()
    )
  })
}
