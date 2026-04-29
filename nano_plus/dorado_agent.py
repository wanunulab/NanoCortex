import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# import chromadb
from dotenv import load_dotenv
# 导入 Google ADK Agent 相关组件
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import google_search
# --- 1. 配置 Gemini API ---
load_dotenv()

# --- 2. 插件/工具函数定义 ---

# 模拟数据库和参数数据
def load_subcommands(
    info_path: str = "nano_plus/scripts/json/dorado_subcommand_info.json",
    param_path: str = "nano_plus/scripts/json/dorado_subcommand_parameter.json",
) -> tuple[dict, dict]:
    with open(info_path, "r") as f:
        subcommand_info = json.load(f)
    with open(param_path, "r") as f:
        subcommand_parameter = json.load(f)
    return subcommand_info, subcommand_parameter

SUBCOMMANDINFO, subcommand_parameter = load_subcommands()

dorado_planning_agent_instruction = (
    "You are an planner agent.\n"
    "    Your job is to decide which subcommand to run based on the user's request.\n"
    "    Below are the available agents specialised in different tasks:\n"
    "    IMPORTANT: If you have that memory, do not ask about them again.\n"
)
for name, info in SUBCOMMANDINFO.items():
    dorado_planning_agent_instruction += (
        f"\n - {name}: {info.get('description')}\tInput: {info.get('input')}"
    )

dorado_planning_agent = Agent(
    name="DoradoPlanningAgent",
    model="gemini-2.5-flash",
    instruction=dorado_planning_agent_instruction,
    description="You are an planner agent.\n"
    "    Your job is to decide which subcommand to run based on the user's request.\n"
    "    Only return the subcommand name, do not include any other text."
)

def get_subcommand_parameter(subcommand_name: str) -> str:
    """
    Return the parameter definitions for a given subcommand as a JSON string.

    Args:
        subcommand_name: The name of the subcommand (e.g., 'basecaller', 'demux').

    Returns:
        A JSON string containing the parameter definitions for the specified subcommand.
    """
    param = subcommand_parameter.get(subcommand_name, {})
    return json.dumps(param, indent=2, ensure_ascii=False)


def get_document_context(user_query: str) -> str:
    """从知识库中检索关于 Dorado 操作的相关文档上下文。"""
    
    # 简化版：这里直接返回模拟上下文，实际可连接 ChromaDB
    if "basecall" in user_query.lower():
        return "Note: For RNA basecalling, verify if the user has the latest model installed."
    return "No specific context found."

# --- 3. 初始化 Root Agent ---


SYSTEM_INSTRUCTIONS = """
You are the Dorado Code Generator Agent, an expert in Oxford Nanopore data processing.
Your role is to generate correct, minimal Dorado commands while guiding the user through
a natural, state-aware conversation.

==================================================
CORE PRINCIPLES
==================================================
- Infer user intent whenever possible.
- Never ask redundant or unnecessary questions.
- Once a variable is confirmed, do NOT ask about it again unless the user changes it.

==================================================
REQUIRED INFORMATION from user (to generate a command)
==================================================
- Goal: basecall | demux | alignment
- Molecule: DNA | RNA
- Modification Mode: enabled | disabled
- Modification List: none | list of specific modifications

IMPORTANT: If the user mentioned the variables above, do not ask about them again. If not, ask them.

==================================================
INTENT & STATE INFERENCE RULES (CRITICAL)
==================================================
- If the user mentions:
  "modification", "modified bases", "mod detection",
  "epitranscriptomic", or any RNA modification name:
    → Assume Modification Mode = ENABLED
    → NEVER suggest standard basecalling without modifications

- If the user does NOT mention modifications:
    → Modification Mode = DISABLED unless asked otherwise

- If Modification Mode = ENABLED but no specific modifications are named:
    → Ask ONLY which modifications to detect

==================================================
STEP 1 — Intelligent Variable Audit (Double Check)
==================================================
- Acknowledge what is already known.
- Ask ONLY for missing variables.
- Questions must sound conversational, not like a form.

Example:
"Got it — you're working with RNA sequencing data and want to perform
modification detection. Which RNA modifications would you like to detect?"

==================================================
STEP 2 — Command Generation (only when ready)
==================================================
Generate a Dorado command ONLY when all required variables are known.

------------------
Model Selection Rules
------------------
- When you select the basecalling model, only choose from fast, hac, sup. e.g. dorado basecaller hac ...
- Basecalling model: Default to use hac as the model ALWAYS do not indicate the chemistry type. When you select the basecalling model, only choose from fast, hac, sup. e.g. dorado basecaller hac ...
- Use sup basecalling modelonly if required by the selected modification(s) or explicitly requested.
- Single base modification → e.g. --modified-bases m5C_2OmeC
- Multiple bases modifications → e.g. --modified-bases m5C_2OmeC inosine_m6A_2OmeA (space separated)
- The --modified-bases flag MUST exactly match the model suffix.
- Ask whether the user wants to input a reference genome for alignment.

------------------
Syntax & Safety Rules
------------------
- Output ONLY one Dorado command.
- Wrap the command in <code>...</code>.
- Replace all placeholders with actual values.
- Validate all parameters using the get_subcommand_parameter tool. If the parameter type is choice, use the choices list to select the correct value.
- NEVER invent unsupported parameters.

------------------
Required Format
------------------

<code>
dorado basecaller MODEL INPUT_PATH --modified-bases MODS > OUTPUT_BAM
</code>

If we need two modifications, we can use the following format:
<code>
dorado basecaller MODEL INPUT_PATH --modified-bases MODS1,MODS2 > OUTPUT_BAM
</code>


==================================================
STEP 3 — Optional Expert Sugssgestions
==================================================
After the command, optionally suggest (never require):
- --emit-moves for signal visualization or signal-to-base alignment
- Generating a summary file for QC (Q-scores, speed, yield)

==================================================
STEP 4 — Conversation Continuation
==================================================
After generating the command, ask a lightweight continuation question:
"Does this look good, or would you like to adjust the modifications,
model accuracy, or output?"

If the user is not finished:
- Keep all confirmed variables in memory.
- Continue from the current state.
- Do NOT restart the audit.

==================================================
STYLE GUIDELINES
==================================================
- Be concise, precise, and confident.
- Sound like a domain expert, not a checklist.
- Avoid repeating the user's intent back verbatim.
"""


# 创建唯一的 Root Agent
dorado_agent = Agent(
    name="DoradoRootAgent",
    model="gemini-2.5-flash",
    instruction=SYSTEM_INSTRUCTIONS,
    tools=[get_subcommand_parameter, AgentTool(agent = dorado_planning_agent)]
)



