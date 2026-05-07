import os
import json
from typing import TYPE_CHECKING, Dict, Any, List

import chromadb
from dotenv import load_dotenv
from openai import AsyncOpenAI

from pydantic import BaseModel, Field

from semantic_kernel.agents import ChatCompletionAgent, SequentialOrchestration
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents import (
    ChatMessageContent,
    ChatHistorySummarizationReducer
)
from semantic_kernel.functions import kernel_function, KernelArguments

# For typing hints only (not runtime dependency)
if TYPE_CHECKING:
    from chromadb.api.models.Collection import Collection

# -------------------------------------------
# Utility Functions
# -------------------------------------------
def load_subcommands(
    info_path: str = "../json/dorado_subcommand_info.json",
    param_path: str = "../json/dorado_subcommand_parameter.json",
) -> tuple[dict, dict]:
    with open(info_path, "r") as f:
        subcommand_info = json.load(f)
    with open(param_path, "r") as f:
        subcommand_parameter = json.load(f)
    return subcommand_info, subcommand_parameter

def agent_response_callback(message: ChatMessageContent) -> None:
    # print(f"# {message.name}\n{message.content}")
    print("Dorado Running...")

# -------------------------------------------
# Dorado CodeGeneratorPlugin (all methods together)
# -------------------------------------------
class CodeGeneratorPlugin:
    def __init__(
        self, collection: "Collection", subcommand_parameter_dict: Dict[str, Any] = None
    ):
        self.subcommand_parameter = subcommand_parameter_dict
        self.collection = collection

    @kernel_function(
        description="Get the subcommand parameter",
        name="get_subcommand_parameter",
    )
    def get_subcommand_parameter(self, subcommand_name: str) -> Dict[str, Any]:
        return self.subcommand_parameter[subcommand_name]

    @kernel_function(
        description="Get the document context",
        name="get_document_context",
    )
    def get_document_context(self, user_query: str) -> str:
        return self.collection.query(query_texts=[user_query], n_results=10)

    @kernel_function(
        description="Generate a prompt for the LLM given tool parameters JSON and the user's task request.",
        name="generate_tool_prompt",
    )
    def generate_tool_prompt(self, tool_definition: Dict[str, Any], user_task: str) -> str:
        """
        Generate a prompt for the LLM given tool parameters JSON and the user's task request. English only.
        """
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
            "2. Only use the parameters that are shown in the parameter definition. "
            "Never use parameters that are not in the parameter definition."
            "3. Do not use space as a parameter value. Use a name instead."
        )
        return prompt

# -------------------------------------------
# Dorado agent and orchestration setup module
# -------------------------------------------
from dotenv import load_dotenv
import os
import chromadb
from openai import AsyncOpenAI

# === Core Data Loading and Shared Resources ===

def get_subcommand_info_and_collection():
    """
    Loads subcommand info/parameters and returns them
    along with an initialized ChromaDB document collection.
    """
    SUBCOMMANDINFO, subcommand_parameter = load_subcommands()
    chroma_client = chromadb.PersistentClient(path="../db/dorado_db")
    collection = chroma_client.get_or_create_collection(
        name="dorado_documents",
        metadata={"description": "dorado_import_documents"},
    )
    # Insert example doc on first load (idempotent by doc_id)
    documents = [
        (
            "Before basecalling, it's necessary to ask user whether he or she has downloaded the model. "
            "If not, tell him use subcommand 'download_model' of download to finish the task."
        ),
    ]
    collection.add(
        documents=documents,
        ids=[f"doc_{i}" for i in range(len(documents))],
        metadatas=[{"source": "training"} for _ in documents],
    )
    return SUBCOMMANDINFO, subcommand_parameter, collection

def get_chat_completion_service():
    load_dotenv()
    client = AsyncOpenAI(
        api_key=os.environ["GITHUB_TOKEN"],
        base_url="https://models.inference.ai.azure.com/",
    )
    return OpenAIChatCompletion(
        ai_model_id="gpt-4o",
        async_client=client,
    )

# === Pydantic Data Structures ===

class SubTask(BaseModel):
    assigned_subcommand: str = Field(
        description="The specific subcommand assigned to handle this subtask"
    )
    task_details: str = Field(
        description="Detailed description of what needs to be done for this subtask"
    )

class PreparePlan(BaseModel):
    main_task: str = Field(
        description="The overall request from the user"
    )
    subtasks: List[SubTask] = Field(
        description="List of subtasks broken down from the main task, each assigned to a specialized subcommand"
    )

# === Agent Factory Functions ===

def create_prepare_agent(
    chat_completion_service, SUBCOMMANDINFO, settings=None, agent_name="Prepare_Agent"
):
    """
    Returns the preparation/planner agent instance.
    """
    AGENT_INSTRUCTIONS_PRE = (
        "You are an planner agent.\n"
        "    Your job is to decide which subcommand to run based on the user's request.\n"
        "    Below are the available agents specialised in different tasks:\n"
    )
    for name, info in SUBCOMMANDINFO.items():
        AGENT_INSTRUCTIONS_PRE += (
            f"\n - {name}: {info.get('description')}\tInput: {info.get('input')}"
        )

    _settings = settings or OpenAIChatPromptExecutionSettings(response_format=PreparePlan)

    return ChatCompletionAgent(
        service=chat_completion_service,
        description="You are an planner agent.",
        name=agent_name,
        instructions=AGENT_INSTRUCTIONS_PRE,
        arguments=KernelArguments(_settings),
    )

def create_code_generator_agent(
    chat_completion_service, collection, subcommand_parameter, agent_name="CodeGeneratorAgent"
):
    """
    Returns the Dorado code generator agent instance.
    """
    AGENT_INSTRUCTIONS_CODE = """
    ### Role
    You are the Dorado Code Generator Agent, an expert in Oxford Nanopore data processing. You generate precise commands while providing intelligent, context-aware suggestions for downstream analysis.

    ### Workflow

    #### 1. Smart Information Audit (The Delta Check)
    Analyze input to identify **MISSING** variables. Acknowledge what is known; only ask for the unknown:
    * **Goal**: (basecall, demux, or alignment)
    * **Molecule**: (DNA or RNA)
    * **Modifications**: (Which specific mods, or "none")

    #### 2. Code Generation (Once all variables are known)
    - **Model Precision**:
        - Single Mod: Use single-mod suffix (e.g., `_2OmeC@v1`).
        - Combined Mods: Use combined suffix ONLY if multiple mods are requested (e.g., `_m5C_2OmeC@v1`).
    - **Sync Flag**: `--modified-bases` MUST exactly match the modifications in the model name.
    - **Accuracy**: Default to `hac` unless `sup` is required for that specific mod combination.
    - **Syntax**: Wrap code in <code>...</code>. Use `[INPUT_PATH]` and `[OUTPUT_BAM]`.

    #### 3. Proactive Expert Suggestions (Post-Command)
    After providing the code, offer these optional value-adds:
    - **Visualization Tip**: "If you plan to plot signal traces or perform signal-to-base alignment later, I suggest adding `--emit-moves` to your command."
    - **Downstream Summary**: Ask if they want a summary: "Would you like me to generate a command to produce a `summary.txt` file for this run to check translocation speeds and Q-scores?"

    ---

    ### Interaction Protocol Examples

    **User:** "Basecall RNA for 2OmeC."
    **Agent:** "Got it. Preparing the command for RNA basecalling with 2OmeC detection.

    <code>dorado basecaller rna004_130bps_sup@v5.2.0_2OmeC@v1 [INPUT_PATH] --modified-bases 2OmeC > [OUTPUT_BAM]</code>

    **Expert Tips:**
    - **Plotting:** If you need to visualize signal traces later, consider adding `--emit-moves`.
    - **Next Step:** Would you like the command to generate a summary file for this run to evaluate sequencing quality?"

    **User:** "I want to basecall RNA."
    **Agent:** "I see you're working with RNA. Do you need to detect any specific modifications (e.g., m6A, m5C, 2OmeC), or should I proceed with standard basecalling?"
    """
    return ChatCompletionAgent(
        service=chat_completion_service,
        description="You are an code generator agent.",
        name=agent_name,
        instructions=AGENT_INSTRUCTIONS_CODE,
        plugins=[CodeGeneratorPlugin(collection, subcommand_parameter)],
    )

def get_history_reducer(chat_completion_service, target_count=1, threshold_count=4):
    return ChatHistorySummarizationReducer(
        service=chat_completion_service,
        target_count=target_count,
        threshold_count=threshold_count,
    )

def get_sequential_orchestration(pre_agent, code_agent, agent_response_callback):
    """
    Returns the SequentialOrchestration composed of the planner and code generation agents.
    """
    return SequentialOrchestration(
        members=[pre_agent, code_agent],
        agent_response_callback=agent_response_callback,
    )

# def get_dorado_orchestration():
#     SUBCOMMANDINFO, subcommand_parameter, collection = get_subcommand_info_and_collection()
#     chat_completion_service = get_chat_completion_service()
#     pre_agent = create_prepare_agent(chat_completion_service, SUBCOMMANDINFO)
#     code_agent = create_code_generator_agent(chat_completion_service, collection, subcommand_parameter)
#     history_reducer = get_history_reducer(chat_completion_service)
#     # You may now use: pre_agent, code_agent, history_reducer, or combine via:
#     chat = get_sequential_orchestration(pre_agent, code_agent, agent_response_callback)
#     return chat, history_reducer

# # === Quick Usage Example (NOT run on import) ===
# if __name__ == "__main__":
#     # This block gives an example of setting up everything for interactive use.
#     SUBCOMMANDINFO, subcommand_parameter, collection = get_subcommand_info_and_collection()
#     chat_completion_service = get_chat_completion_service()
#     pre_agent = create_prepare_agent(chat_completion_service, SUBCOMMANDINFO)
#     code_agent = create_code_generator_agent(chat_completion_service, collection, subcommand_parameter)
#     history_reducer = get_history_reducer(chat_completion_service)
#     # You may now use: pre_agent, code_agent, history_reducer, or combine via:
#     chat = get_sequential_orchestration(pre_agent, code_agent, agent_response_callback)


# Example: How to import and use this module from another Python file

# In your other Python script (e.g., main.py) in the same directory or with this directory on your PYTHONPATH:

# from llm.ONT_plus.scripts.codes import dorado_agent

# # Load info, parameters, and collection
# SUBCOMMANDINFO, subcommand_parameter, collection = dorado_agent.get_subcommand_info_and_collection()

# # Set up chat completion service
# chat_completion_service = dorado_agent.get_chat_completion_service()

# # Create agents
# pre_agent = dorado_agent.create_prepare_agent(chat_completion_service, SUBCOMMANDINFO)
# code_agent = dorado_agent.create_code_generator_agent(
#     chat_completion_service, collection, subcommand_parameter
# )

# # Optionally, create a history reducer and an orchestration pipeline
# history_reducer = dorado_agent.get_history_reducer(chat_completion_service)
# orchestration = dorado_agent.get_sequential_orchestration(
#     pre_agent, code_agent, dorado_agent.agent_response_callback
# )



