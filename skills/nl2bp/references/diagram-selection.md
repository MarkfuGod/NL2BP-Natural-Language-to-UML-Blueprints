# Choosing diagrams

Draw a diagram only when it answers a question a reader of the next stage will ask.
Prefer few, correct diagrams over many decorative ones. Syntax for each type:
[plantuml-syntax.md](plantuml-syntax.md).

## By stage

| Stage | Question the diagram answers | Draw | Optional |
|---|---|---|---|
| Requirements | Who uses the system and for what? Which rules matter? | Use case; activity for each rule-heavy flow | Mind map / WBS of scope; Chen ER for the domain vocabulary |
| Architecture | What are the parts, what runs where, what talks to what? | C4 Context + C4 Container | C4 Component for the riskiest container; deployment |
| Blueprint (design contract) | What exactly must the code contain? | Class diagram (all domain types and service interfaces); sequence for each core use case; IE ER schema if there is a database | State diagram for entities with a lifecycle; file structure; JSON payloads for key APIs; Salt wireframes for UI |
| Planning | What gets built when? | Gantt for the sprint | Chart (burndown) |
| Status / review | How far along are we? | Chart (burndown, tests passing) | — |

## Rules

1. **The class diagram is the contract.** Every domain type and service interface the
   implementation must contain is declared as `class`, `interface`, `enum` or
   `abstract class`. Tooling turns these names into the implementation checklist and
   later measures how many exist in the code. Use names that fit the implementation
   language (`LoanService`, not `LoanServiceImpl` for Python).
2. **One diagram per module** when there are several subsystems; never one giant diagram.
3. **Consistent names** across all diagrams and documents: the same entity is spelled the
   same way in use case, class, sequence and ER diagrams.
4. **C4 for architecture, UML for design.** Do not draw architecture as an ad-hoc component
   diagram when C4 Context/Container says it more clearly.
5. **Match the stack.** If the architecture chooses Python/FastAPI, do not use Spring idioms
   (`*Impl`, `@Controller`, `SecurityConfig`) in the blueprint.
6. **Every diagram gets 2–3 sentences of explanation** directly after it.

## Quick map: need → diagram

| Need | Diagram | Start keyword |
|---|---|---|
| actors and goals | use case | `@startuml` |
| process with decisions / parallel steps | activity | `@startuml` |
| message order, API calls | sequence | `@startuml` |
| types, attributes, relationships | class | `@startuml` |
| system landscape, containers | C4 | `@startuml` + `!include <C4/...>` |
| modules and interfaces | component | `@startuml` |
| servers, containers, networks | deployment | `@startuml` |
| lifecycle of one entity | state | `@startuml` |
| database tables | IE entity-relationship | `@startuml` |
| conceptual domain model | Chen ER | `@startchen` |
| signal or state over time | timing | `@startuml` |
| project layout | files | `@startfiles` |
| schedule | Gantt | `@startgantt` |
| numbers: burndown, rates | chart | `@startchart` |
| scope breakdown | mind map / WBS | `@startmindmap` / `@startwbs` |
| payload or config | JSON / YAML | `@startjson` / `@startyaml` |
| UI wireframe | Salt | `@startsalt` |
