# 多代理协作开发工作流程

## 📋 概述

本目录包含了一个基于多代理协作的敏捷软件开发工作流程系统。该系统通过多个专业化Agent之间的消息交换和协作，实现从用户需求到产品交付的完整开发生命周期，并构建了持续演进的敏捷开发闭环。

## 🏗️ 系统架构

### 核心理念
- **多代理协作**: 多个专业化Agent并行工作，通过消息交换协调任务
- **敏捷迭代**: 以迭代为单位的循环式开发流程
- **用户反馈驱动**: 基于用户反馈的持续优化闭环
- **实时监控**: 全程进度跟踪和状态管理

### Agent集合定义

系统中的Agent集合 $\mathcal{A}$ 定义为：

$$\mathcal{A}=\{A_{sd},A_{ra},A_{bd},A_{fe},A_{be},A_{vc},A_{dash},A_{fp},H\}$$

其中：
- $A_{sd}$: System Design Agent（系统架构设计）
- $A_{ra}$: Requirement Analysis Agent（需求分析）
- $A_{bd}$: Blueprint Design Agent（蓝图设计）
- $A_{fe}$: Frontend Design Agent（前端实现）
- $A_{be}$: Backend Design Agent（后端实现）
- $A_{vc}$: Version Control Agent（版本控制）
- $A_{dash}$: Agile Dashboard Agent（进度追踪）
- $A_{fp}$: Feedback Planning Agent（反馈规划）
- $H$: Human Collaborator（人类用户/产品负责人）

## 👥 Agent分类与职责

### 🔧 核心开发Agent

| Agent | 中文名称 | 主要职责 |
|-------|----------|----------|
| $A_{sd}$ | 系统架构设计Agent | 负责系统架构设计和技术选型，将用户需求转化为技术架构方案，定义系统组件和它们之间的关系 |
| $A_{ra}$ | 需求分析Agent | 分析和细化用户需求，创建优先级排序的需求列表，编写用户故事和验收标准 |
| $A_{bd}$ | 蓝图设计Agent | 创建系统蓝图和接口规范，生成PlantUML图表描述系统结构，定义组件间的接口和数据流 |
| $A_{fe}$ | 前端设计Agent | 实现用户界面和前端逻辑，根据蓝图创建UI组件，实现与后端的API调用 |
| $A_{be}$ | 后端设计Agent | 实现后端服务和API，设计数据模型和业务逻辑，创建可部署的后端代码 |

### 🛠️ 管理系统Agent

| Agent | 中文名称 | 主要职责 |
|-------|----------|----------|
| $A_{vc}$ | 版本控制Agent | 维护所有开发产物（如代码、文档）的版本控制，分配版本号并记录历史提交，防止版本冲突 |
| $A_{dash}$ | 敏捷看板Agent | 用于跟踪开发进度，聚合开发状态与关键指标，支持其他Agent或用户查询项目状态 |
| $A_{fp}$ | 反馈规划Agent | 主导用户反馈收集与分析，制定迭代计划，组织团队回顾会议，实现持续优化闭环 |

## 🔄 工作流程详解

### 迭代式开发流程

整个多Agent系统遵循以迭代为单位的循环式开发流程，具体包括五个阶段：

#### 1. 迭代启动阶段
- **触发条件**: 用户提供自然语言需求
- **参与Agent**: $A_{sd}$, $A_{ra}$
- **工作内容**:
  - $A_{sd}$ 创建系统架构方案
  - $A_{ra}$ 将需求分解为功能点并排序
  - 两个Agent通过直接消息交换协作，确保技术设计满足业务需求

#### 2. 蓝图设计阶段
- **参与Agent**: $A_{ra}$, $A_{bd}$, $A_{vc}$
- **工作内容**:
  - $A_{ra}$ 将需求优先级列表传递给 $A_{bd}$
  - $A_{bd}$ 依据已有系统设计生成蓝图文件
  - $A_{vc}$ 管理蓝图版本，供后续调用

#### 3. 实现阶段
- **参与Agent**: $A_{fe}$, $A_{be}$, $A_{vc}$, $A_{dash}$
- **工作内容**:
  - $A_{fe}$ 和 $A_{be}$ 并行工作，实现系统功能
  - 两个Agent从 $A_{vc}$ 获取最新蓝图
  - 根据接口规范各自实现前端和后端代码
  - 定期向 $A_{dash}$ 报告进度和阻碍
  - 通过直接消息交换协调API实现和调用细节

#### 4. 演示与反馈阶段
- **参与Agent**: $A_{fp}$, $H$
- **工作内容**:
  - 当前版本开发完成后，系统整合并生成演示版本
  - 向用户展示当前迭代成果
  - $A_{fp}$ 分析用户反馈并确定优先级

#### 5. 回顾与规划阶段
- **参与Agent**: $A_{fp}$, $A_{ra}$
- **工作内容**:
  - $A_{fp}$ 组织回顾会议，分析成功与不足
  - 基于用户反馈和回顾结果规划下一轮迭代
  - 将规划结果传回 $A_{ra}$，开始新的迭代

## 📡 Agent间通信机制

### 直接通信模式

#### 任务分配与执行
- **模式**: 一个Agent创建任务描述并分配给另一个Agent
- **流程**: 接收Agent执行任务并返回结果
- **示例**: $A_{sd}$ 创建架构后，将其作为任务上下文传给 $A_{ra}$

#### 协作讨论
- **模式**: Agent之间通过结构化消息交换信息和观点
- **用途**: 解决冲突或澄清需求
- **示例**: $A_{fe}$ 和 $A_{be}$ 讨论API接口细节

### 通过管理系统Agent的间接通信

#### 通过版本控制Agent通信
- $A_{bd}$ 将蓝图提交给 $A_{vc}$
- $A_{vc}$ 为蓝图分配版本号并存储
- $A_{fe}$ 和 $A_{be}$ 从 $A_{vc}$ 获取最新蓝图

#### 通过敏捷看板Agent通信
- 所有开发Agent向 $A_{dash}$ 报告进度
- $A_{dash}$ 聚合信息并生成状态报告
- 其他Agent可以查询 $A_{dash}$ 获取项目状态

#### 通过反馈规划Agent通信
- 用户反馈传递给 $A_{fp}$
- $A_{fp}$ 分析反馈并创建迭代计划
- 计划传回 $A_{ra}$ 开始新的迭代

## 📁 目录结构

```
workflow_multi_agent/
├── README.md                          # 本文档
├── crewai_code/                       # CrewAI实现代码
└── workflow_pic/                      # 工作流程图
    └── multi_agent_workflow.svg       # 多代理工作流程图
```

## 🎯 核心特性

### 🔄 敏捷迭代开发
- 以迭代为单位的循环式开发
- 快速响应用户反馈
- 持续优化和改进

### 📊 实时进度监控
- $A_{dash}$ 提供实时项目状态
- 关键指标聚合和展示
- 支持多维度查询

### 🔧 智能版本管理
- $A_{vc}$ 自动版本控制
- 防止版本冲突
- 完整的历史记录

### 💬 多模式通信
- 直接Agent间通信
- 通过管理Agent的间接通信
- 结构化消息交换

## 🚀 优势特点

### 相比单代理系统的优势

1. **并行处理能力**: 多个Agent可以同时工作，提高开发效率
2. **专业化分工**: 每个Agent专注于特定领域，提高工作质量
3. **实时协作**: Agent间实时通信，快速解决问题和冲突
4. **持续监控**: 全程进度跟踪，及时发现和解决问题

### 敏捷开发支持

1. **快速迭代**: 支持短周期迭代开发
2. **用户反馈驱动**: 基于用户反馈的持续改进
3. **团队协作**: 多Agent协作模拟真实团队开发
4. **持续集成**: 自动化版本管理和集成

## 📋 使用指南

### 启动多代理工作流程

1. **需求输入**: 用户向系统提供自然语言需求
2. **自动分配**: 系统自动将需求分配给相关Agent
3. **并行执行**: 多个Agent并行工作，实时协调
4. **迭代交付**: 按迭代周期交付可用产品
5. **反馈收集**: 收集用户反馈，规划下一迭代

### 监控和管理

- 通过 $A_{dash}$ 查看项目进度
- 通过 $A_{vc}$ 管理版本历史
- 通过 $A_{fp}$ 分析反馈和规划迭代

## 🤖 CrewAI 实现指南

### 关于 CrewAI

CrewAI 是一个强大的多代理协作框架，专门用于构建和管理复杂的AI代理团队。本项目使用 CrewAI 来实现多代理协作开发工作流程。

### 安装和设置

#### 1. 安装 CrewAI

```bash
pip install crewai
```

#### 2. 从源码安装（开发版本）

```bash
git clone https://github.com/crewAIInc/crewAI.git
cd crewAI
pip install -e .
```

### 快速开始

#### 基本概念

- **Agent（代理）**: 具有特定角色和技能的AI实体
- **Task（任务）**: 需要完成的具体工作
- **Crew（团队）**: 多个代理组成的协作团队
- **Process（流程）**: 任务执行的顺序和方式

#### 创建代理示例

```python
from crewai import Agent, Task, Crew

# 创建需求分析代理
requirements_agent = Agent(
    role='Requirements Analyst',
    goal='分析和细化用户需求，创建优先级排序的需求列表',
    backstory='你是一位经验丰富的需求分析师，擅长将模糊的用户需求转化为清晰的功能规格。',
    verbose=True
)

# 创建系统设计代理
system_design_agent = Agent(
    role='System Architect',
    goal='设计系统架构和技术方案',
    backstory='你是一位资深的系统架构师，能够设计可扩展和可维护的系统架构。',
    verbose=True
)
```

#### 定义任务

```python
# 需求分析任务
requirements_task = Task(
    description='分析用户需求并生成结构化的需求文档',
    agent=requirements_agent
)

# 系统设计任务
design_task = Task(
    description='基于需求文档设计系统架构',
    agent=system_design_agent
)
```

#### 创建团队

```python
# 创建开发团队
dev_crew = Crew(
    agents=[requirements_agent, system_design_agent],
    tasks=[requirements_task, design_task],
    verbose=2
)

# 执行工作流程
result = dev_crew.kickoff()
```

### 高级功能

#### 1. 自定义工具集成

```python
from crewai_tools import SerperDevTool, WebsiteSearchTool

# 为代理添加工具
search_tool = SerperDevTool()
web_tool = WebsiteSearchTool()

agent_with_tools = Agent(
    role='Research Specialist',
    tools=[search_tool, web_tool],
    # ... 其他配置
)
```

#### 2. 内存和上下文管理

```python
crew = Crew(
    agents=[agent1, agent2],
    tasks=[task1, task2],
    memory=True,  # 启用团队记忆
    verbose=2
)
```

#### 3. 协作流程控制

```python
from crewai import Process

crew = Crew(
    agents=[agent1, agent2, agent3],
    tasks=[task1, task2, task3],
    process=Process.sequential,  # 或 Process.hierarchical
    verbose=2
)
```

### 项目集成

本项目的 `crewai_code/` 目录包含了完整的 CrewAI 实现代码，展示了如何将上述9个Agent集成到一个协作系统中。

### 学习资源

- **官方文档**: [https://docs.crewai.com/introduction](https://docs.crewai.com/introduction)
- **GitHub仓库**: [https://github.com/crewAIInc/crewAI](https://github.com/crewAIInc/crewAI)
- **示例项目**: [CrewAI Examples](https://github.com/crewAIInc/crewAI-examples)

## 🔗 相关资源

- [多代理工作流程图](workflow_pic/multi_agent_workflow.svg)
- [CrewAI实现代码](crewai_code/)
- [单代理工作流程对比](../workflow_single_agent/)
- [CrewAI官方文档](https://docs.crewai.com/introduction)
- [CrewAI GitHub仓库](https://github.com/crewAIInc/crewAI)

---

*本多代理协作系统通过专业化分工和智能协调，实现了高效的敏捷软件开发流程，为复杂项目提供了可扩展的解决方案。*