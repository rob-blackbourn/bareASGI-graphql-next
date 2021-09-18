/**
 * A GraphQL error.
 */
export default class GraphQLError extends Error {
  /**
   * Create a GraphQL error.
   * @param {any} details - The error details.
   * @param  {...any} params - Any other Error params.
   */
  constructor (details, ...params) {
    super(...params)

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, GraphQLError)
    }

    this.details = details
  }
}
