import { Component } from 'react'
import QUERIES from '../queries'
import CONFIG from '../config'
import {
  renderRequestTypeSelector,
  renderRequestComplexitySelector,
  renderClientTypeSelector
} from './Selectables'
import CLIENTS from './clients'

class Home extends Component {
  constructor(props) {
    super(props)

    this.state = {
      requestType: 'query',
      requestComplexity: 'simple',
      clientType: 'fetch',
      response: '',
      complete: false,
      error: ''
    }

    this.subscription = null
  }

  handleRequestTypeChange = event => {
    this.setState(
      { 
        requestType: event.target.value,
        response: '',
        complete: false,
        error: ''
      },
      this.startSubscription)
  }

  handleRequestComplexityChange = event => {
    this.setState(
      { 
        requestComplexity: event.target.value,
        response: '',
        complete: false,
        error: ''
      },
      this.startSubscription)
  }

  handleClientTypeChange = event => {
    const requestType = event.target.value === 'fetch' ? 'query' : this.state.requestType
    this.setState(
      {
        clientType: event.target.value,
        requestType,
        response: '',
        complete: false,
        error: ''
      },
      this.startSubscription)
  }

  startSubscription = () => {
    const {requestType, requestComplexity, clientType} = this.state

    const query = QUERIES[requestType][requestComplexity]
    const graphqlObserve = CLIENTS[clientType]

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
        console.log(response)
        this.setState({ response })
      },
      complete: () => {
        console.log('complete')
        this.setState({ complete: true })
      },
      error: error => {
        console.error(error)
        this.setState({ error })
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

  renderSelectors = (requestType, requestComplexity, clientType) => (
    <div>
    {renderRequestTypeSelector(requestType, clientType, this.handleRequestTypeChange)}
    {renderRequestComplexitySelector(requestComplexity, this.handleRequestComplexityChange)}
    {renderClientTypeSelector(clientType, this.handleClientTypeChange)}
    </div>
  )
  
  render() {
    const { requestType, requestComplexity, clientType, response, complete, error } = this.state

    return (
      <div>
        {this.renderSelectors(requestType, requestComplexity, clientType)}
        <div>
          <div>Response: {JSON.stringify(response)}</div>
          <div>Complete: {complete ? 'true' : 'false'}</div>
          <div>Error: {error.message}</div>
        </div>
      </div>
    )
  }
}

export default Home
