#!/usr/bin/env python
from random import randint
import sys

from pydantic import BaseModel

from crewai.flow import Flow, listen, start

from agileworkflow.agile_flow import AgileWorkflowFlow

def kickoff():
    """启动敏捷开发工作流"""
    agile_flow = AgileWorkflowFlow()
    agile_flow.kickoff()


def plot():
    """生成敏捷开发工作流可视化图"""
    agile_flow = AgileWorkflowFlow()
    agile_flow.plot("agile_workflow_flow")
    print("敏捷开发工作流可视化图已保存为 agile_workflow_flow.html")

if __name__ == "__main__":
    # 默认运行敏捷开发工作流
    kickoff_agile()
