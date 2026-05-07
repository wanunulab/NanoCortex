import os
import asyncio
from enum import Enum
from typing import ClassVar, Annotated, Optional, Any
from pydantic import Field
from dotenv import load_dotenv
from openai import AsyncOpenAI

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_context import KernelProcessStepContext
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start
from semantic_kernel.processes.process_builder import ProcessBuilder
from semantic_kernel.agents.runtime import InProcessRuntime
import dorado_agent 
from semantic_kernel.contents import ChatHistorySummarizationReducer
import modkit_agent

# --- Utility Functions ---
def get_chat_completion_service():
    load_dotenv()
    client = AsyncOpenAI(
        api_key=os.environ.get("GITHUB_TOKEN"),
        base_url="https://models.inference.ai.azure.com/",
    )
    return OpenAIChatCompletion(
        api_key=os.environ.get("GITHUB_TOKEN"),
        ai_model_id="gpt-4o-mini",
        async_client=client,
    )

def generate_dorado_orchestration(chat_completion_service):
    SUBCOMMANDINFO, subcommand_parameter, collection = dorado_agent.get_subcommand_info_and_collection()
    pre_agent = dorado_agent.create_prepare_agent(chat_completion_service, SUBCOMMANDINFO)
    code_agent = dorado_agent.create_code_generator_agent(
        chat_completion_service, collection, subcommand_parameter
    )
    return dorado_agent.get_sequential_orchestration(
        pre_agent, code_agent, dorado_agent.agent_response_callback
    )

# --- Event Definitions ---
class CommonEvents(Enum):
    UserInputReceived = "UserInputReceived"
    ValidationFailed = "ValidationFailed"
    ToDorado = "ToDorado"
    ToModkit = "ToModkit"

class ChatBotEvents(Enum):
    StartProcess = "startProcess"
    AssistantResponseGenerated = "assistantResponseGenerated"
    Exit = "exit"

# --- State Model ---
class GlobalChatState(KernelBaseModel):
    history: ChatHistorySummarizationReducer = None
    is_dorado_finished: bool = False

# --- Step Definitions ---

class IntroStep(KernelProcessStep):
    @kernel_function
    async def print_intro_message(self):
        print("Welcome to the Nanopore Data Analysis Orchestrator (Dorado & Modkit).")
        print("Type 'exit' to quit the program.\n")

class UserInputStep(KernelProcessStep):
    @kernel_function
    async def get_user_input(self, context: KernelProcessStepContext):
        user_message = input("USER: ")
        if "exit" in user_message.lower():
            await context.emit_event(process_event=ChatBotEvents.Exit, data=None)
            return
        await context.emit_event(process_event=CommonEvents.UserInputReceived, data=user_message)

class InputValidationStep(KernelProcessStep[GlobalChatState]):

    state: GlobalChatState = Field(default_factory=GlobalChatState)

    async def activate(self, state: KernelProcessStepState[GlobalChatState]):
        self.state = global_state

    @kernel_function
    async def validate_input(
        self, 
        context: KernelProcessStepContext, 
        user_message: str, 
        kernel: Kernel
    ):
        clean_msg = user_message.strip().lower()
        current_state = self.state
        if current_state.is_dorado_finished:
            print("ASSISTANT: Dorado workflow completed. Routing to Modkit.")
            await context.emit_event(process_event=CommonEvents.ToModkit, data=user_message)
            return
        
        if clean_msg in ["yes", "no", "y", "n", "ok"]:
            await context.emit_event(process_event=CommonEvents.ToDorado, data=user_message)
            return

        history_context = ""
        if current_state and current_state.history and len(current_state.history.messages) > 0:
            history_context = "\nContext:\n" + "\n".join([f"{m.role}: {m.content}" for m in current_state.history.messages[-3:]])

        prompt = (
            "Classify Nanopore workflow task.\n"
            f"{history_context}\n"
            f"Message: {user_message}\n"
            "Respond: 'dorado', 'modkit', or 'chat'."
        )
        response = await kernel.invoke_prompt(prompt)
        category = str(response).lower().strip()
        current_state.history.add_user_message(user_message)

        if "dorado" in category:
            await context.emit_event(process_event=CommonEvents.ToDorado, data=user_message)
        elif "modkit" in category:
            await context.emit_event(process_event=CommonEvents.ToModkit, data=user_message)
        else:
            print("ASSISTANT: Not bio-related. Try again.")
            await context.emit_event(process_event=CommonEvents.ValidationFailed, data=None)

class DoradoResponseStep(KernelProcessStep[GlobalChatState]):
    _dorado_orchestration: Optional[Any] = None
    state: GlobalChatState = Field(default_factory=GlobalChatState)

    async def activate(self, state: KernelProcessStepState[GlobalChatState]):
        self.state = global_state

    @kernel_function
    async def run_dorado(
        self, 
        context: KernelProcessStepContext, 
        validated_message: str, 
        kernel: Kernel
    ):
        print(f"ASSISTANT: [Dorado] processing...")
        current_state = self.state
        
        if validated_message.strip().lower() in ["yes", "y", "ok"]:
            if current_state:
                current_state.is_dorado_finished = True
            await context.emit_event(process_event=CommonEvents.ToModkit, data=validated_message)
            return

        if self._dorado_orchestration is None:
            self._dorado_orchestration = generate_dorado_orchestration(kernel.get_service(type=ChatCompletionClientBase))
        
        runtime = InProcessRuntime()
        runtime.start()
        history_msgs = current_state.history.messages if current_state and current_state.history else []
        res = await self._dorado_orchestration.invoke(task=history_msgs, runtime=runtime)
        response = await res.get(timeout=1000)
        await runtime.stop_when_idle()
        
        content = response.content
        print(f"DORADO: {content}")
        if current_state and current_state.history:
            current_state.history.add_assistant_message(content)
        
        await context.emit_event(process_event=ChatBotEvents.AssistantResponseGenerated, data=content)

class ModkitResponseStep(KernelProcessStep[GlobalChatState]):
    _modkit_orchestration: Optional[Any] = None
    state: GlobalChatState = Field(default_factory=GlobalChatState)

    async def activate(self, state: KernelProcessStepState[GlobalChatState]):
        self.state = global_state

    @kernel_function
    async def run_modkit(
        self, 
        context: KernelProcessStepContext, 
        validated_message: str, 
        kernel: Kernel
    ):
        print(f"ASSISTANT: [Modkit] processing...")
        current_state = self.state
        
        if self._modkit_orchestration is None:
            self._modkit_orchestration = modkit_agent.start_modkit_agents(kernel.get_service(type=ChatCompletionClientBase), dorado_agent.agent_response_callback)

        if current_state and current_state.history:
            current_state.history.add_user_message(validated_message)
        
        runtime = InProcessRuntime()
        runtime.start()
        history_msgs = current_state.history.messages if current_state and current_state.history else []
        res = await self._modkit_orchestration.invoke(task=history_msgs, runtime=runtime)
        response = await res.get(timeout=1000)
        await runtime.stop_when_idle()
        
        content = response.content
        print(f"MODKIT: {content}")
        if current_state and current_state.history:
            current_state.history.add_assistant_message(content)
        
        await context.emit_event(process_event=ChatBotEvents.AssistantResponseGenerated, data=content)


# --- Execution ---
async def run_process():
    chat_service = get_chat_completion_service()
    kernel = Kernel()
    kernel.add_service(chat_service)
    history = ChatHistorySummarizationReducer(
        service=chat_service,
        target_count=4,
        threshold_count=10,
    )
    global global_state
    global_state = GlobalChatState(history=history)
    process_builder = ProcessBuilder(name="Workflow")

    # ADDED: Using simple add_step without initial_state in the constructor
    # The SDK will handle the state container initialization. 
    # If custom initialization is needed and initial_state fails, 
    # we define the steps first and then build the process.
    intro = process_builder.add_step(IntroStep)
    user_input = process_builder.add_step(UserInputStep)
    validator = process_builder.add_step(InputValidationStep)
    dorado_proc = process_builder.add_step(DoradoResponseStep)
    modkit_proc = process_builder.add_step(ModkitResponseStep)

    # Note: If the error persists, it usually means the Step class 
    # is missing the Generic type in its declaration. 
    # We have ensured KernelProcessStep[GlobalChatState] is used.

    process_builder.on_input_event(ChatBotEvents.StartProcess).send_event_to(target=intro)
    intro.on_function_result("print_intro_message").send_event_to(target=user_input)
    user_input.on_event(CommonEvents.UserInputReceived).send_event_to(target=validator, parameter_name="user_message")
    user_input.on_event(ChatBotEvents.Exit).stop_process()
    validator.on_event(CommonEvents.ValidationFailed).send_event_to(target=user_input)
    validator.on_event(CommonEvents.ToDorado).send_event_to(target=dorado_proc, parameter_name="validated_message")
    validator.on_event(CommonEvents.ToModkit).send_event_to(target=modkit_proc, parameter_name="validated_message")
    dorado_proc.on_event(ChatBotEvents.AssistantResponseGenerated).send_event_to(target=user_input)
    dorado_proc.on_event(CommonEvents.ToModkit).send_event_to(target=modkit_proc, parameter_name="validated_message")
    modkit_proc.on_event(ChatBotEvents.AssistantResponseGenerated).send_event_to(target=user_input)

    # Build and start
    kernel_process = process_builder.build()
    
    # We start the process with the initial event
    await start(
        process=kernel_process, 
        kernel=kernel, 
        initial_event=KernelProcessEvent(id=ChatBotEvents.StartProcess)
    )

if __name__ == "__main__":
    asyncio.run(run_process())