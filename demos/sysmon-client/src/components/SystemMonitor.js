import { Component } from 'react'
import PropTypes from 'prop-types'
import CONFIG from '../config'

class GraphQLObservableClient extends Component {
  constructor(props) {
    super(props)
    this.subscription = null
    this.state = {
      response: '',
      complete: false,
      error: ''
    }
  }

  invokeQuery = () => {
    const url = CONFIG.graphqlQueryPath
    const {graphqlObserve, query, variables, init, operation} = this.props

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

GraphQLObservableClient.propTypes = {
  graphqlObserve: PropTypes.func.isRequired,
  query: PropTypes.string.isRequired,
  variables: PropTypes.object.isRequired,
  init: PropTypes.object.isRequired,
  operation: PropTypes.string
}

export default GraphQLObservableClient
