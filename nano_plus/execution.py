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

import subprocess
from typing import List
AGENT_NAME = "calculator_agent"
APP_NAME = "calculator"
USER_ID = "user1234"
SESSION_ID = "session_code_exec_async"
GEMINI_MODEL = "gemini-2.0-flash"

# Agent Definition

def code_execute(command: List[str]):
    """
    Execute a list of bash commands sequentially.
    Args:
        command (List[str]): A list where EACH element is a COMPLETE, standalone bash command string.
                             Example: ["ls -l", "rm *.ipynb", "mkdir results"]
                             DO NOT split a single command into multiple items (e.g., ["rm", "*.ipynb"] is INVALID).
    Returns:
        Tuple[int, str]: Return code and output of the LAST executed command.
    """
    last_output = (0, "No commands executed")
    for cmd in command:
        try:
            # Ensure shell=True is used to handle wildcards like '*'
            process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            print(f"Command '{cmd}' output: {process.stdout or process.stderr}")
            last_output = (process.returncode, f"Command '{cmd}' output: {process.stdout or process.stderr}")
            if process.returncode != 0:
                return last_output # Break early on error
        except Exception as e:
            return 1, f"Execution failed for '{cmd}': {str(e)}"
    return last_output

# bash_agent = LlmAgent(
#     name="BashAgent",
#     model=GEMINI_MODEL,
#     instruction="""You are a precise Bash execution agent.
    
#     CRITICAL RULES FOR TOOL CALLING:
#     1. You must provide a List[str] to code_execute.
#     2. EACH string in the list must be a TOTAL, COMPLETE command.
#     3. NEVER split a command and its arguments. 
#        - WRONG: ["rm", "*.ipynb"]
#        - RIGHT: ["rm *.ipynb"]
#     4. If you need to run multiple steps, put each full step as a separate string in the list.
#     5. Use 'shell=True' logic (provided by the tool) to handle wildcards and piping.

#     Output Requirements:
#     - Return ONLY the final result as plain text.
#     - No markdown, no code blocks, no conversational filler.
#     - If a command fails, analyze the error, fix the syntax, and retry once.
#     """,
#     description="Executes full bash command strings via a sequential list.",
#     tools=[code_execute]
# )

# # Session and Runner
# session_service = InMemorySessionService()
# session = asyncio.run(session_service.create_session(
#     app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
# ))
# runner = Runner(agent=bash_agent, app_name=APP_NAME,
#                 session_service=session_service)

# # Agent Interaction (Async)
# async def call_agent_async(query):
#     content = types.Content(role="user", parts=[types.Part(text=query)])
#     print(f"\n--- Running Query: {query} ---")
#     final_response_text = "No final text response captured."
#     try:
#         # Use run_async
#         async for event in runner.run_async(
#             user_id=USER_ID, session_id=SESSION_ID, new_message=content
#         ):
#             print(f"Event ID: {event.id}, Author: {event.author}")
#             if event.is_final_response():
#                 if (
#                     event.content
#                     and event.content.parts
#                     and event.content.parts[0].text
#                 ):
#                     final_response_text = event.content.parts[0].text.strip()
#                     print(f"==> Final Agent Response: {final_response_text}")
#                 else:
#                     print(
#                         "==> Final Agent Response: [No text content in final event]")

#     except Exception as e:
#         print(f"ERROR during agent run: {e}")
#     print("-" * 30)


# # Main async function to run the examples
# async def main():
#     await call_agent_async("I want to know how many GPUs I have access to.")


# # Execute the main async function
# try:
#     asyncio.run(main())
# except RuntimeError as e:
#     # Handle specific error when running asyncio.run in an already running loop (like Jupyter/Colab)
#     if "cannot be called from a running event loop" in str(e):
#         print("\nRunning in an existing event loop (like Colab/Jupyter).")
#         print("Please run `await main()` in a notebook cell instead.")
#         # If in an interactive environment like a notebook, you might need to run:
#         # await main()
#     else:
#         raise e  # Re-raise other runtime errors

