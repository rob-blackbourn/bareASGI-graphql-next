import { Component } from 'react'
import { BrowserRouter as Router, Switch, Route, Link } from 'react-router-dom'
import Example1 from './Example1'
import ObservableFetchQuery from './ObservableFetchQuery'
import ObservableStreamQuery from './ObservableStreamQuery'
import ObservableStreamSubscription from './ObservableStreamSubscription'

class App extends Component {
  render() {
    return (
      <Router>
        <div>
          <nav>
            <ul>
              <li>
                <Link to="/">Example1</Link>
              </li>
              <li>
                <Link to="/observable-stream-subscription">ObservableStreamSubscription</Link>
              </li>
              <li>
                <Link to="/observable-stream-query">ObservableStreamQuery</Link>
              </li>
              <li>
                <Link to="/observable-fetch-query">ObservableFetchQuery</Link>
              </li>
            </ul>
          </nav>

          <Switch>
            <Route path="/observable-stream-query">
              <ObservableStreamQuery />
            </Route>
            <Route path="/observable-fetch-query">
              <ObservableFetchQuery />
            </Route>
            <Route path="/observable-stream-subscription">
              <ObservableStreamSubscription />
            </Route>
            <Route path="/">
              <Example1 />
            </Route>
          </Switch>
        </div>
      </Router>
    )
  }
}

export default App
