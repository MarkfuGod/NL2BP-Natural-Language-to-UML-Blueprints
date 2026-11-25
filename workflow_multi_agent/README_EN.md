# Multi-Agent Collaborative Development Workflow

> **2026 implementation (read this first)**
>
> The sections from "System Architecture" to "Usage Guide" below are the original 2025 design:
> nine agents modelled on an agile team. The current implementation in
> [`crewai_code/`](crewai_code/) was trimmed on the evidence:
>
> - **5 agents**: requirements → architecture (C4) → blueprint → frontend ∥ backend.
> - **Version control, dashboard and feedback planning are no longer agents**; code produces them.
>   The run directory is a real git repo with one commit per stage; `project_status.md` combines
>   the real history with measured quality signals; the human collaborator ($H$) reviews the
>   blueprint with `--review`. Reason: those three agents had no real signals and could only
>   restate or invent status, while every measured gain came from deterministic checks
>   ([evals/RESULTS.md](crewai_code/evals/RESULTS.md)).
> - **Quality gates**: PlantUML syntax check and repair, blueprint conformance, generated tests run
>   in Docker.
> - Diagram selection, output contract and PlantUML syntax live in
>   [`skills/nl2bp/references/`](../skills/nl2bp/references/).

## 📋 Overview

This directory contains a multi-agent collaborative agile software development workflow system. The system achieves a complete development lifecycle from user requirements to product delivery through message exchange and collaboration between multiple specialized agents, building a continuous evolution agile development loop.

## 🏗️ System Architecture

### Core Concepts
- **Multi-Agent Collaboration**: Multiple specialized agents work in parallel, coordinating tasks through message exchange
- **Agile Iteration**: Iterative cyclic development process
- **User Feedback Driven**: Continuous optimization loop based on user feedback
- **Real-time Monitoring**: Full-process progress tracking and status management

### Agent Set Definition

The agent set $\mathcal{A}$ in the system is defined as:

$$\mathcal{A}=\{A_{sd},A_{ra},A_{bd},A_{fe},A_{be},A_{vc},A_{dash},A_{fp},H\}$$

Where:
- $A_{sd}$: System Design Agent (System Architecture Design)
- $A_{ra}$: Requirement Analysis Agent (Requirements Analysis)
- $A_{bd}$: Blueprint Design Agent (Blueprint Design)
- $A_{fe}$: Frontend Design Agent (Frontend Implementation)
- $A_{be}$: Backend Design Agent (Backend Implementation)
- $A_{vc}$: Version Control Agent (Version Control)
- $A_{dash}$: Agile Dashboard Agent (Progress Tracking)
- $A_{fp}$: Feedback Planning Agent (Feedback Planning)
- $H$: Human Collaborator (Human User/Product Owner)

## 👥 Agent Classification and Responsibilities

### 🔧 Core Development Agents

| Agent | Chinese Name | Primary Responsibilities |
|-------|--------------|-------------------------|
| $A_{sd}$ | System Architecture Design Agent | Responsible for system architecture design and technology selection, converting user requirements into technical architecture solutions, defining system components and their relationships |
| $A_{ra}$ | Requirements Analysis Agent | Analyze and refine user requirements, create prioritized requirement lists, write user stories and acceptance criteria |
| $A_{bd}$ | Blueprint Design Agent | Create system blueprints and interface specifications, generate PlantUML diagrams describing system structure, define interfaces and data flow between components |
| $A_{fe}$ | Frontend Design Agent | Implement user interfaces and frontend logic, create UI components based on blueprints, implement API calls to backend |
| $A_{be}$ | Backend Design Agent | Implement backend services and APIs, design data models and business logic, create deployable backend code |

### 🛠️ Management System Agents

| Agent | Chinese Name | Primary Responsibilities |
|-------|--------------|-------------------------|
| $A_{vc}$ | Version Control Agent | Maintain version control of all development artifacts (code, documents), assign version numbers and record commit history, prevent version conflicts |
| $A_{dash}$ | Agile Dashboard Agent | Track development progress, aggregate development status and key metrics, support other agents or users in querying project status |
| $A_{fp}$ | Feedback Planning Agent | Lead user feedback collection and analysis, formulate iteration plans, organize team retrospective meetings, implement continuous optimization loop |

## 🔄 Detailed Workflow Process

### Iterative Development Process

The entire multi-agent system follows an iterative cyclic development process, consisting of five stages:

#### 1. Iteration Initiation Stage
- **Trigger Condition**: User provides natural language requirements
- **Participating Agents**: $A_{sd}$, $A_{ra}$
- **Work Content**:
  - $A_{sd}$ creates system architecture solutions
  - $A_{ra}$ decomposes requirements into functional points and prioritizes them
  - Both agents collaborate through direct message exchange to ensure technical design meets business requirements

#### 2. Blueprint Design Stage
- **Participating Agents**: $A_{ra}$, $A_{bd}$, $A_{vc}$
- **Work Content**:
  - $A_{ra}$ passes requirement priority list to $A_{bd}$
  - $A_{bd}$ generates blueprint files based on existing system design
  - $A_{vc}$ manages blueprint versions for subsequent calls

#### 3. Implementation Stage
- **Participating Agents**: $A_{fe}$, $A_{be}$, $A_{vc}$, $A_{dash}$
- **Work Content**:
  - $A_{fe}$ and $A_{be}$ work in parallel to implement system functionality
  - Both agents obtain latest blueprints from $A_{vc}$
  - Implement frontend and backend code respectively according to interface specifications
  - Regularly report progress and obstacles to $A_{dash}$
  - Coordinate API implementation and call details through direct message exchange

#### 4. Demo and Feedback Stage
- **Participating Agents**: $A_{fp}$, $H$
- **Work Content**:
  - After current version development is complete, system integrates and generates demo version
  - Present current iteration results to users
  - $A_{fp}$ analyzes user feedback and determines priorities

#### 5. Review and Planning Stage
- **Participating Agents**: $A_{fp}$, $A_{ra}$
- **Work Content**:
  - $A_{fp}$ organizes retrospective meetings, analyzes successes and shortcomings
  - Plan next iteration based on user feedback and retrospective results
  - Pass planning results back to $A_{ra}$ to start new iteration

## 📡 Inter-Agent Communication Mechanisms

### Direct Communication Mode

#### Task Assignment and Execution
- **Pattern**: One agent creates task description and assigns it to another agent
- **Process**: Receiving agent executes task and returns results
- **Example**: $A_{sd}$ creates architecture and passes it as task context to $A_{ra}$

#### Collaborative Discussion
- **Pattern**: Agents exchange information and viewpoints through structured messages
- **Purpose**: Resolve conflicts or clarify requirements
- **Example**: $A_{fe}$ and $A_{be}$ discuss API interface details

### Indirect Communication Through Management System Agents

#### Communication Through Version Control Agent
- $A_{bd}$ submits blueprints to $A_{vc}$
- $A_{vc}$ assigns version numbers to blueprints and stores them
- $A_{fe}$ and $A_{be}$ obtain latest blueprints from $A_{vc}$

#### Communication Through Agile Dashboard Agent
- All development agents report progress to $A_{dash}$
- $A_{dash}$ aggregates information and generates status reports
- Other agents can query $A_{dash}$ to get project status

#### Communication Through Feedback Planning Agent
- User feedback is passed to $A_{fp}$
- $A_{fp}$ analyzes feedback and creates iteration plans
- Plans are passed back to $A_{ra}$ to start new iteration

## 📁 Directory Structure

```
workflow_multi_agent/
├── README.md                          # This document (Chinese)
├── README_EN.md                       # This document (English)
├── crewai_code/                       # CrewAI implementation code
└── workflow_pic/                      # Workflow diagrams
    └── multi_agent_workflow.svg       # Multi-agent workflow diagram
```

## 🎯 Core Features

### 🔄 Agile Iterative Development
- Iterative cyclic development
- Rapid response to user feedback
- Continuous optimization and improvement

### 📊 Real-time Progress Monitoring
- $A_{dash}$ provides real-time project status
- Key metrics aggregation and display
- Multi-dimensional query support

### 🔧 Intelligent Version Management
- $A_{vc}$ automatic version control
- Prevent version conflicts
- Complete historical records

### 💬 Multi-mode Communication
- Direct inter-agent communication
- Indirect communication through management agents
- Structured message exchange

## 🚀 Advantages

### Advantages Over Single-Agent Systems

1. **Parallel Processing Capability**: Multiple agents can work simultaneously, improving development efficiency
2. **Professional Specialization**: Each agent focuses on specific domains, improving work quality
3. **Real-time Collaboration**: Real-time communication between agents, quick problem and conflict resolution
4. **Continuous Monitoring**: Full-process progress tracking, timely problem detection and resolution

### Agile Development Support

1. **Rapid Iteration**: Support for short-cycle iterative development
2. **User Feedback Driven**: Continuous improvement based on user feedback
3. **Team Collaboration**: Multi-agent collaboration simulates real team development
4. **Continuous Integration**: Automated version management and integration

## 📋 Usage Guide

### Starting Multi-Agent Workflow

1. **Requirements Input**: User provides natural language requirements to the system
2. **Automatic Assignment**: System automatically assigns requirements to relevant agents
3. **Parallel Execution**: Multiple agents work in parallel with real-time coordination
4. **Iterative Delivery**: Deliver usable products by iteration cycles
5. **Feedback Collection**: Collect user feedback and plan next iteration

### Monitoring and Management

- View project progress through $A_{dash}$
- Manage version history through $A_{vc}$
- Analyze feedback and plan iterations through $A_{fp}$

## 🤖 CrewAI implementation

How to run it, the stage graph, quality gates and output layout:
[crewai_code/README_EN.md](crewai_code/README_EN.md).

```bash
cd workflow_multi_agent/crewai_code
uv sync && cp .env.example .env     # set MODEL and the API key
uv run nl2bp multi --name RoomBooking --description-file evals/requirements/room-booking.md --language English --review
```

## 🔗 Related Resources

- [Multi-Agent Workflow Diagram](workflow_pic/multi_agent_workflow.svg)
- [CrewAI Implementation Code](crewai_code/)
- [Single-Agent Workflow Comparison](../workflow_single_agent/)
- [CrewAI Official Documentation](https://docs.crewai.com/introduction)
- [CrewAI GitHub Repository](https://github.com/crewAIInc/crewAI)

---

*This multi-agent collaborative system achieves efficient agile software development processes through professional specialization and intelligent coordination, providing scalable solutions for complex projects.*