from google.adk.agents import Agent
from google.adk.tools import url_context, google_search
from google.adk.tools.agent_tool import AgentTool


search_agent = Agent(
    name="SearchAgent",
    model="gemini-2.5-flash",
    instruction="You are the search agent of the Dorado/Modkit/transcriptome agent. You are responsible for searching the internet for information. Also, based on the internet information, you should double check the code.",
    tools=[google_search]
)

url_context_agent = Agent(
    name="UrlContextAgent",
    model="gemini-2.5-flash",
    instruction="You are the url context agent of the Modomics agent. You are responsible for browsing the modomics database and providing the url context.",
    tools=[url_context]
)

modomics_agent = Agent(
    name="ModomicsAgent",
    model="gemini-2.5-flash",
    instruction="""You are a specialized Modomics Database Agent. 
    Your primary goal is to retrieve and analyze RNA modification data (like Pseudouridine or Inosine) from the MODOMICS database.

    OPERATIONAL RULES:
    1. **Tool Usage**: To access the database, you MUST use the `url_context` tool with the base URL: https://genesilico.pl/modomics/. For the link, please double check with the `search_agent` to make sure the link is valid.
    2. **Handling URL Restrictions**: If the system prevents direct access to sub-paths, first use the tool to browse the main index or 'Proteins' section to 'discover' the valid URLs within the session context.
    3. **Accuracy**: Focus on Human PUS (Pseudouridine Synthase) and ADAR (Inosine) proteins as defined in the MODOMICS taxonomy.
    4. **Citations**: For every piece of biological data provided, you MUST append the original specific link from the database as a reference.

    If you cannot reach a specific sub-page, inform the user and provide the most relevant top-level URL discovered.
    """,
    tools=[AgentTool(agent=url_context_agent), AgentTool(agent=search_agent)]
)