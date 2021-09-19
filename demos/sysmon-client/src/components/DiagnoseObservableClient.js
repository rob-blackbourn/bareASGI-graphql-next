import { Component } from 'react'
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormControl from '@mui/material/FormControl';
import FormLabel from '@mui/material/FormLabel';
import {
  graphqlObservableFetchClient,
  graphqlObservableEventSourceClient,
  graphqlObservableStreamClient,
  graphqlObservableWsClient
} from '../graphql-observable'
import QUERIES from '../queries'
import CONFIG from '../config'

const CLIENTS = {
  fetch: graphqlObservableFetchClient,
  stream: graphqlObservableStreamClient,
  eventSource: graphqlObservableEventSourceClient,
  webSocket: graphqlObservableWsClient
}

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

  renderRequestTypeSelector = (requestType, clientType) => (
    <FormControl component="fieldset">
      <FormLabel component="legend">Request Type</FormLabel>
      <RadioGroup
        aria-label="requestType"
        name="request-radio-buttons-group"
        value={requestType}
        onChange={this.handleRequestTypeChange}
      >
        <FormControlLabel value="query" control={<Radio />} label="Query" />
        <FormControlLabel
          value="subscription"
          control={<Radio disabled={clientType==='fetch'}/>}
          label="Subscription"
        />
      </RadioGroup>
    </FormControl>
  )

  renderRequestComplexitySelector = requestComplexity => (
    <FormControl component="fieldset">
      <FormLabel component="legend">Request Complexity</FormLabel>
      <RadioGroup
        aria-label="requestComplexity"
        name="request-complexity-radio-buttons-group"
        value={requestComplexity}
        onChange={this.handleRequestComplexityChange}
      >
        <FormControlLabel value="simple" control={<Radio />} label="Simple" />
        <FormControlLabel value="complex" control={<Radio />} label="Complex" />
      </RadioGroup>
    </FormControl>
  )

  renderClientTypeSelector = clientType => (
    <FormControl component="fieldset">
      <FormLabel component="legend">Client</FormLabel>
      <RadioGroup
        aria-label="clientType"
        name="client-radio-buttons-group"
        value={clientType}
        onChange={this.handleClientTypeChange}
      >
        <FormControlLabel value="fetch" control={<Radio />} label="Fetch" />
        <FormControlLabel value="stream" control={<Radio />} label="Stream" />
        <FormControlLabel value="eventSource" control={<Radio />} label="Event Source" />
        <FormControlLabel value="webSocket" control={<Radio />} label="WebSocket" />
      </RadioGroup>
    </FormControl>
  )

  renderSelectors = (requestType, requestComplexity, clientType) => (
    <div>
    {this.renderRequestTypeSelector(requestType, clientType)}
    {this.renderRequestComplexitySelector(requestComplexity)}
    {this.renderClientTypeSelector(clientType)}
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
