from typing import Type
import os
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class FileWriterToolInput(BaseModel):
    """写入文件工具的输入模式"""
    content: str = Field(..., description="要写入文件的内容")
    file_name: str = Field(..., description="文件名，例如：requirement_1.md")
    project_id: str = Field(..., description="项目ID，例如：1")
    project_name: str = Field(..., description="项目名称，例如：电商系统")


class FileWriterTool(BaseTool):
    name: str = "文件写入工具"
    description: str = (
        "将内容写入到指定的文件中。这个工具可以用来保存需求文档、设计文档等。"
        "文件将被保存为Project/project_{project_id}_{project_name}/{file_name}。"
    )
    args_schema: Type[BaseModel] = FileWriterToolInput

    def _run(self, content: str, file_name: str, project_id: str, project_name: str) -> str:
        """
        将内容写入到指定的文件中
        
        参数:
            content: 要写入的内容
            file_name: 文件名
            project_id: 项目ID
            project_name: 项目名称
            
        返回:
            写入成功的消息
        """
        # 创建项目目录
        project_dir = f"Project/project_{project_id}_{project_name}"
        os.makedirs(project_dir, exist_ok=True)
        
        # 构建文件路径
        file_path = os.path.join(project_dir, file_name)
        
        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return f"内容已成功写入到 {file_path}"