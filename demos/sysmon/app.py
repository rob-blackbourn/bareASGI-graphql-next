import asyncio
from functools import partial
import logging
from bareasgi import Application
from bareasgi_cors import CORSMiddleware
from bareasgi_graphql_next import add_graphql_next, GraphQLController
from baretypes import Scope, Info, RouteMatches, Content, HttpResponse
from bareutils import text_writer
from .system_monitor import SystemMonitor
from .schema import schema

logger = logging.getLogger(__name__)


async def start_service(scope: Scope, info: Info, request) -> None:
    system_monitor = SystemMonitor(1)

    info['system_monitor'] = system_monitor
    info['system_monitor_task'] = asyncio.create_task(system_monitor.startup())


async def stop_service(scope: Scope, info: Info, request) -> None:
    system_monitor: SystemMonitor = info['system_monitor']
    system_monitor_task: asyncio.Task = info['system_monitor_task']
    system_monitor.shutdown()
    await system_monitor_task


async def start_graphql(scope: Scope, info: Info, request, *, app: Application) -> None:
    info['graphql_controller'] = add_graphql_next(app, schema, path_prefix='/test')


async def stop_graphql(scope: Scope, info: Info, request) -> None:
    graphql_controller: GraphQLController = info['graphql_controller']
    graphql_controller.shutdown()


async def graphql_handler(
        scope: Scope,
        info: Info,
        matches: RouteMatches,
        content: Content
) -> HttpResponse:
    html = """
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
        fetch('http://127.0.0.1:9009/test/graphql', {
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
    """
    return 200, [(b'content-type', b'text/html')], text_writer(html)


def make_application() -> Application:
    cors_middleware = CORSMiddleware()
    info = {}
    app = Application(
        info=info,
        startup_handlers=[start_service],
        shutdown_handlers=[stop_service],
        middlewares=[cors_middleware]
    )

    app.startup_handlers.append(partial(start_graphql, app=app))
    app.shutdown_handlers.append(stop_graphql)

    app.http_router.add({'GET'}, '/test/graphql2', graphql_handler)

    return app
