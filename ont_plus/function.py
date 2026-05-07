# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.tools import google_search
# import yfinance as yf
import asyncio

from google.adk.tools.agent_tool import AgentTool


APP_NAME = "stock_app"
USER_ID = "1234"
SESSION_ID = "session1234"

# def get_stock_price(symbol: str):
#     """
#     Retrieves the current stock price for a given symbol.

#     Args:
#         symbol (str): The stock symbol (e.g., "AAPL", "GOOG").

#     Returns:
#         float: The current stock price, or None if an error occurs.
#     """
#     try:
#         stock = yf.Ticker(symbol)
#         historical_data = stock.history(period="1d")
#         if not historical_data.empty:
#             current_price = historical_data['Close'].iloc[-1]
#             return current_price
#         else:
#             return None
#     except Exception as e:
#         print(f"Error retrieving stock price for {symbol}: {e}")
#         return None

def get_university_tuition(university: str):
    """
    Retrieves the current tuition for a given university.
    Args:
        university (str): The university name (e.g., "MIT", "Harvard").

    Returns:
        float: The current tuition, or None if an error occurs.
    """

    university_tuition = {
        "MIT": 100000,
        "Harvard": 150000,
        "Stanford": 120000,
        "Cambridge": 130000,
        "Oxford": 140000,
        "University of Arizona": 130000,
    }

    if university not in university_tuition.keys():
        return "University not found in get_university_tuition tool."
    else:
        fee = university_tuition[university]
        return f"The tuition for {university} is {fee}."

search_agent = Agent(
    model='gemini-2.0-flash',
    name='SearchAgent',
    instruction="""
    You're a specialist in Google Search
    """,
    tools=[google_search],
)

university_tuition_agent = Agent(
    model="gemini-2.5-flash",
    name="UniversityTuitionAgent",
    instruction=(
        "You are an expert who helps users calculate and report the tuition fees for various universities. "
        "Use get_university_tuition as your primary tool. If the university is not found, search for the tuition with the google_search tool."
    ),
    description=(
        "This agent assists users by calculating total tuition fees for recognized universities. "
        "If tuition data is unavailable from get_university_tuition, the agent will use google_search to help find it."
    ),
    tools=[get_university_tuition, AgentTool(agent = search_agent)],  # List Python functions here; the ADK will wrap them as FunctionTools.
)

# Session and Runner
async def setup_session_and_runner():
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=university_tuition_agent, app_name=APP_NAME, session_service=session_service)
    return session, runner

# Agent Interaction
async def call_agent_async(query):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    _, runner = await setup_session_and_runner()
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    async for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent Response: ", final_response)


# Note: In Colab, you can directly use 'await' at the top level.
# If running this code as a standalone Python script, you'll need to use asyncio.run() or manage the event loop.
# await call_agent_async("stock price of GOOG")
asyncio.run(call_agent_async("tuition of Arizona State University"))