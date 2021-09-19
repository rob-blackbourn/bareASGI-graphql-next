import { Component } from 'react'
import { graphqlObservableWsClient as graphqlObserve } from '../graphql-observable'
import CONFIG from '../config'

class ObservableWsSubscription extends Component {
  constructor(props) {
    super()
    this.subscription = null
    this.state = {
      response: '',
      complete: false,
      error: ''
    }
  }

  invokeQuery = () => {
    const url = CONFIG.graphqlQueryPath
    const query = `
subscription {
  system {
    timestamp
    cpu {
      percent
    }
  }
}`
    const variables = {}
    const operation = null
    const init = {
      mode: 'cors'
    }

    return graphqlObserve(
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

  componentDidMount() {
    console.log('componentDidMount')
    this.subscription = this.invokeQuery()
  }

  componentWillUnmount() {
    console.log('componentWillUnmount')
    if (this.subscription) {
      this.subscription.unsubscribe()
      this.subscription = null
    }
  }

  render() {
    const { response, complete, error } = this.state

    return (
      <div>
        <div>Response: {JSON.stringify(response)}</div>
        <div>Complete: {complete ? 'true' : 'false'}</div>
        <div>Error: {error.message}</div>
      </div>
    )
  }
}

export default ObservableWsSubscription
