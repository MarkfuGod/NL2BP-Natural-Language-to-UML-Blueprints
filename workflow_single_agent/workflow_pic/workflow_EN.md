# Multi-Role Collaborative Development Workflow

## 📋 Role Overview

This system includes the following 7 core roles:

| Role | Chinese Name | Primary Responsibilities |
|------|--------------|-------------------------|
| 👤 User | 用户 | Provide requirements, interact with system |
| 📝 Requirements Analyst | 需求分析师 | Convert natural language to requirement documents |
| 🏗️ System Architect | 架构设计师 | Design system architecture |
| 📊 Blueprint Designer | 蓝图设计师 | Generate PlantUML diagrams |
| 💻 Coder | 编码工程师 | Implement code |
| 🔍 Code Reviewer | 代码审查员 | Review code quality |
| 🚀 Deployer & Debugger | 部署调试员 | Deploy and debug |
| 🛠️ Code Critic | 代码诊断师 | Diagnose issues, provide solutions |

---

## 🔄 Detailed Role Responsibilities

### 👤 A. User

**Description**: Interact with the system through natural language instructions to obtain complete software development services

**Main Functions**:
1. 📝 Provide natural language requirement descriptions
2. 🛠️ Interact with Code Critic to resolve issues
3. 📋 Confirm requirement documents with Requirements Analyst
4. 💻 Communicate code implementation with Coder
5. 🏗️ Discuss system design with System Architect
6. 📊 Confirm diagram designs with Blueprint Designer

---

### 📝 B. Requirements Analyst

**Description**: Responsible for converting user's natural language instructions into structured requirement documents

**Main Functions**:
1. 🔄 Convert user natural language to requirement points
2. 📄 Generate Markdown format requirement documents
3. 📊 Collaborate with Blueprint Designer
4. 🏗️ Collaborate with System Architect

**Interaction Scenarios**:
- **With Blueprint Designer**: Provide requirement documents, support modification requests
- **With System Architect**: Deliver requirement documents

---

### 🏗️ C. System Architect

**Description**: Convert requirement documents into implementable system architecture designs

**Main Functions**:
1. 🎯 Generate system architecture based on requirement documents
2. ✅ Evaluate design rationality and feasibility
3. 📄 Generate Markdown format design documents
4. 📊 Collaborate with Blueprint Designer
5. 💻 Collaborate with Coder

**Interaction Scenarios**:
- **With Blueprint Designer**: Provide architecture design documents
- **With Coder**: Provide architecture design and requirement documents

---

### 📊 D. Blueprint Designer

**Description**: Convert requirement documents and architecture designs into visual PlantUML diagrams

**Main Functions**:
1. 🔍 Analyze requirement documents and design document key points
2. 📈 Generate corresponding PlantUML images for different project phases
3. 👤 Interact with users to confirm diagrams

**Supported Diagram Types**:
- 📋 **Use Case Diagram**: Show user-system interactions
- 🏗️ **Class Diagram**: Display system core entities and relationships
- 🔄 **Activity Diagram**: Describe business processes
- ⏱️ **Sequence Diagram**: Show message interaction processes
- 🚀 **Deployment Diagram**: Display system deployment architecture

**Example Scenarios**:

#### Scenario 1: User Permission Management System
```
Input Requirements:
1. Users can register, login, view personal profiles
2. Administrators can manage user data and audit content
3. Users and administrators have different permissions
4. All user operations need to be logged

Output Diagrams:
- Use Case Diagram: Show operation permission boundaries between users and administrators
- Class Diagram: User, Admin, Log and other core entities and their relationships
- Activity Diagram: Describe user registration and login processes
- Sequence Diagram: User login process message interaction
```

#### Scenario 2: Online Shopping System
```
Project Name: Online Shopping System
Project Phase: Requirements Analysis
Requirements Description: Users can browse products, add products to cart, place orders and make payments
Output: Use case diagram with brief explanation
```

#### Scenario 3: Library Management System
```
Project Name: Library Management System
Project Phase: System Design
System Architecture: Frontend-backend separation
Requirements Description: System should support adding, deleting, modifying and querying books, users can borrow and return books
Output: Class diagram with brief explanation
```

---

### 💻 E. Coder

**Description**: Implement specific code functionality based on architecture design

**Main Functions**:
1. 🎨 Generate frontend interfaces (UI dimensions, component sizes, color schemes)
2. ⚙️ Implement backend code logic
3. 📝 Interact with Requirements Analyst
4. 🏗️ Interact with System Architect
5. 🔍 Interact with Code Reviewer

**Exception Handling**:
- **Requirement Issues**: When encountering unreasonable requirements or implementation impossibility, return modification requests
- **Architecture Issues**: When encountering unreasonable architecture, implementation impossibility, or deployment impossibility, return modification requests
- **Review Feedback**: Modify based on code review results

---

### 🔍 F. Code Reviewer

**Description**: Conduct quality reviews on code implementations to ensure code meets standards

**Main Functions**:
1. ✅ Review code based on requirement documents and architecture design
2. 📋 Provide detailed code review opinions
3. 💻 Interact with Coder
4. 🚀 Interact with Deployer & Debugger

**Review Process**:
- **Issues Found**: Provide code review opinions, request modifications
- **Review Passed**: Confirm code quality, deliver for deployment

---

### 🚀 G. Deployer & Debugger

**Description**: Responsible for project deployment, debugging and testing work

**Main Functions**:
1. 🚀 Execute project deployment
2. 🐛 Perform debugging and troubleshooting
3. 🧪 Execute project testing
4. 📊 Generate detailed deployment, debugging, testing reports
5. 👤 Interact with users to provide feedback

**Result Handling**:
- **Deployment Success**: Deliver to user with detailed reports
- **Deployment Failure**: Deliver to user, specify implementation ideas, error content, error location, error fields, error categories

---

### 🛠️ H. Code Critic

**Description**: Interact with users to provide problem diagnosis and solutions

**Main Functions**:
1. ❓ Answer user technical questions
2. 💡 Provide problem solutions
3. ✅ Wait for user confirmation of solutions
4. 🔄 Return confirmed solutions to Deployer & Debugger
5. 👤 Interact with users
6. 🚀 Interact with Deployer & Debugger

---

## 🔗 Detailed Interaction Flows

### 👤 User Interaction Scenarios

#### A.2 Interaction with Code Critic
1. ❓ Inquire about reasons for error content
2. 🔍 Ask if suspected errors are actual errors
3. 💡 Ask how to resolve specific errors

#### A.3 Interaction with Requirements Analyst
1. ✅ Confirm if requirement documents are reasonable and meet actual needs

#### A.4 Interaction with Coder
1. 🔧 Directly request code error modifications

#### A.5 Interaction with System Architect
1. ✅ Confirm if architecture design is reasonable and meets actual needs

#### A.6 Interaction with Blueprint Designer
1. ✅ Confirm if blueprints are reasonable and meet actual needs

### 🔄 Inter-Role Collaboration Flows

#### 📝 Requirements Analyst → 📊 Blueprint Designer (B.3)
- Input requirement documents, handle modification requests

#### 📝 Requirements Analyst → 🏗️ System Architect (B.4)
- Provide requirement documents

#### 🏗️ System Architect → 📊 Blueprint Designer (C.4)
- Provide architecture design documents

#### 🏗️ System Architect → 💻 Coder (C.5)
- Provide architecture design and requirement documents

#### 📊 Blueprint Designer → 👤 User (D.3)
- Provide blueprints for user review

#### 💻 Coder Exception Handling (E.3, E.4)
- **E.3**: When encountering unreasonable requirements or implementation impossibility, return modification requests
- **E.4**: When encountering unreasonable architecture, implementation impossibility, or deployment impossibility, return modification requests

#### 💻 Coder → 🔍 Code Reviewer (E.5)
- Submit frontend and backend code for review, modify based on review results

#### 🔍 Code Reviewer Feedback (F.3, F.4)
- **F.3**: When issues found, provide review opinions requesting modifications
- **F.4**: When review passed, confirm delivery for deployment

#### 🚀 Deployer & Debugger → 👤 User (G.4)
- **Deployment Success**: Deliver detailed deployment, debugging, testing reports
- **Deployment Failure**: Provide error analysis reports

#### 🛠️ Code Critic Interactions (H.4, H.5)
- **H.4**: Return problem answers
- **H.5**: When deployment issues found, return solutions
