# AgileWorkflow：NL2BP 的 CrewAI 实现

[English](README_EN.md)

把一段自然语言需求，经由多 Agent（或单 Agent 多角色）协作，变成架构文档、PlantUML UML 蓝图和可运行的前后端代码。基于 **CrewAI 1.x**（已在 1.15 上测试）。

## 快速开始

```bash
cd workflow_multi_agent/crewai_code
uv sync                       # Python 3.10–3.13；uv 会自动下载合适的 Python
cp .env.example .env          # 填 MODEL 和对应厂商的 API key

# 多 Agent 敏捷工作流
uv run nl2bp multi --name 图书馆系统 \
  --description "学生可以检索、借阅、归还图书；管理员管理图书与逾期罚款。" \
  --sprint-days 14

# 单 Agent 多角色工作流（使用 workflow_single_agent/role_prompts 中的角色提示词）
uv run nl2bp single --name 图书馆系统 --description-file requirements.md

# 把生成的 .puml 渲染成 SVG（需本机 plantuml：brew install plantuml）
uv run nl2bp render output/<run>/diagrams
```

不带参数运行 `uv run kickoff` 或 `crewai flow kickoff` 会进入交互式输入。

### 模型配置

`MODEL` 采用 `<厂商>/<模型>` 格式。CrewAI 1.x 原生支持 openai、anthropic、gemini、deepseek、ollama、openrouter、azure、bedrock：

| MODEL 示例 | 需要的环境变量 |
|---|---|
| `anthropic/claude-sonnet-5-5` | `ANTHROPIC_API_KEY` |
| `openai/gpt-5.1` | `OPENAI_API_KEY` |
| `deepseek/deepseek-chat` | `DEEPSEEK_API_KEY` |
| `ollama/qwen3:14b` | 本地 Ollama，无需 key |

其他厂商：`uv sync --extra litellm` 后用 LiteLLM 的模型字符串。CrewAI 的匿名遥测与 tracing 默认关闭（`CREWAI_DISABLE_TELEMETRY` 等可覆盖）。

## 多 Agent 工作流

```
prepare
  └─ system_design                       系统架构设计 Agent
       └─ requirement_analysis           需求分析 Agent
            ├─ sprint_planning           敏捷看板 Agent（并行）
            └─ blueprint_design          蓝图设计 Agent（--review：人类协作者评审，可多轮）
                 ├─ frontend_design      前端 Agent ─┐ 并行，write_file 写代码
                 └─ backend_design       后端 Agent ─┤
                                                     ├─ version_control     版本控制 Agent
                                                     └─ agile_dashboard     敏捷看板 Agent
                                                          └─ feedback_planning  反馈规划 Agent
                                                               └─ system_design_summary  蓝图设计 Agent
```

- 每个阶段只运行一次，是一个“单 Agent + 单任务”的 Crew；只把它需要的上游文档传给它。
- `--review` 打开人类协作者环节：蓝图生成后暂停，输入修改意见即重新生成，直接回车接受（最多 3 轮）。
- 文档以 Agent 的最终答案返回，由工作流统一落盘，并自动抽取其中所有 `@startuml … @enduml`（以及 `@startfiles` 等）为 `.puml` 文件。

## 单 Agent 多角色工作流

一个 Agent 依次切换角色，每个角色只依据上一角色留下的文档工作：

```
01-req-gen → systemdesign → blueprintdesign → coder → code-reviewer
    ↺ 审查不通过：code-critic 诊断 → coder 修复 → code-reviewer 复审（--max-fix-rounds，默认 1）
→ debugger-deployer
```

角色规则直接读取 `workflow_single_agent/role_prompts/rules-<slug>/*.md`（可用 `NL2BP_ROLE_PROMPTS` 指向其他目录）。同一套提示词也可以作为 Roo Code 自定义模式使用，见 [workflow_single_agent](../../workflow_single_agent/)。

## 输出

每次运行生成独立目录 `output/<时间>_<项目名>/`：

```
docs/<stage>.md        每个阶段的文档
diagrams/*.puml        从文档中抽取的 PlantUML 图
frontend/ backend/     多 Agent：前后端代码（write_file 工具写入）
code/                  单 Agent：代码与部署文件
manifest.json          输入、模型、阶段耗时、token 用量、评审结论
```

`write_file` / `read_file` / `list_files` 工具只能访问本次运行目录，越界路径（`../`、符号链接）会被拒绝。

## 项目结构

```
agileworkflow/
├── main.py                    CLI：nl2bp multi | single | render | plot
├── agile_flow.py              多 Agent Flow（阶段图、并行、人类评审）
├── settings.py                模型与输出配置、.env 读取
├── templating.py              单次占位符渲染（不触发 CrewAI 对花括号的插值）
├── workspace.py               运行目录与路径约束
├── plantuml.py                抽取 / 本地或服务器渲染 PlantUML
├── crews/agile_crew/
│   ├── agile_crew.py          按阶段构建 Agent + Task 并运行
│   ├── config/agents.yaml     8 个 Agent 的角色设定
│   ├── config/tasks.yaml      10 个阶段的任务描述
│   └── prompts/blueprint_guide.md   蓝图写作规范
├── single_agent/              单 Agent 多角色运行器
└── tools/                     受限于运行目录的文件工具
tests/                         离线测试（假 LLM 驱动真实 CrewAI 对象）
```

## 开发

```bash
uv sync --group dev
uv run pytest -q
uv run ruff check . && uv run ruff format --check .
uv run nl2bp plot             # 导出 Flow 结构图 agile_workflow_flow.html
```

扩展：在 `agents.yaml` / `tasks.yaml` 中新增条目，然后在 `agile_flow.py` 中加一个 `@listen(...)` 方法调用 `self._stage("<stage>")`。`tests/test_core.py::test_config_is_consistent` 会检查配置引用是否一致。

## 从 0.1 迁移

- CrewAI `>=0.118,<1` → `>=1.15,<2`，Python 上限放宽到 3.13，改用 uv。
- 旧版每个阶段都调用整个 Crew（10+ 个任务全跑一遍，共 8 次），现在每阶段只跑自己的任务一次，前后端并行。
- 不再依赖 Agent 主动调用文件工具保存文档；未使用的 `developer_agent` / `testing_agent` 与重复的提示词文件已移除。
- 输出从 `output/*.md` + `Project/` 改为每次运行独立的 `output/<run>/`。
