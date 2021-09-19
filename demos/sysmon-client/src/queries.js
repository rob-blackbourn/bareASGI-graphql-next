const simpleQuery = `
query {
  latest {
    timestamp
    cpu {
      percent
    }
  }
}
`

const complexQuery = `
query {
  latest {
    timestamp
    cpu {
      count
      percent
      cores {
        percent
        times {
          user
          nice
          system
          idle
          iowait
          irq
          softirq
          steal
          guest
          guestNice
        }
      }
      stats {
        ctxSwitches
        interrupts
        softInterrupts
        syscalls
      }
    }
  }
}
`

const simpleSubscription = `
subscription {
  system {
    timestamp
    cpu {
      percent
    }
  }
}
`

const complexSubscription = `
subscription {
  system {
    timestamp
    cpu {
      count
      percent
      cores {
        percent
        times {
          user
          nice
          system
          idle
          iowait
          irq
          softirq
          steal
          guest
          guestNice
        }
      }
      stats {
        ctxSwitches
        interrupts
        softInterrupts
        syscalls
      }
    }
  }
`

const QUERIES = {
  query: {
    simple: simpleQuery,
    complex: complexQuery
  },
  subscription: {
    simple: simpleSubscription,
    complex: complexSubscription
  }
}

export default QUERIES
