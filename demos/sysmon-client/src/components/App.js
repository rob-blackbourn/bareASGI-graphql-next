import { Component } from 'react'
import { BrowserRouter as Router, Switch, Route, Link } from 'react-router-dom'
import Home from './Home'
import DiagnoseObservableClient from './DiagnoseObservableClient'
import SysMonObservableClient from './SysMonObservableClient'

class App extends Component {
  render() {
    return (
      <Router>
        <div>
          <nav>
            <ul>
              <li>
                <Link to="/diagnose-observable-client">
                  Diagnose observable client
                </Link>
              </li>
              <li>
                <Link to="/sysmon-observable-client">
                  Monitor observable client
                </Link>
              </li>
            </ul>
          </nav>

          <Switch>
            <Route path="/diagnose-observable-client">
              <DiagnoseObservableClient />
            </Route>
            <Route path="/sysmon-observable-client">
              <SysMonObservableClient />
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
