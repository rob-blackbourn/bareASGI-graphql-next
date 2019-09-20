"""
The ASGI Application
"""

import string
HTML = string.Template("""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>GraphQL Request</title>
  </head>
  <body>
    <h1>GraphQL Request</h1>

    <form id="message-form" action="#" method="post">
      <textarea id="message" placeholder="Write your query here..." required></textarea>
      <button type="submit">Send Query</button>
    </form>
    
    <div id="response">Response goes here...</div>
    
    <h4>Example Query</h4>

    <p>query { latest { timestamp cpu { percent } } }</p>
    <pre>
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
    </pre>
    
    <h4>Example Subscription</h4>
    
    <p>subscription { system { timestamp cpu { percent } } }</p>
    
    <pre>
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
}    
    </pre>

  <script language="javascript" type="text/javascript">

    window.onload = function() {

      var form = document.getElementById('message-form')
      var messageField = document.getElementById('message')
      var responseField = document.getElementById("response")
      var eventSource = null

      // Send a message when the form is submitted.
      form.onsubmit = function(e) {
        e.preventDefault()
        
        if (eventSource !== null && eventSource.readyState != 2) {
          eventSource.close()
        }

        // Retrieve the message from the textarea.
        var query = messageField.value

        // Send the message
        fetch('${sse_url}', {
          method: 'POST',
          mode: 'same-origin',
          body: JSON.stringify({
            query
          })
        })
          .then(response => {
            console.log(response)
            if (response.status == 200) {
              // This is a query result, so just show the data.
              response.text()
                .then(text => {
                  responseField.innerHTML = text
                })
                .catch(error => {
                  console.log(error)
                })
            } else if (response.status == 201) {
              // This is a subscription response. An endpoint is
              // returned in the "Location" header which we can
              // consume with an EventSource.
              var location = response.headers.get('location')
              eventSource = new EventSource(location)
              eventSource.onmessage = function(event) {
                responseField.innerHTML = event.data
              }
            } else {
              throw new Error("Unhandled response")
            }
          })
          .catch(error => {
            console.error(error)
          })
        
        return false
      }
    }  
  
  </script>     
  </body>
</html>
    """)
    
def make_html(sse_url: str) -> str:
    return HTML.substitute(sse_url=sse_url)