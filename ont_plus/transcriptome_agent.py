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
from google.adk.agents import LlmAgent
from google.adk.code_executors import BuiltInCodeExecutor

# --- 1. 配置 Gemini API ---
load_dotenv()

# --- 2. 插件/工具函数定义 ---


AGENT_NAME = "json_reader_agent"
APP_NAME = "modkit"
USER_ID = "user1234"
SESSION_ID = "session_code_exec_async"
GEMINI_MODEL = "gemini-2.0-flash"

search_agent = Agent(
    name="SearchAgent",
    model="gemini-2.5-flash",
    instruction="You are the search agent of the softwares Flair and Stringtie. You are responsible for searching the internet for information to help the agent to write the command.",
    tools=[google_search]
)

# 创建唯一的 Root Agent
transcriptome_agent = Agent(
    name="TranscriptomeAgent",
    model="gemini-2.5-flash",
    instruction="""You are a transcriptome agent.
    You are responsible for writing the flair command based on the user's request.
    Here are the helpful links for the flair command:
    - Flair transcriptome : https://flair.readthedocs.io/en/latest/modules.html#flair-transcriptome
    - Flair quantify : https://flair.readthedocs.io/en/latest/modules.html#flair-quantify
    - Flair fusion : https://flair.readthedocs.io/en/latest/modules.html#flair-fusion
    - Stringtie : https://ccb.jhu.edu/software/stringtie/index.shtml?t=manual
    If the users want to only rely on the annotation gtf file please use flair.
    If the users want to find more new novel transcripts that may not be included in the annotation gtf file please use stringtie.
    The user can also use the GTEXAgent to analyze the isoform usage and significance of the transcripts compared with healthy tissue.
    e.g. "User: Analyze the cancer gene isoform usage and significance of the transcripts compared with healthy tissue."
    "First find some potential cancer genes. Then see whether the cancer genes have differential isoform usage compared with healthy tissue."
    Make sure to ask the user to provide all the necessary input and output paths and parameters for the command.
    """,  
    description = ("This agent is responsible for writing code to deal with basecalled data to analyze transcriptome (de novo transcriptome assembly (stringtie/flair transcriptome) and quantification (flair quantify))"),
    tools=[AgentTool(agent = search_agent)]
)

