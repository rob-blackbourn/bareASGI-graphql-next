import { Component } from 'react'
import { BrowserRouter as Router, Switch, Route, Link } from 'react-router-dom'
import Home from './Home'
import GraphQLObservableClient from './GraphQLObservableClient'
import DiagnoseObservableClient from './DiagnoseObservableClient'
import {
  graphqlObservableFetchClient,
  graphqlObservableEventSourceClient,
  graphqlObservableStreamClient,
  graphqlObservableWsClient
} from '../graphql-observable'
import QUERIES from '../queries'

class App extends Component {
  render() {
    return (
      <Router>
        <div>
          <nav>
            <ul>
              <li>
                <Link to="/diagnose-observable-client">Diagnose observable client</Link>
              </li>
              <li>
                <Link to="/observable-fetch-query">ObservableFetchQuery</Link>
              </li>
              <li>
                <Link to="/observable-stream-query">ObservableStreamQuery</Link>
              </li>
              <li>
                <Link to="/observable-stream-subscription">ObservableStreamSubscription</Link>
              </li>
              <li>
                <Link to="/observable-ws-query">ObservableWsQuery</Link>
              </li>
              <li>
                <Link to="/observable-ws-subscription">ObservableWsSubscription</Link>
              </li>
              <li>
                <Link to="/observable-sse-query">ObservableSseQuery</Link>
              </li>
              <li>
                <Link to="/observable-sse-subscription">ObservableSseSubscription</Link>
              </li>
            </ul>
          </nav>

          <Switch>
            <Route path="/diagnose-observable-client">
              <DiagnoseObservableClient />
            </Route>
            <Route path="/observable-fetch-query">
              <GraphQLObservableClient
                graphqlObserve={graphqlObservableFetchClient}
                query={QUERIES.query.simple}
                variables={{}}
                init={{ mode: 'cores'}}
                operation={null}
                />
            </Route>
            <Route path="/observable-stream-query">
              <GraphQLObservableClient
                graphqlObserve={graphqlObservableStreamClient}
                query={QUERIES.query.simple}
                variables={{}}
                init={{ mode: 'cores'}}
                operation={null}
                />
            </Route>
            <Route path="/observable-stream-subscription">
              <GraphQLObservableClient
                graphqlObserve={graphqlObservableStreamClient}
                query={QUERIES.subscription.simple}
                variables={{}}
                init={{ mode: 'cores'}}
                operation={null}
                />
            </Route>
            <Route path="/observable-ws-query">
              <GraphQLObservableClient
                graphqlObserve={graphqlObservableWsClient}
                query={QUERIES.query.simple}
                variables={{}}
                init={{ mode: 'cores'}}
                operation={null}
                />
            </Route>
            <Route path="/observable-ws-subscription">
              <GraphQLObservableClient
                graphqlObserve={graphqlObservableWsClient}
                query={QUERIES.subscription.simple}
                variables={{}}
                init={{ mode: 'cores'}}
                operation={null}
                />
            </Route>
            <Route path="/observable-sse-query">
              <GraphQLObservableClient
                graphqlObserve={graphqlObservableEventSourceClient}
                query={QUERIES.query.simple}
                variables={{}}
                init={{ mode: 'cores'}}
                operation={null}
                />
            </Route>
            <Route path="/observable-sse-subscription">
              <GraphQLObservableClient
                graphqlObserve={graphqlObservableEventSourceClient}
                query={QUERIES.subscription.simple}
                variables={{}}
                init={{ mode: 'cores'}}
                operation={null}
                />
            </Route>
            <Route path="/">
              <Home />
            </Route>
          </Switch>
        </div>
      </Router>
    )
  }
}

export default App
