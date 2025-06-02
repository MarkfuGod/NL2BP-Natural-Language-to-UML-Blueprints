from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Dict, Any
import os

from agileworkflow.tools.file_writer_tool import FileWriterTool

@CrewBase
class AgileCrew:
    """敏捷开发工作流团队"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # 配置文件路径
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    

    @before_kickoff
    def prepare_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """在工作流开始前准备输入数据"""
        print("准备敏捷开发工作流...")
        
        # 确保必要的输入参数存在
        if 'project_name' not in inputs:
            inputs['project_name'] = "默认项目"
        
        if 'project_description' not in inputs:
            inputs['project_description'] = "这是一个使用敏捷方法开发的项目。"
            
        if 'sprint_duration' not in inputs:
            inputs['sprint_duration'] = "14"
            
        print(f"项目名称: {inputs['project_name']}")
        print(f"项目描述: {inputs['project_description']}")
        print(f"Sprint周期: {inputs['sprint_duration']}天")
        
        return inputs

    @after_kickoff
    def process_output(self, output):
        """在工作流结束后处理输出数据"""
        print("\n敏捷开发工作流完成!")
        print("最终输出是系统设计文档。")
        return output

    # 核心开发Agent

    @agent
    def system_design_agent(self) -> Agent:
        """创建系统架构设计专家Agent"""
        # 读取系统提示模板
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts/system_design_agent_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_template = f.read()
            
        # 创建文件写入工具
        file_writer_tool = FileWriterTool()
        
        return Agent(
            config=self.agents_config["system_design_agent"],  # type: ignore[index]
            verbose=True,
            tools=[file_writer_tool],
            system_template=system_template
        )

    @agent
    def requirement_analysis_agent(self) -> Agent:
        """创建需求分析专家Agent"""
        # 读取系统提示模板
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts/requirement_analysis_agent_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_template = f.read()
            
        # 创建文件写入工具
        file_writer_tool = FileWriterTool()
        
        return Agent(
            config=self.agents_config["requirement_analysis_agent"],  # type: ignore[index]
            verbose=True,
            tools=[file_writer_tool],
            system_template=system_template
        )

    @agent
    def blueprint_design_agent(self) -> Agent:
        """创建系统蓝图设计专家Agent"""
        # 读取系统提示模板
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts/blueprint_design_agent_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_template = f.read()
            
        # 创建文件写入工具
        file_writer_tool = FileWriterTool()
        
        return Agent(
            config=self.agents_config["blueprint_design_agent"],  # type: ignore[index]
            verbose=True,
            tools=[file_writer_tool],
            system_template=system_template
        )

    @agent
    def frontend_design_agent(self) -> Agent:
        """创建前端设计实现专家Agent"""
        # 读取系统提示模板
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts/frontend_design_agent_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_template = f.read()
            
        # 创建文件写入工具
        file_writer_tool = FileWriterTool()
        
        return Agent(
            config=self.agents_config["frontend_design_agent"],  # type: ignore[index]
            verbose=True,
            tools=[file_writer_tool],
            system_template=system_template
        )

    @agent
    def backend_design_agent(self) -> Agent:
        """创建后端设计实现专家Agent"""
        # 读取系统提示模板
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts/backend_design_agent_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_template = f.read()
            
        # 创建文件写入工具
        file_writer_tool = FileWriterTool()
        
        return Agent(
            config=self.agents_config["backend_design_agent"],  # type: ignore[index]
            verbose=True,
            tools=[file_writer_tool],
            system_template=system_template
        )

    # 管理系统Agent

    @agent
    def version_control_agent(self) -> Agent:
        """创建版本控制管理专家Agent"""
        # 读取系统提示模板
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts/version_control_agent_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_template = f.read()
            
        # 创建文件写入工具
        file_writer_tool = FileWriterTool()
        
        return Agent(
            config=self.agents_config["version_control_agent"],  # type: ignore[index]
            verbose=True,
            tools=[file_writer_tool],
            system_template=system_template
        )

    @agent
    def agile_dashboard_agent(self) -> Agent:
        """创建敏捷仪表盘管理专家Agent"""
        # 读取系统提示模板
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts/agile_dashboard_agent_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_template = f.read()
            
        # 创建文件写入工具
        file_writer_tool = FileWriterTool()
        
        return Agent(
            config=self.agents_config["agile_dashboard_agent"],  # type: ignore[index]
            verbose=True,
            tools=[file_writer_tool],
            system_template=system_template
        )

    @agent
    def feedback_planning_agent(self) -> Agent:
        """创建反馈规划专家Agent"""
        # 读取系统提示模板
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts/feedback_planning_agent_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_template = f.read()
            
        # 创建文件写入工具
        file_writer_tool = FileWriterTool()
        
        return Agent(
            config=self.agents_config["feedback_planning_agent"],  # type: ignore[index]
            verbose=True,
            tools=[file_writer_tool],
            system_template=system_template
        )

    # 保留原有Agent用于兼容性

    @agent
    def developer_agent(self) -> Agent:
        """创建开发实现专家Agent"""
        # 读取系统提示模板
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts/developer_agent_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_template = f.read()
            
        # 创建文件写入工具
        file_writer_tool = FileWriterTool()
        
        return Agent(
            config=self.agents_config["developer_agent"],  # type: ignore[index]
            verbose=True,
            tools=[file_writer_tool],
            system_template=system_template
        )

    @agent
    def testing_agent(self) -> Agent:
        """创建测试验证专家Agent"""
        # 读取系统提示模板
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts/testing_agent_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_template = f.read()
            
        # 创建文件写入工具
        file_writer_tool = FileWriterTool()
        
        return Agent(
            config=self.agents_config["testing_agent"],  # type: ignore[index]
            verbose=True,
            tools=[file_writer_tool],
            system_template=system_template
        )

    # 兼容性方法
    @agent
    def blueprint_agent(self) -> Agent:
        """创建核心协调者Agent（兼容性方法）"""
        return self.blueprint_design_agent()

    @agent
    def requirement_agent(self) -> Agent:
        """创建需求分析专家Agent（兼容性方法）"""
        return self.requirement_analysis_agent()

    # 迭代启动阶段任务

    @task
    def sprint_planning_task(self) -> Task:
        """创建Sprint规划任务"""
        return Task(
            config=self.tasks_config["sprint_planning_task"],  # type: ignore[index]
        )

    @task
    def system_design_task(self) -> Task:
        """创建系统架构设计任务"""
        return Task(
            config=self.tasks_config["system_design_task"],  # type: ignore[index]
        )

    @task
    def requirement_analysis_task(self) -> Task:
        """创建需求分析任务"""
        return Task(
            config=self.tasks_config["requirement_analysis_task"],  # type: ignore[index]
            context=[self.system_design_task()]
        )

    # 蓝图设计阶段任务

    @task
    def blueprint_design_task(self) -> Task:
        """创建系统蓝图设计任务"""
        return Task(
            config=self.tasks_config["blueprint_design_task"],  # type: ignore[index]
            context=[
                self.requirement_analysis_task(),
                self.system_design_task()
            ]
        )

    # 实现阶段任务

    @task
    def frontend_design_task(self) -> Task:
        """创建前端设计实现任务"""
        return Task(
            config=self.tasks_config["frontend_design_task"],  # type: ignore[index]
            context=[self.blueprint_design_task()]
        )

    @task
    def backend_design_task(self) -> Task:
        """创建后端设计实现任务"""
        return Task(
            config=self.tasks_config["backend_design_task"],  # type: ignore[index]
            context=[self.blueprint_design_task()]
        )

    # 管理系统任务

    @task
    def version_control_task(self) -> Task:
        """创建版本控制管理任务"""
        return Task(
            config=self.tasks_config["version_control_task"],  # type: ignore[index]
            context=[
                self.blueprint_design_task(),
                self.frontend_design_task(),
                self.backend_design_task()
            ]
        )

    @task
    def agile_dashboard_task(self) -> Task:
        """创建敏捷仪表盘管理任务"""
        return Task(
            config=self.tasks_config["agile_dashboard_task"],  # type: ignore[index]
            context=[
                self.requirement_analysis_task(),
                self.frontend_design_task(),
                self.backend_design_task()
            ]
        )

    @task
    def feedback_planning_task(self) -> Task:
        """创建反馈规划任务"""
        return Task(
            config=self.tasks_config["feedback_planning_task"],  # type: ignore[index]
            context=[
                self.frontend_design_task(),
                self.backend_design_task(),
                self.agile_dashboard_task()
            ]
        )

    # 保留原有任务用于兼容性

    @task
    def development_task(self) -> Task:
        """创建开发实现任务"""
        return Task(
            config=self.tasks_config["development_task"],  # type: ignore[index]
            context=[self.requirement_analysis_task()]
        )

    @task
    def testing_task(self) -> Task:
        """创建测试验证任务"""
        return Task(
            config=self.tasks_config["testing_task"],  # type: ignore[index]
            context=[self.development_task(), self.requirement_analysis_task()]
        )

    @task
    def system_design_summary_task(self) -> Task:
        """创建系统设计总结任务"""
        return Task(
            config=self.tasks_config["system_design_summary_task"],  # type: ignore[index]
            context=[
                self.system_design_task(),
                self.requirement_analysis_task(),
                self.blueprint_design_task(),
                self.frontend_design_task(),
                self.backend_design_task(),
                self.version_control_task(),
                self.agile_dashboard_task(),
                self.feedback_planning_task()
            ]
        )

    @crew
    def crew(self) -> Crew:
        """创建敏捷开发工作流团队"""
        return Crew(
            agents=self.agents,  # 由@agent装饰器自动收集
            tasks=self.tasks,    # 由@task装饰器自动收集
            process=Process.sequential,
            verbose=True,
            output_log_file="agile_workflow_logs.txt"
        )