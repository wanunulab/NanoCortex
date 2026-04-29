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



# search_agent = Agent(
#     name="SearchAgent",
#     model="gemini-2.5-flash",
#     instruction="You are the search agent of the softwares Flair and Stringtie. You are responsible for searching the internet for information to help the agent to write the command.",
#     tools=[google_search]
# )

# 创建唯一的 Root Agent
splicing_agent = Agent(
    name="SplicingAgent",
    model="gemini-2.5-flash",
    instruction="""You are an agent to deal with mRNA splicing analysis.
    Your task contains:
    - Predict genome-wise splicing sites via spliceAI.
    - Predict custome sequence splicing donor and acceptor sites via spliceAI.
    - Prepare finetune dataset for splicing prediction models.
    """,  
    description = ("This agent is responsible for writing code to deal with splicing data"),
    tools=[google_search]
)



# interpreter_agent = Agent(
#     name="InterpreterAgent",
#     model="gemini-2.5-flash",
#     instruction="""You are an agent to interpret the user's results containing:
#     - genome-wise splicing sites which is vcf files
#     - alignment files (bam files)
#     - gene annotation files (gff/gtf files)
#     Your task is to write and excute code to answer some biological questions.
#     """,
#     tools=[google_search]
# )

