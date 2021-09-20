import { Observable } from 'rxjs'
import { graphqlWsSubscriber } from '@barejs/graphql-client'

export default function graphqlObservableWsSubscriber(
  url,
  init,
  query,
  variables,
  operation
) {
  return new Observable(subscriber => {
    return graphqlWsSubscriber(
      url,
      init,
      query,
      variables,
      operation,
      subscriber.next,
      subscriber.error,
      subscriber.complete
    )
  })
}
