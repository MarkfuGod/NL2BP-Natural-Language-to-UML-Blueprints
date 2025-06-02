# AgileWorkflow - Agile LLM Multi-Agent Development Workflow

## Project Overview

AgileWorkflow is an agile development workflow system built on the CrewAI framework, utilizing multiple specialized AI Agents to collaborate and complete the entire software development lifecycle management. This system simulates a real agile development team, providing a complete automated development process from requirements analysis to system design, from frontend and backend implementation to project management.

## Core Features

- **Multi-Agent Collaboration**: 10 specialized Agents working together, simulating a real agile team
- **Complete Workflow**: Covers the entire process including requirements analysis, system design, blueprint design, frontend/backend implementation, and project management
- **Automated Documentation**: Automatically generates system design documents, requirements analysis reports, implementation plans, etc.
- **Agile Management**: Built-in Sprint planning, progress tracking, feedback collection, and other agile management functions
- **Visualization Support**: Supports workflow visualization and project status dashboards

## System Architecture

### Agent Role Distribution

#### Core Development Agents
- **System Architecture Design Expert** (`system_design_agent`): Responsible for system architecture design and technology selection
- **Requirements Analysis Expert** (`requirement_analysis_agent`): Analyzes user requirements, creates user stories and acceptance criteria
- **System Blueprint Design Expert** (`blueprint_design_agent`): Creates system blueprints and PlantUML diagrams
- **Frontend Design Implementation Expert** (`frontend_design_agent`): Implements user interfaces and frontend logic
- **Backend Design Implementation Expert** (`backend_design_agent`): Implements backend services and APIs

#### Management System Agents
- **Version Control Management Expert** (`version_control_agent`): Manages version history and change records
- **Agile Dashboard Management Expert** (`agile_dashboard_agent`): Tracks project progress and status
- **Feedback Planning Expert** (`feedback_planning_agent`): Collects feedback and plans next iteration

#### Compatibility Agents
- **Development Implementation Expert** (`developer_agent`): General development tasks
- **Testing Verification Expert** (`testing_agent`): Test case design and quality assurance

### Workflow Phases

1. **Project Initialization**: Collect basic project information and Sprint configuration
2. **Iteration Startup Phase**: System Architecture Design → Requirements Analysis
3. **Blueprint Design Phase**: Create system blueprints and interface specifications
4. **Implementation Phase**: Frontend Design Implementation → Backend Design Implementation
5. **Management System Phase**: Version Control → Agile Dashboard → Feedback Planning
6. **Summary Phase**: Generate system design summary document

## Installation and Usage

### Environment Requirements

- Python 3.10-3.12
- CrewAI >= 0.118.0

### Installation Steps

1. Clone the project locally
```bash
git clone <repository-url>
cd crewai_code
```

2. Install dependencies
```bash
pip install -e .
```

### Usage Methods

#### Start Agile Development Workflow
```bash
crewai flow kickoff
```

#### Generate Workflow Visualization
```bash
crewai flow plot
```

### Interactive Process

1. After starting the program, the system will prompt for input:
   - Project name
   - Project description
   - Sprint duration (recommended 7-30 days)

2. The system will automatically execute the following phases:
   - Iteration Startup Phase (System Design + Requirements Analysis)
   - Blueprint Design Phase
   - Implementation Phase (Frontend + Backend)
   - Management System Phase (Version Control + Dashboard + Feedback Planning)
   - Summary Phase

3. All generated documents will be saved in the `output/` directory

## Output Files

After the workflow completes, the following documents will be generated in the `output/` directory:

- `system_design_summary.md` - System design summary document
- `system_design.md` - System architecture design plan
- `requirement_analysis.md` - Requirements analysis document
- `blueprint_design.md` - System blueprint document
- `frontend_design.md` - Frontend implementation report
- `backend_design.md` - Backend implementation report
- `version_control.md` - Version control report
- `agile_dashboard.md` - Project status report
- `feedback_planning.md` - Feedback analysis and iteration planning report

## Project Structure

```
agileworkflow/
├── __init__.py
├── main.py                 # Main entry file
├── agile_flow.py          # Core workflow definition
├── crews/
│   └── agile_crew/
│       ├── __init__.py
│       ├── agile_crew.py  # Agent team definition
│       ├── config/
│       │   ├── agents.yaml # Agent configuration
│       │   └── tasks.yaml  # Task configuration
│       └── prompts/        # Agent prompts
└── tools/                  # Custom tools
    ├── __init__.py
    ├── custom_tool.py
    └── file_writer_tool.py
```

## Configuration Instructions

### Agent Configuration (agents.yaml)
Defines each Agent's role, goals, and backstory. You can adjust the Agent's professional domain and work focus as needed.

### Task Configuration (tasks.yaml)
Defines specific task descriptions, expected outputs, and responsible Agents for each phase. You can customize task processes and output requirements.

## Extension Development

### Adding New Agents
1. Define new Agent in `config/agents.yaml`
2. Add corresponding tasks in `config/tasks.yaml`
3. Integrate new workflow steps in `agile_flow.py`

### Custom Tools
Create new tool classes in the `tools/` directory, inheriting from CrewAI's BaseTool class.

### Modifying Workflow
Edit the `AgileWorkflowFlow` class in `agile_flow.py` to add new workflow steps or modify existing processes.

## License

This project uses an open source license. Please see the LICENSE file for specific license information.

## Contribution Guidelines

We welcome Issues and Pull Requests to improve the project. 

## Contact Information

If you have questions or suggestions, please contact us through:

- Submit GitHub Issues
- Send email to project maintainers

---