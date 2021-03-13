"""
Graphiql template
"""

import json
import string
from typing import Any, Mapping, Optional

GRAPHIQL_VERSION = '1.0.3'
SUBSCRIPTIONS_TRANSPORT_VERSION = '0.7.3'

GRAPHIQL_TEMPLATE = string.Template(
    """
<!DOCTYPE html>
<html>
  <head>
    <title>${graphiql_html_title}</title>
    <meta name="robots" content="noindex" />
    <meta name="referrer" content="origin" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      body {
        margin: 0;
        overflow: hidden;
      }
      #graphiql {
        height: 100vh;
      }
    </style>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/graphiql@${graphiql_version}/graphiql.css" />
    <script src="//cdn.jsdelivr.net/npm/promise-polyfill@8.1.3/dist/polyfill.min.js"></script>
    <script src="//cdn.jsdelivr.net/npm/unfetch@4.1.0/dist/unfetch.umd.js"></script>
    <script src="//cdn.jsdelivr.net/npm/react@16.13.1/umd/react.production.min.js"></script>
    <script src="//cdn.jsdelivr.net/npm/react-dom@16.13.1/umd/react-dom.production.min.js"></script>
    <script src="//cdn.jsdelivr.net/npm/graphiql@${graphiql_version}/graphiql.min.js"></script>
    <script src="//cdn.jsdelivr.net/npm/subscriptions-transport-ws@${subscriptions_transport_version}/browser/client.js"></script>
    <script src="//cdn.jsdelivr.net/npm/graphiql-subscriptions-fetcher@0.0.2/browser/client.js"></script>
  </head>
  <body>
    <div id="graphiql">Loading...</div>
    <script>
      // Collect the URL parameters
      var parameters = {};
      window.location.search.substr(1).split('&').forEach(function (entry) {
        var eq = entry.indexOf('=');
        if (eq >= 0) {
          parameters[decodeURIComponent(entry.slice(0, eq))] =
            decodeURIComponent(entry.slice(eq + 1));
        }
      });
      var headers = JSON.stringify(JSON.parse('${headers}'), null, 2)

      // if variables was provided, try to format it.
      if (parameters.variables) {
        try {
          parameters.variables =
            JSON.stringify(JSON.parse(parameters.variables), null, 2);
        } catch (e) {
          // Do nothing, we want to display the invalid JSON as a string, rather
          // than present an error.
        }
      }

      // Produce a Location query string from a parameter object.
      function locationQuery(params) {
        return '?' + Object.keys(params).filter(function (key) {
          return Boolean(params[key]);
        }).map(function (key) {
          return encodeURIComponent(key) + '=' +
            encodeURIComponent(params[key]);
        }).join('&');
      }

      function graphQLFetcher(graphQLParams, opts) {
        return fetch(`${query_url}`, {
          method: 'post',
          headers: Object.assign(
            {
              'Accept': 'application/json',
              'Content-Type': 'application/json'
            },
            opts && opts.headers,
          ),
          body: JSON.stringify(graphQLParams),
          credentials: 'include',
        }).then(function (response) {
          return response.text();
        }).then(function (responseBody) {
          try {
            return JSON.parse(responseBody);
          } catch (error) {
            return responseBody;
          }
        });
      }

      let subscriptionsClient = new SubscriptionsTransportWs.SubscriptionClient(
        '${subscription_url}',
        { reconnect: true }
      );
      let subscriptionsFetcher = GraphiQLSubscriptionsFetcher.graphQLFetcher(
        subscriptionsClient,
        graphQLFetcher
      );

      function onEditQuery(newQuery) {
        parameters.query = newQuery;
        updateURL();
      }
      function onEditVariables(newVariables) {
        parameters.variables = newVariables;
        updateURL();
      }
      function onEditOperationName(newOperationName) {
        parameters.operationName = newOperationName;
        updateURL();
      }
      function onEditHeaders(newHeaders) {
        parameters.headers = newHeaders;
        updateURL();
      }
      function updateURL() {
        history.replaceState(null, null, locationQuery(parameters));
      }

      ReactDOM.render(
        React.createElement(GraphiQL, {
          fetcher: subscriptionsFetcher,
          onEditQuery: onEditQuery,
          onEditVariables: onEditVariables,
          onEditOperationName: onEditOperationName,
          onEditHeaders: onEditHeaders,
          query: parameters.query,
          variables: parameters.variables,
          operationName: parameters.operationName,
          headers: headers,
          headerEditorEnabled: true,
          shouldPersistHeaders: true
        }),
        document.getElementById('graphiql')
      );
    </script>
  </body>
</html>
"""
)


def make_template(
        host: str,
        query_url: str,
        subscription_url: str,
        *,
        graphiql_version: str = GRAPHIQL_VERSION,
        subscriptions_transport_version: str = SUBSCRIPTIONS_TRANSPORT_VERSION,
        title: str = 'GraphiQL',
        headers: Optional[Mapping[str, Any]] = None
) -> str:
    return GRAPHIQL_TEMPLATE.substitute(
        host=host,
        query_url=query_url,
        subscription_url=subscription_url,
        graphiql_version=graphiql_version,
        subscriptions_transport_version=subscriptions_transport_version,
        graphiql_html_title=title,
        headers=json.dumps(headers or {})
    )
