import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

import chromadb
from dotenv import load_dotenv
# 导入 Google ADK Agent 相关组件
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import google_search
from google.adk.agents import LlmAgent
from google.adk.code_executors import BuiltInCodeExecutor
# --- 1. 配置 Gemini API ---
load_dotenv()

# --- 2. 插件/工具函数定义 ---


AGENT_NAME = "json_reader_agent"
APP_NAME = "modkit"
USER_ID = "user1234"
SESSION_ID = "session_code_exec_async"
GEMINI_MODEL = "gemini-2.5-flash"

def load_subcommands(
    info_path: str = "nano_plus/scripts/json/modkit_subcommand_info.json",
    param_path: str = "nano_plus/scripts/json/modkit_subcommand_parameter.json",
) -> tuple[dict, dict]:
    with open(info_path, "r") as f:
        subcommand_info = json.load(f)
    with open(param_path, "r") as f:
        subcommand_parameter = json.load(f)
    return subcommand_info, subcommand_parameter

SUBCOMMANDINFO, subcommand_parameter = load_subcommands()

modkit_planning_agent_instruction = (
    "You are an planner agent.\n"
    "    Your job is to decide which subcommand to run based on the user's request.\n"
    "    Below are the available agents specialised in different tasks:\n"
)
for name, info in SUBCOMMANDINFO.items():
    modkit_planning_agent_instruction += (
        f"\n - {name}: {info.get('description')}\tInput: {info.get('input')}"
    )

modkit_planning_agent = Agent(
    name="ModkitPlanningAgent",
    model="gemini-2.5-flash",
    instruction=modkit_planning_agent_instruction,
    description="You are an planner agent.\n"
    "    Your job is to decide which subcommand to run based on the user's request.\n"
)

def get_subcommand_parameter(subcommand_name: str) -> str:
    """Based on the subcommand name, return the parameter for the subcommand.
    The subcommand_name should be approved by ModkitPlanningAgent.
    """
    param = subcommand_parameter.get(subcommand_name, {})
    return json.dumps(param, indent=2, ensure_ascii=False)



# 创建唯一的 Root Agent
modkit_agent = Agent(
    name="ModkitRootAgent",
    model="gemini-2.5-flash",
    instruction="""You are a modkit agent.
    You are responsible for planning the subcommand to run based on the user's request and providing the parameter for the subcommand.
    You should follow the rules below:
    - Use the modkit_planning_agent to access the subcommand information and decide which subcommand to run based on the user's request.
    - Use the get_subcommand_parameter tool to access the parameter information for the subcommand based on the subcommand name.
    - Generate the code for the subcommand based on the parameter.
    Important rules:
    - If you want to generate codes, your code section should start with <code> and end with </code>. Do not include any other text.
    """,
    tools=[AgentTool(agent = modkit_planning_agent), get_subcommand_parameter]   
)



