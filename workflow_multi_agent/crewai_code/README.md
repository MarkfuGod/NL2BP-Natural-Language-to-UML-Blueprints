# AgileWorkflow - 敏捷LLM多Agent开发工作流

## 项目简介

AgileWorkflow 是一个基于 CrewAI 框架构建的敏捷开发工作流系统，通过多个专业化的 AI Agent 协作完成软件开发的全生命周期管理。该系统模拟真实的敏捷开发团队，从需求分析到系统设计，从前后端实现到项目管理，提供完整的自动化开发流程。

## 核心特性

- **多Agent协作**: 10个专业化Agent分工协作，模拟真实敏捷团队
- **完整工作流**: 覆盖需求分析、系统设计、蓝图设计、前后端实现、项目管理等全流程
- **自动化文档生成**: 自动生成系统设计文档、需求分析报告、实现方案等
- **敏捷管理**: 内置Sprint规划、进度跟踪、反馈收集等敏捷管理功能
- **可视化支持**: 支持工作流可视化和项目状态仪表盘

## 系统架构

### Agent角色分工

#### 核心开发Agent
- **系统架构设计专家** (`system_design_agent`): 负责系统架构设计和技术选型
- **需求分析专家** (`requirement_analysis_agent`): 分析用户需求，创建用户故事和验收标准
- **系统蓝图设计专家** (`blueprint_design_agent`): 创建系统蓝图和PlantUML图表
- **前端设计实现专家** (`frontend_design_agent`): 实现用户界面和前端逻辑
- **后端设计实现专家** (`backend_design_agent`): 实现后端服务和API

#### 管理系统Agent
- **版本控制管理专家** (`version_control_agent`): 管理版本历史和变更记录
- **敏捷仪表盘管理专家** (`agile_dashboard_agent`): 跟踪项目进度和状态
- **反馈规划专家** (`feedback_planning_agent`): 收集反馈，规划下一轮迭代

#### 兼容性Agent
- **开发实现专家** (`developer_agent`): 通用开发任务
- **测试验证专家** (`testing_agent`): 测试用例设计和质量保证

### 工作流阶段

1. **项目初始化**: 收集项目基本信息和Sprint配置
2. **迭代启动阶段**: 系统架构设计 → 需求分析
3. **蓝图设计阶段**: 创建系统蓝图和接口规范
4. **实现阶段**: 前端设计实现 → 后端设计实现
5. **管理系统阶段**: 版本控制 → 敏捷仪表盘 → 反馈规划
6. **总结阶段**: 生成系统设计总结文档

## 安装和使用

### 环境要求

- Python 3.10-3.12
- CrewAI >= 0.118.0

### 安装步骤

1. 克隆项目到本地
```bash
git clone <repository-url>
cd crewai_code
```

2. 安装依赖
```bash
pip install -e .
```

### 使用方法

#### 启动敏捷开发工作流
```bash
crewai flow kickoff
```

#### 生成工作流可视化图
```bash
crewai flow plot
```

### 交互流程

1. 启动程序后，系统会提示输入：
   - 项目名称
   - 项目描述  
   - Sprint周期（推荐7-30天）

2. 系统将自动执行以下阶段：
   - 迭代启动阶段（系统设计 + 需求分析）
   - 蓝图设计阶段
   - 实现阶段（前端 + 后端）
   - 管理系统阶段（版本控制 + 仪表盘 + 反馈规划）
   - 总结阶段

3. 所有生成的文档将保存在 `output/` 目录中

## 输出文件

工作流完成后，将在 `output/` 目录生成以下文档：

- `system_design_summary.md` - 系统设计总结文档
- `system_design.md` - 系统架构设计方案
- `requirement_analysis.md` - 需求分析文档
- `blueprint_design.md` - 系统蓝图文档
- `frontend_design.md` - 前端实现报告
- `backend_design.md` - 后端实现报告
- `version_control.md` - 版本控制报告
- `agile_dashboard.md` - 项目状态报告
- `feedback_planning.md` - 反馈分析和迭代规划报告

## 项目结构

```
agileworkflow/
├── __init__.py
├── main.py                 # 主入口文件
├── agile_flow.py          # 核心工作流定义
├── crews/
│   └── agile_crew/
│       ├── __init__.py
│       ├── agile_crew.py  # Agent团队定义
│       ├── config/
│       │   ├── agents.yaml # Agent配置
│       │   └── tasks.yaml  # 任务配置
│       └── prompts/        # Agent提示词
└── tools/                  # 自定义工具
    ├── __init__.py
    ├── custom_tool.py
    └── file_writer_tool.py
```

## 配置说明

### Agent配置 (agents.yaml)
定义了每个Agent的角色、目标和背景故事，可以根据需要调整Agent的专业领域和工作重点。

### 任务配置 (tasks.yaml)
定义了每个阶段的具体任务描述、期望输出和负责的Agent，可以自定义任务流程和输出要求。

## 扩展开发

### 添加新的Agent
1. 在 `config/agents.yaml` 中定义新Agent
2. 在 `config/tasks.yaml` 中添加对应任务
3. 在 `agile_flow.py` 中集成新的工作流步骤

### 自定义工具
在 `tools/` 目录下创建新的工具类，继承CrewAI的BaseTool类。

### 修改工作流
编辑 `agile_flow.py` 中的 `AgileWorkflowFlow` 类，添加新的工作流步骤或修改现有流程。

## 许可证

本项目采用开源许可证，具体许可证信息请查看 LICENSE 文件。

## 贡献指南

欢迎提交Issue和Pull Request来改进项目。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交GitHub Issue
- 发送邮件至项目维护者

---
