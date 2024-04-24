import os

from typing import List

from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

# Select your transport with a defined url endpoint
headers = {
    "Authorization": f"bearer {os.getenv('GH_PAT')}"
}
transport = AIOHTTPTransport(url="https://api.github.com/graphql", headers=headers)

# Create a GraphQL client using the defined transport
client = Client(transport=transport, fetch_schema_from_transport=True)


# Provide a GraphQL query
def query_nodes(node_id_list: List[str]):
    query = gql(
      """
        query getCheckRuns($node_id_list: [ID!]!) {
        nodes(ids: $node_id_list) {
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
    params = {"node_id_list": node_id_list}

    return client.execute(query, variable_values=params)
