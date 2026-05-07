import os
import json
from typing import Annotated, TYPE_CHECKING, Dict, Any, List

from dotenv import load_dotenv

from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError, Field

from semantic_kernel.agents import (
    ChatCompletionAgent,
    ChatHistoryAgentThread,
    SequentialOrchestration,
)
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
    OpenAIChatPromptExecutionSettings
)
from semantic_kernel.functions import (
    kernel_function,
    KernelArguments
)
from semantic_kernel.contents import (
    ChatMessageContent,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents import AuthorRole
from semantic_kernel.contents import ChatHistorySummarizationReducer
from semantic_kernel.agents.runtime import InProcessRuntime

if TYPE_CHECKING:
    from chromadb.api.models.Collection import Collection

# ---------- Utility: Load Subcommands ----------
def load_subcommands(
    info_path="../json/modkit_subcommand_info.json", 
    param_path="../json/modkit_subcommand_parameter.json"
) -> tuple[dict, dict]:
    with open(info_path, "r") as f:
        subcommand_info = json.load(f)
    with open(param_path, "r") as f:
        subcommand_parameter = json.load(f)
    return subcommand_info, subcommand_parameter



# ---------- Plugin Class: Code Generator ----------
class CodeGeneratorPlugin:
    def __init__(self, subcommand_parameter_dict: Dict[str, Any] = None):
        self.subcommand_parameter = subcommand_parameter_dict

    @kernel_function(
        description="Get the subcommand parameter",
        name="get_subcommand_parameter"
    )
    def get_subcommand_parameter(self, subcommand_name: str) -> Dict[str, Any]:
        return self.subcommand_parameter[subcommand_name]

    @kernel_function(
        description="Generate a prompt for the LLM given tool parameters JSON and the user's task request.",
        name="generate_tool_prompt"
    )
    def generate_tool_prompt(self, tool_definition: Dict[str, Any], user_task: str) -> str:
        formatted_params = json.dumps(tool_definition, indent=2, ensure_ascii=False)
        prompt = (
            "You are an expert systems engineer skilled in integrating command-line tools. "
            "You will be given a parameter definition and a user task. "
            "Your goal is to generate accurate codes that fulfills the user's request.\n\n"
            f"User Task:\n{user_task}\n\n"
            "Parameter Definition:\n"
            f"{formatted_params}\n\n"
            "Instructions:\n"
            "1. Use relevant optional parameters if they match the user's intent.\n"
            "2. Only use the parameters that are shown in the parameter definition. Never use parameters that are not in the parameter definition."
            "3. Do not use space as a parameter value. Use a name instead."
        )
        return prompt

# ---------- Pydantic Models ----------
class SubTask(BaseModel):
    assigned_subcommand: str = Field(
        description="The specific subcommand assigned to handle this subtask")
    task_details: str = Field(
        description="Detailed description of what needs to be done for this subtask")

class ModkitPlan(BaseModel):
    main_task: str = Field(
        description="The overall travel request from the user")
    subtasks: List[SubTask] = Field(
        description="List of subtasks broken down from the main task, each assigned to a specialized subcommand"
    )

# ---------- AGENTS DEFINITION ----------
def build_modkit_agent(
    chat_service,
    subcommand_info: dict
) -> ChatCompletionAgent:
    AGENT_NAME = "ModkitAgent"
    AGENT_INSTRUCTIONS = (
        "You are an planner agent.\n"
        "Your job is to decide which subcommand to run based on the user's request.\n"
        "Below are the available agents specialised in different tasks:\n"
    )
    for name, info in subcommand_info.items():
        AGENT_INSTRUCTIONS += (
            f"\n - {name}: {info.get('description')}\tInput: {info.get('input')}"
        )
    settings = OpenAIChatPromptExecutionSettings(response_format=ModkitPlan)
    agent = ChatCompletionAgent(
        service=chat_service,
        description="You are an planner agent.",
        name=AGENT_NAME,
        instructions=AGENT_INSTRUCTIONS,
        arguments=KernelArguments(settings)
    )
    return agent

def build_code_generator_agent(
    chat_service,
    subcommand_parameter_dict: dict
) -> ChatCompletionAgent:
    AGENT_NAME = "CodeGeneratorAgent"
    AGENT_INSTRUCTIONS = (
        "You are an code generator agent.\n"
        "Your job is to generate the code based on the user's request and the subcommand parameter description.\n"
        "You should follow the steps:\n"
        "- Generate the code prompt based on the user's request and the subcommand parameter description.\n"
        "- Generate the code based on the code prompt in step 1.\n"
        "- Explain the parameter in the code.\n\n"
        "Important:\n"
        "- Your code section should start with <code> and end with </code>.\n"
        "- Your code MUST start with 'modkit '\n"
    )
    code_agent = ChatCompletionAgent(
        service=chat_service,
        description="You are an code generator agent.",
        name=AGENT_NAME,
        instructions=AGENT_INSTRUCTIONS,
        plugins=[CodeGeneratorPlugin(subcommand_parameter_dict)],
    )
    return code_agent


# ---------- Orchestration & Reducer ----------
def agent_response_callback(message: ChatMessageContent) -> None:
    print(f"# {message.name}\n{message.content}")



def start_modkit_agents(
    chat_completion_service, 
    agent_response_callback=agent_response_callback
):
    """
    Initializes and starts the modkit and code generator agents alongside the orchestration runtime.
    Returns the runtime and orchestration for further use if desired.
    """
    SUBCOMMANDINFO, subcommand_parameter = load_subcommands()
    modkit_agent = build_modkit_agent(chat_completion_service, SUBCOMMANDINFO)
    code_generator_agent = build_code_generator_agent(chat_completion_service, subcommand_parameter)
    chat_orchestration = SequentialOrchestration(
        members=[modkit_agent, code_generator_agent],
        agent_response_callback=agent_response_callback,
    )
    return chat_orchestration


# ---------- Example: how to run in code ----------
# (Below block can be moved to a separate script or notebook for demo usage.)

# Example: How to import and use the modular agents/orchestration in your own Python code.

# Import the function to start modkit agents
# from llm.ONT_plus.scripts.codes.modkit_agent import start_modkit_agents

# # You may also need to import or define required variables. Example:
# # chat_completion_service = ...   # your OpenAI or compatible API/completion service
# # SUBCOMMANDINFO = ...           # your subcommand info for modkit agent
# # subcommand_parameter = ...     # parameter dict for code generator agent

# # Then you can start the agents and orchestration like this:
# runtime, chat_orchestration = start_modkit_agents(
#     chat_completion_service,
#     SUBCOMMANDINFO,
#     subcommand_parameter
# )

# Now you can use runtime and chat_orchestration for further chat or code generation tasks.



# if __name__ == "__main__":
#     import asyncio

#     async def main():
#         user_inputs = [
#             "I want to know each site modification information in the bam file.", 
#             "My bam file is mod.sorted.bam",
#             "my reference genome is /athena/chenlab/scratch/ziw4007/llm/ONT_plus/ref/ref.fa"
#         ]
#         thread = ChatHistoryAgentThread(chat_history=history_reducer)
#         for user_input in user_inputs:
#             history_reducer.add_user_message(user_input)
#             orchestration_result = await chat_orchestration.invoke(
#                 task=history_reducer.messages,
#                 runtime=runtime,
#             )
#             value = await orchestration_result.get(timeout=100)
#             print(f"***** Final Result *****\n{value}")
#             history_reducer.add_assistant_message(value.content)

#             if len(thread) > 4:
#                 await thread.reduce()
#         await runtime.stop_when_idle()

#     asyncio.run(main())

# ---------- Optional: Interactive Chat Function ----------
# The following is not required for import, but useful for notebook/testing.

# async def interactive_chat():
#     from IPython.display import display, HTML
#     thread = ChatHistoryAgentThread(chat_history=history_reducer)
#     while True:
#         user_input = input("Enter your request (or 'exit' to quit): ")
#         if user_input.strip().lower() in {"exit", "quit"}:
#             print("Exiting chat...")
#             await runtime.stop_when_idle()
#             break

#         html_output = "<div style='margin-bottom:10px'>"
#         html_output += "<div style='font-weight:bold'>User:</div>"
#         html_output += f"<div style='margin-left:20px'>{user_input}</div>"
#         html_output += "</div>"

#         orchestration_result = await chat_orchestration.invoke(
#             task=user_input,
#             runtime=runtime,
#             thread=thread
#         )
#         value = await orchestration_result.get()
#         agent_response = str(value)

#         try:
#             html_output += "<div style='margin-bottom:20px'>"
#             html_output += "<div style='font-weight:bold'>Modkit Subcommand Plan:</div>"
#             html_output += f"<pre style='margin-left:20px; padding:10px; border-radius:5px;'>{agent_response}</pre>"
#             html_output += "</div>"
#         except Exception as e:
#             html_output += "<div style='margin-bottom:20px; color:red;'>"
#             html_output += "<div style='font-weight:bold'>Validation/Error:</div>"
#             html_output += f"<pre style='margin-left:20px;'>{str(e)}</pre>"
#             html_output += "</div>"
#             html_output += "<div style='margin-bottom:20px;'>"
#             html_output += "<div style='font-weight:bold'>Raw Agent Response:</div>"
#             html_output += f"<div style='margin-left:20px; white-space:pre-wrap'>{agent_response}</div>"
#             html_output += "</div>"

#         html_output += "<hr>"
#         display(HTML(html_output))

