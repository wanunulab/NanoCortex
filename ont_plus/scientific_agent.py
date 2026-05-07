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
from .execution import code_execute
from .pmc import pmc_search_tool, get_pmc_fulltext_tool
# --- 1. 配置 Gemini API ---
load_dotenv()
import requests
import time
import re


search_agent = Agent(
    name="SearchAgent",
    model="gemini-2.5-flash",
    instruction="You are the search agent of the scientific agent. Please use google scholar to find the related papers and its abstracts.",
    tools=[google_search]
)




system_instruction = """
You are a Biologist. You are responsible for interpretate the data.
For bam/sam files please use samtools to analyze and draw conclusions. You can create tmp files to help you analyze the data and delete them after the analysis.
For txt/csv files please write and run R/bash to analyze, draw plots and draw conclusions. You can create tmp files to help you analyze the data and delete them after the analysis.
For DNA/RNA/Protein sequences please use the ncbi_blast_tool to analyze and draw conclusions. You can create tmp files to help you analyze the data and delete them after the analysis.
If you find any results, please use google scholar to search the related papers and draw conclusions.
If you need to find literature, use `pmc_search_tool` to search for PMC IDs.
Once you have a PMC ID, use `get_pmc_fulltext_tool` to retrieve the full text for analysis.
Everytime run "ml samtools;ml R"
When you want to make plots only use R and try only use the packages in the R environment. If the packages are not installed, ask for user's permission.
A suggested workflow is:
1. Use python, bash and other tools to generate the txt/csv data for the plot.
2. Use R to draw the plot.

"""

# 创建唯一的 Root Agent
scientist_agent = Agent(
    name="ScientistAgent",
    model="gemini-2.5-flash",
    description="This agent is responsible for interpreting the data, making plots and drawing conclusions.",
    instruction=system_instruction,
    tools=[code_execute, AgentTool(agent = search_agent), pmc_search_tool, get_pmc_fulltext_tool]
)



