/**
 * An error which encapsulates an event.
 */
export default class EventError extends Error {
  /**
   * Create an event error.
   * @param {Event} event - The event that caused the error.
   * @param  {...any} params - Any other error params.
   */
  constructor (event, ...params) {
    super(...params)

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, EventError)
    }

    this.event = event
  }
}
