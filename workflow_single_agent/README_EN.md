# Single-Agent Multi-Role Collaborative Development Workflow

## 📋 Overview

This directory contains a single-agent multi-role collaborative software development workflow system. The system enables a single AI agent to play different professional roles through role switching, completing the entire software development lifecycle from requirements analysis to code deployment.

## 🏗️ System Architecture

### Core Concepts
- **Single-Agent Multi-Role**: One AI agent plays different professional roles through role switching
- **Workflow-Driven**: Execute tasks in predefined workflow sequence
- **Document-Driven**: Each role's output serves as input for the next role
- **PlantUML Integration**: Specially optimized for generating and managing PlantUML diagrams

## 👥 Role System

This system includes the following 7 core roles:

| Role | English Name | Mode ID | Primary Responsibilities |
|------|--------------|---------|-------------------------|
| 📝 Requirements Analyst | Requirements Analyst | `01-req-gen` | Convert natural language to structured requirement documents |
| 🏗️ System Architect | System Architect | `systemdesign` | Design system architecture and technical solutions |
| 📊 Blueprint Designer | Blueprint Designer | `blueprintdesign` | Generate PlantUML diagrams and visual designs |
| 💻 Coder | Coder | `coder` | Implement specific code functionality |
| 🔍 Code Reviewer | Code Reviewer | `code-reviewer` | Review code quality and standards |
| 🚀 Deployer & Debugger | Deployer & Debugger | `debugger-deployer` | Deploy, debug, and test |
| 🛠️ Code Critic | Code Critic | `code-critic` | Diagnose problems and provide solutions |

## 📁 Directory Structure

```
workflow_single_agent/
├── README.md                          # This document (Chinese)
├── README_EN.md                       # This document (English)
├── agent_profile/                     # Agent configuration files
│   ├── BlueprintWriter_Profile.md     # Blueprint Designer role configuration
│   └── BlueprintWirter_Profile.drawio.svg  # Role relationship diagram
├── role_prompts/                      # Role prompt rules
│   ├── rules-01-req-gen/             # Requirements Analyst rules
│   ├── rules-blueprintdesign/        # Blueprint Designer rules
│   ├── rules-code-reviewer/          # Code Reviewer rules
│   ├── rules-coder/                  # Coder rules
│   ├── rules-debugger-deployer/      # Deployer & Debugger rules
│   └── rules-systemdesign/           # System Architect rules
└── workflow_pic/                     # Workflow diagrams and documentation
    ├── single_agent_workflow.drawio.svg  # Workflow diagram
    ├── workflow_EN.md                # English workflow documentation
    └── workflow_ZH.md                # Chinese workflow documentation
```

## 🔄 Workflow Process

### Standard Development Process

1. **Requirements Gathering** → 📝 Requirements Analyst
   - Receive user natural language requirements
   - Generate structured requirement documents
   - Output: Markdown-formatted requirement document

2. **Architecture Design** → 🏗️ System Architect
   - Design system architecture based on requirement document
   - Develop technical solutions and implementation strategies
   - Output: Architecture design document

3. **Blueprint Design** → 📊 Blueprint Designer
   - Convert requirements and architecture into visual diagrams
   - Generate PlantUML diagrams (use case, class, sequence diagrams, etc.)
   - Output: PlantUML files and diagram descriptions

4. **Code Implementation** → 💻 Coder
   - Implement code based on architecture design
   - Generate frontend interfaces and backend logic
   - Output: Complete code implementation

5. **Code Review** → 🔍 Code Reviewer
   - Review code quality and standards
   - Provide improvement suggestions
   - Output: Code review report

6. **Deployment & Testing** → 🚀 Deployer & Debugger
   - Execute project deployment
   - Perform debugging and testing
   - Output: Deployment report and test results

### Exception Handling Process

- **Problem Diagnosis** → 🛠️ Code Critic
  - Interact with users to solve technical problems
  - Provide problem solutions
  - Coordinate other roles to fix issues

## 🎯 Core Features

### 📊 PlantUML Diagram Generation
Supports multiple diagram types:
- **Use Case Diagrams**: Show user-system interactions
- **Class Diagrams**: Display core system entities and relationships
- **Activity Diagrams**: Describe business processes
- **Sequence Diagrams**: Show message interaction processes
- **Deployment Diagrams**: Display system deployment architecture
- **File Structure Diagrams**: Show project file organization

### 🔧 Intelligent Role Switching
- Automatically switch roles according to workflow
- Each role focuses on domain-specific tasks
- Information transfer between roles through documents

### 📝 Document-Driven Development
- Structured requirement documents
- Detailed architecture design documents
- Complete code review reports
- Comprehensive deployment test reports

## 🚀 Usage Guide

### Starting the Workflow

1. **Initialize Requirements Analysis**
   ```
   Switch to 01-req-gen mode
   Provide natural language requirement description
   ```

2. **Automatic Process Execution**
   - System automatically executes in workflow sequence
   - Automatically switches to next role after each role completes tasks
   - Users can provide feedback and modification requests at any stage

3. **Problem Handling**
   ```
   Switch to code-critic mode when encountering problems
   Describe specific issues to get solutions
   ```

### Configuration File Description

#### Role Configuration Files (`agent_profile/`)
- Define core identity and capabilities of each role
- Specify available tools and operational rules
- Set input/output format requirements

#### Role Prompt Rules (`role_prompts/`)
- Detailed role behavior guidance
- Specific task execution rules
- Collaboration methods with other roles

## 📋 Best Practices

### Requirement Description
- Use clear, specific natural language
- Include functional and non-functional requirements
- Clearly define user roles and usage scenarios

### Diagram Design
- Choose appropriate diagram types based on project stage
- Maintain naming consistency
- Add necessary comments and explanations

### Code Implementation
- Follow architecture design guidance
- Focus on code quality and maintainability
- Respond promptly to review feedback

## 🔗 Related Resources

- [Detailed Workflow Documentation](workflow_pic/workflow_EN.md)
- [Blueprint Designer Configuration](agent_profile/BlueprintWriter_Profile.md)
- [PlantUML Format Examples](role_prompts/rules-blueprintdesign/02-formatting-examples.md)
- [Generation Examples](../generation_examples_uml_zh/)

## 📞 Support & Feedback

If you encounter problems or have improvement suggestions during use, please:
1. Consult relevant role prompt rule documents
2. Use Code Critic role for technical support
3. Refer to workflow documentation

---

*This workflow system is designed for efficient software development and PlantUML diagram generation. Through role specialization and process standardization, it ensures development quality and efficiency.*