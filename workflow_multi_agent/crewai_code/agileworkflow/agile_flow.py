#!/usr/bin/env python
import os
import datetime
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

from crewai.flow import Flow, listen, start

from agileworkflow.crews.agile_crew.agile_crew import AgileCrew


class AgileWorkflowState(BaseModel):
    """敏捷工作流状态模型"""
    # 基本项目信息
    project_name: str = Field(default="", description="项目名称")
    project_description: str = Field(default="", description="项目描述")
    sprint_duration: str = Field(default="14", description="Sprint周期（天）")
    
    # 迭代启动阶段
    sprint_plan: str = Field(default="", description="Sprint计划")
    system_design: str = Field(default="", description="系统架构设计方案")
    requirement_analysis: str = Field(default="", description="需求分析文档")
    
    # 蓝图设计阶段
    blueprint_design: str = Field(default="", description="系统蓝图文档")
    
    # 实现阶段
    frontend_design: str = Field(default="", description="前端实现报告")
    backend_design: str = Field(default="", description="后端实现报告")
    
    # 管理系统阶段
    version_control: str = Field(default="", description="版本控制报告")
    agile_dashboard: str = Field(default="", description="项目状态报告")
    feedback_planning: str = Field(default="", description="反馈分析和迭代规划报告")
    
    # 最终输出
    system_design_summary: str = Field(default="", description="系统设计总结文档")
    
    # 兼容性字段
    development_report: str = Field(default="", description="开发实现报告")
    test_report: str = Field(default="", description="测试报告")


class AgileWorkflowFlow(Flow[AgileWorkflowState]):
    """敏捷LLM多Agent开发工作流"""

    @start()
    def get_project_info(self):
        """获取项目信息"""
        print("\n=== 敏捷LLM多Agent开发工作流 ===\n")
        print("请提供项目信息：")
        
        # 获取用户输入
        self.state.project_name = input("项目名称: ")
        self.state.project_description = input("项目描述: ")
        
        # 获取Sprint周期，并进行验证
        while True:
            sprint_duration = input("Sprint周期（天，推荐7-30天）: ")
            if sprint_duration.isdigit() and 1 <= int(sprint_duration) <= 60:
                self.state.sprint_duration = sprint_duration
                break
            print("请输入1-60之间的数字")
        
        print(f"\n开始为项目 '{self.state.project_name}' 创建敏捷开发工作流...\n")
        return self.state

    @listen(get_project_info)
    def run_agile_workflow(self, state):
        """运行敏捷开发工作流"""
        print("启动敏捷开发团队...")
        
        # 确保Project目录存在
        os.makedirs("Project", exist_ok=True)
        
        # 创建项目ID（使用当前日期）
        project_id = datetime.datetime.now().strftime("%Y%m%d")
        
        # 创建敏捷团队
        agile_crew = AgileCrew()
        
        # 1. 迭代启动阶段
        print("\n=== 迭代启动阶段 ===")
        
        # 1.1 执行系统架构设计任务
        print("执行系统架构设计任务...")
        system_design_result = (
            agile_crew
            .crew()
            .kickoff(
                inputs={
                    "project_id": project_id,
                    "project_name": state.project_name,
                    "project_description": state.project_description,
                    "sprint_duration": state.sprint_duration,
                    "system_design": self.state.system_design,
                    "requirement_analysis": self.state.requirement_analysis,
                    "blueprint_design": self.state.blueprint_design,
                    "frontend_design": self.state.frontend_design,
                    "backend_design": self.state.backend_design,
                    "version_control": self.state.version_control,
                    "agile_dashboard": self.state.agile_dashboard,
                    "feedback_planning": self.state.feedback_planning,
                    "system_design_summary": self.state.system_design_summary,
                    "development_report": self.state.development_report,
                    "test_report": self.state.test_report
                }
            )
        )
        
        # 保存系统架构设计方案
        self.state.system_design = system_design_result.raw
        print("系统架构设计完成！")
        
        # 1.2 执行需求分析任务
        print("执行需求分析任务...")
        requirement_analysis_result = (
            agile_crew
            .crew()
            .kickoff(
                inputs={
                    "project_id": project_id,
                    "project_name": state.project_name,
                    "project_description": state.project_description,
                    "sprint_duration": state.sprint_duration,
                    "system_design": self.state.system_design,
                    "requirement_analysis": self.state.requirement_analysis,
                    "blueprint_design": self.state.blueprint_design,
                    "frontend_design": self.state.frontend_design,
                    "backend_design": self.state.backend_design,
                    "version_control": self.state.version_control,
                    "agile_dashboard": self.state.agile_dashboard,
                    "feedback_planning": self.state.feedback_planning,
                    "system_design_summary": self.state.system_design_summary,
                    "development_report": self.state.development_report,
                    "test_report": self.state.test_report
                }
            )
        )
        
        # 保存需求分析文档
        self.state.requirement_analysis = requirement_analysis_result.raw
        print("需求分析完成！")
        
        # 2. 蓝图设计阶段
        print("\n=== 蓝图设计阶段 ===")
        
        # 执行蓝图设计任务
        print("执行系统蓝图设计任务...")
        blueprint_design_result = (
            agile_crew
            .crew()
            .kickoff(
                inputs={
                    "project_id": project_id,
                    "project_name": state.project_name,
                    "project_description": state.project_description,
                    "sprint_duration": state.sprint_duration,
                    "system_design": self.state.system_design,
                    "requirement_analysis": self.state.requirement_analysis,
                    "blueprint_design": self.state.blueprint_design,
                    "frontend_design": self.state.frontend_design,
                    "backend_design": self.state.backend_design,
                    "version_control": self.state.version_control,
                    "agile_dashboard": self.state.agile_dashboard,
                    "feedback_planning": self.state.feedback_planning,
                    "system_design_summary": self.state.system_design_summary,
                    "development_report": self.state.development_report,
                    "test_report": self.state.test_report
                }
            )
        )
        
        # 保存蓝图设计文档
        self.state.blueprint_design = blueprint_design_result.raw
        print("系统蓝图设计完成！")
        
        # 3. 实现阶段
        print("\n=== 实现阶段 ===")
        
        # 3.1 执行前端设计任务
        print("执行前端设计实现任务...")
        frontend_design_result = (
            agile_crew
            .crew()
            .kickoff(
                inputs={
                    "project_id": project_id,
                    "project_name": state.project_name,
                    "project_description": state.project_description,
                    "sprint_duration": state.sprint_duration,
                    "system_design": self.state.system_design,
                    "requirement_analysis": self.state.requirement_analysis,
                    "blueprint_design": self.state.blueprint_design,
                    "frontend_design": self.state.frontend_design,
                    "backend_design": self.state.backend_design,
                    "version_control": self.state.version_control,
                    "agile_dashboard": self.state.agile_dashboard,
                    "feedback_planning": self.state.feedback_planning,
                    "system_design_summary": self.state.system_design_summary,
                    "development_report": self.state.development_report,
                    "test_report": self.state.test_report
                }
            )
        )
        
        # 保存前端设计报告
        self.state.frontend_design = frontend_design_result.raw
        print("前端设计实现完成！")
        
        # 3.2 执行后端设计任务
        print("执行后端设计实现任务...")
        backend_design_result = (
            agile_crew
            .crew()
            .kickoff(
                inputs={
                    "project_id": project_id,
                    "project_name": state.project_name,
                    "project_description": state.project_description,
                    "sprint_duration": state.sprint_duration,
                    "system_design": self.state.system_design,
                    "requirement_analysis": self.state.requirement_analysis,
                    "blueprint_design": self.state.blueprint_design,
                    "frontend_design": self.state.frontend_design,
                    "backend_design": self.state.backend_design,
                    "version_control": self.state.version_control,
                    "agile_dashboard": self.state.agile_dashboard,
                    "feedback_planning": self.state.feedback_planning,
                    "system_design_summary": self.state.system_design_summary,
                    "development_report": self.state.development_report,
                    "test_report": self.state.test_report
                }
            )
        )
        
        # 保存后端设计报告
        self.state.backend_design = backend_design_result.raw
        print("后端设计实现完成！")
        
        # 4. 管理系统阶段
        print("\n=== 管理系统阶段 ===")
        
        # 4.1 执行版本控制任务
        print("执行版本控制管理任务...")
        version_control_result = (
            agile_crew
            .crew()
            .kickoff(
                inputs={
                    "project_id": project_id,
                    "project_name": state.project_name,
                    "project_description": state.project_description,
                    "sprint_duration": state.sprint_duration,
                    "system_design": self.state.system_design,
                    "requirement_analysis": self.state.requirement_analysis,
                    "blueprint_design": self.state.blueprint_design,
                    "frontend_design": self.state.frontend_design,
                    "backend_design": self.state.backend_design,
                    "version_control": self.state.version_control,
                    "agile_dashboard": self.state.agile_dashboard,
                    "feedback_planning": self.state.feedback_planning,
                    "system_design_summary": self.state.system_design_summary,
                    "development_report": self.state.development_report,
                    "test_report": self.state.test_report
                }
            )
        )
        
        # 保存版本控制报告
        self.state.version_control = version_control_result.raw
        print("版本控制管理完成！")
        
        # 4.2 执行敏捷仪表盘任务
        print("执行敏捷仪表盘管理任务...")
        agile_dashboard_result = (
            agile_crew
            .crew()
            .kickoff(
                inputs={
                    "project_id": project_id,
                    "project_name": state.project_name,
                    "project_description": state.project_description,
                    "sprint_duration": state.sprint_duration,
                    "system_design": self.state.system_design,
                    "requirement_analysis": self.state.requirement_analysis,
                    "blueprint_design": self.state.blueprint_design,
                    "frontend_design": self.state.frontend_design,
                    "backend_design": self.state.backend_design,
                    "version_control": self.state.version_control,
                    "agile_dashboard": self.state.agile_dashboard,
                    "feedback_planning": self.state.feedback_planning,
                    "system_design_summary": self.state.system_design_summary,
                    "development_report": self.state.development_report,
                    "test_report": self.state.test_report
                }
            )
        )
        
        # 保存敏捷仪表盘报告
        self.state.agile_dashboard = agile_dashboard_result.raw
        print("敏捷仪表盘管理完成！")
        
        # 4.3 执行反馈规划任务
        print("执行反馈规划任务...")
        feedback_planning_result = (
            agile_crew
            .crew()
            .kickoff(
                inputs={
                    "project_id": project_id,
                    "project_name": state.project_name,
                    "project_description": state.project_description,
                    "sprint_duration": state.sprint_duration,
                    "system_design": self.state.system_design,
                    "requirement_analysis": self.state.requirement_analysis,
                    "blueprint_design": self.state.blueprint_design,
                    "frontend_design": self.state.frontend_design,
                    "backend_design": self.state.backend_design,
                    "version_control": self.state.version_control,
                    "agile_dashboard": self.state.agile_dashboard,
                    "feedback_planning": self.state.feedback_planning,
                    "system_design_summary": self.state.system_design_summary,
                    "development_report": self.state.development_report,
                    "test_report": self.state.test_report
                }
            )
        )
        
        # 保存反馈规划报告
        self.state.feedback_planning = feedback_planning_result.raw
        print("反馈规划完成！")
        
        # 5. 系统设计总结
        print("\n=== 系统设计总结 ===")
        
        # 执行系统设计总结任务
        print("执行系统设计总结任务...")
        system_design_summary_result = (
            agile_crew
            .crew()
            .kickoff(
                inputs={
                    "project_id": project_id,
                    "project_name": state.project_name,
                    "project_description": state.project_description,
                    "sprint_duration": state.sprint_duration,
                    "system_design": self.state.system_design,
                    "requirement_analysis": self.state.requirement_analysis,
                    "blueprint_design": self.state.blueprint_design,
                    "frontend_design": self.state.frontend_design,
                    "backend_design": self.state.backend_design,
                    "version_control": self.state.version_control,
                    "agile_dashboard": self.state.agile_dashboard,
                    "feedback_planning": self.state.feedback_planning,
                    "system_design_summary": self.state.system_design_summary,
                    "development_report": self.state.development_report,
                    "test_report": self.state.test_report
                }
            )
        )
        
        # 保存系统设计总结
        self.state.system_design_summary = system_design_summary_result.raw
        print("\n敏捷开发工作流完成！")
        
        return self.state.system_design_summary

    @listen(run_agile_workflow)
    def save_results(self, system_design_summary):
        """保存工作流结果"""
        print("保存工作流结果...")
        
        # 确保输出目录存在
        import os
        os.makedirs("output", exist_ok=True)
        
        # 保存系统设计总结文档
        with open("output/system_design_summary.md", "w") as f:
            f.write(system_design_summary)
        
        # 保存其他文档
        documents = {
            "system_design.md": self.state.system_design,
            "requirement_analysis.md": self.state.requirement_analysis,
            "blueprint_design.md": self.state.blueprint_design,
            "frontend_design.md": self.state.frontend_design,
            "backend_design.md": self.state.backend_design,
            "version_control.md": self.state.version_control,
            "agile_dashboard.md": self.state.agile_dashboard,
            "feedback_planning.md": self.state.feedback_planning
        }
        
        for filename, content in documents.items():
            if content:
                with open(f"output/{filename}", "w") as f:
                    f.write(content)
        
        print("\n所有文档已保存到 output/ 目录")
        return "敏捷开发工作流已成功完成，所有文档已生成。"


def kickoff():
    """启动敏捷开发工作流"""
    AgileWorkflowFlow().kickoff()
    print("\n=== 工作流完成 ===")
    print("您的所有文档已保存在output目录中。")
    print("系统设计总结文档: output/system_design_summary.md")


def plot():
    """生成工作流可视化图"""
    flow = AgileWorkflowFlow()
    flow.plot("agile_workflow_flow")
    print("工作流可视化图已保存为 agile_workflow_flow.html")


if __name__ == "__main__":
    kickoff()
