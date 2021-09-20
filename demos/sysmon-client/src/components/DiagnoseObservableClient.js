import { Component } from 'react'
import QUERIES from '../queries'
import CONFIG from '../config'
import RequestTypeSelector from './RequestTypeSelector'
import RequestComplexitySelector from './RequestComplexitySelector'
import ClientTypeSelector from './ClientTypeSelector'
import DiagnosticView from './DiagnosticView'
import CLIENTS from './clients'

class Home extends Component {
  constructor(props) {
    super(props)

    this.state = {
      requestType: 'query',
      requestComplexity: 'simple',
      clientType: 'fetch',
      response: {},
      complete: false,
      error: ''
    }

    this.subscription = null
  }

  handleRequestTypeChange = event => {
    this.setState(
      {
        requestType: event.target.value
      },
      this.startSubscription
    )
  }

  handleRequestComplexityChange = event => {
    const requestComplexity = event.target.value
    this.setState({ requestComplexity }, this.startSubscription)
  }

  handleClientTypeChange = event => {
    const clientType = event.target.value
    const requestType =
      clientType === 'fetch' ? 'query' : this.state.requestType
    this.setState({ clientType, requestType }, this.startSubscription)
  }

  startSubscription = () => {
    const { requestType, requestComplexity, clientType } = this.state

    const query = QUERIES[requestType][requestComplexity]
    const graphqlObserve = CLIENTS[clientType]

    console.log(query)
    this.stopSubscription()

    const url = CONFIG.graphqlQueryPath
    const init = {
      mode: 'cors'
    }
    const variables = {}
    const operation = null

    this.subscription = graphqlObserve(
      url,
      init,
      query,
      variables,
      operation
    ).subscribe({
      next: response => {
        this.setState({ response, completed: false, error: '' })
      },
      complete: () => {
        this.setState({ complete: true, error: '' })
      },
      error: error => {
        this.setState({
          response: {},
          completed: false,
          error: error ? error.message : 'Unknown error'
        })
      }
    })
  }

  stopSubscription = () => {
    if (this.subscription) {
      this.subscription.unsubscribe()
      this.subscription = null
    }
  }

  componentDidMount() {
    this.startSubscription()
  }

  componentWillUnmount() {
    this.stopSubscription()
  }

  render() {
    const {
      requestType,
      requestComplexity,
      clientType,
      response,
      complete,
      error
    } = this.state

    return (
      <div>
        <div>
          <RequestTypeSelector
            requestType={requestType}
            clientType={clientType}
            handler={this.handleRequestTypeChange}
          />
          <RequestComplexitySelector
            requestComplexity={requestComplexity}
            handler={this.handleRequestComplexityChange}
          />
          <ClientTypeSelector
            clientType={clientType}
            handler={this.handleClientTypeChange}
          />
        </div>
        <DiagnosticView response={response} complete={complete} error={error} />
      </div>
    )
  }
}

export default Home
