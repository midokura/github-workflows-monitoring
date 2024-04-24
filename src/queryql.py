import os

from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

from flask import current_app as app

# Select your transport with a defined url endpoint
headers = {
    "Authorization": f"bearer {os.getenv('GH_PAT')}"
}
transport = AIOHTTPTransport(url="https://api.github.com/graphql", headers=headers)

# Create a GraphQL client using the defined transport
client = Client(transport=transport, fetch_schema_from_transport=True)


# Provide a GraphQL query
def query_node(node_id):
    query = gql(
      """
      query getCheckRun($node_id: ID!) {
        node(id: $node_id) {
        ... on CheckRun {
                id
                name
                status
                startedAt
                completedAt
                }
            }
      }
      """
    )
    params = {"node_id": node_id}

    result = client.execute(query, variable_values=params)
    app.logger.info(f"Node type {result}")
