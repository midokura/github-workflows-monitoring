import os

from typing import List

from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

# Select your transport with a defined url endpoint
headers = {"Authorization": f"bearer {os.getenv('GH_PAT')}"}
transport = AIOHTTPTransport(url="https://api.github.com/graphql", headers=headers)

# Create a GraphQL client using the defined transport
client = Client(transport=transport, fetch_schema_from_transport=True)


# Provide a GraphQL query
def query_jobs(node_id_list: List[str]):
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
                repository {
                  owner {
                    login
                  }
                  name
                }
                checkSuite {
                  status
                  workflowRun {
                    event
                    runNumber
                  }
                }
              }
            }
       }
      """
    )
    params = {
        "node_id_list": node_id_list[:100]
    }  # Get only the 100 first, the others will be processed on next iterations

    return client.execute(query, variable_values=params)
