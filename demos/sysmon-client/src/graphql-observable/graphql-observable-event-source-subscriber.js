import { Observable } from 'rxjs'
import { graphqlEventSourceSubscriber } from '@barejs/graphql-client'

export default function graphqlObservableEventSourceSubscriber(
  url,
  init,
  query,
  variables,
  operationName
) {
  return new Observable(subscriber => {
    return graphqlEventSourceSubscriber(
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
