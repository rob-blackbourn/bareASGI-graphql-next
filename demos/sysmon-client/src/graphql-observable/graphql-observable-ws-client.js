import { Observable } from 'rxjs'
import { graphqlWsClient } from '@barejs/graphql-client'

export default function graphqlObservableWsClient(
  url,
  init,
  query,
  variables,
  operationName
) {
  return new Observable(subscriber => {
    return graphqlWsClient(
      url,
      init,
      query,
      variables,
      operationName,
      response => subscriber.next(response),
      error => subscriber.error(error),
      () => subscriber.complete()
    )
  })
}
