import {
  graphqlObservableFetchClient,
  graphqlObservableEventSourceClient,
  graphqlObservableStreamClient,
  graphqlObservableWsClient
} from '@barejs/graphql-observable'

const CLIENTS = {
  fetch: graphqlObservableFetchClient,
  stream: graphqlObservableStreamClient,
  eventSource: graphqlObservableEventSourceClient,
  webSocket: graphqlObservableWsClient
}

export default CLIENTS
