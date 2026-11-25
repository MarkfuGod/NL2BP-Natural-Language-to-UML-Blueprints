# PlantUML syntax reference (PlantUML 1.2026.x)

Every block in this file is parsed by `plantuml -syntax` and rendered in CI
(`scripts/nl2bp_check.py validate references/plantuml-syntax.md`). Copy the shape,
not the content. Read only the sections for the diagrams you are drawing.

## Current rules (what changed since 2024–2025 tutorials)

- **Styling:** `skinparam` is deprecated. Use a `<style>` block or `!theme <name>`.
  Never mix the two in one diagram.
- **Sequence diagrams:** the default engine is Teoz (since 1.2026.7), so
  `!pragma teoz true` is no longer needed. The old `/` merge syntax is deprecated:
  write each message on its own line.
- **Activity diagrams:** use the current syntax (`start`, `:action;`, `if/elseif/else`,
  `fork`, `repeat`, swimlanes `|Lane|`). The legacy `(*) --> "x"` syntax is deprecated.
  Stereotypes go at the **end** of the line: `:Pay fine; <<output>>`.
- **Dedicated start keywords:** non-UML diagrams have their own pair
  (`@startjson`, `@startchart`, `@startgantt`, `@startmindmap`, `@startwbs`,
  `@startsalt`, `@startchen`, `@startfiles`, …). Since 1.2026.3, putting DOT, ditaa or
  network diagrams under `@startuml` is an error.
- **Preprocessor:** variables are written with `$` (`!$api = "REST"`); 1.2026.10 treats
  `$foo` and `foo` as the same variable and warns when `$` is missing.
- **C4:** the C4-PlantUML library ships inside PlantUML (v2.14.0 in 1.2026.10):
  `!include <C4/C4_Container>`. No network access needed.
- **Layout:** without Graphviz, PlantUML falls back to the built-in Smetana engine
  (1.2026.7). Force it with `!pragma layout smetana` for reproducible output.
- **Names:** put a snake_case name after every `@startX`; tooling uses it as the file name.

---

## Use case diagram: who can do what

Use in requirement analysis: actors, use cases, system boundary, `<<include>>` / `<<extend>>`.

```plantuml
@startuml library_usecase_borrowing
left to right direction
actor Student as s
actor Librarian as l
rectangle "Library System" {
  usecase "Search books" as UC1
  usecase "Borrow book" as UC2
  usecase "Return book" as UC3
  usecase "Pay overdue fine" as UC4
  usecase "Manage catalogue" as UC5
}
s --> UC1
s --> UC2
s --> UC3
UC3 <.. UC4 : <<extend>>
l --> UC5
@enduml
```

## Activity diagram: workflow with business rules

Use for processes with decisions, parallel steps and responsibilities (swimlanes).

```plantuml
@startuml library_activity_borrow
|Student|
start
:Request loan;
|System|
if (Unpaid fines?) then (yes)
  :Reject request; <<output>>
  stop
elseif (5 books already on loan?) then (yes)
  :Reject: loan limit reached;
  stop
else (no)
  fork
    :Decrease stock;
  fork again
    :Create loan (due in 30 days);
  end fork
endif
|Student|
:Receive confirmation;
stop
@enduml
```

## Sequence diagram: interactions over time

Use for API flows and message order. `++` / `--` activate and deactivate, `return`
answers the last call, `alt` / `opt` / `loop` / `group` frame alternatives.

```plantuml
@startuml library_sequence_borrow
autonumber
actor Student
participant "Web App" as Web
participant "Loan API" as API
database DB

Student -> Web : choose book
Web -> API ++ : POST /loans {isbn}
API -> DB ++ : load student, fines, active loans
return rows
alt can borrow
  API -> DB : insert loan, decrement stock
  API --> Web : 201 Created {dueDate}
else limit reached or unpaid fine
  API --> Web : 409 Conflict {reason}
end
deactivate API
Web --> Student : show result
@enduml
```

## Class diagram: domain model and services

Use in system design. Declare every type the code must implement; tooling extracts
`class`, `interface`, `enum`, `abstract class`, `record`, `struct`, `entity` names as the
implementation checklist. Show multiplicities on associations.

```plantuml
@startuml library_class_domain
package domain {
  class Student {
    +id: str
    +name: str
    +can_borrow(): bool
  }
  class Book {
    +isbn: str
    +title: str
    +stock: int
  }
  class Loan {
    +borrowed_at: date
    +due_at: date
    +returned_at: date?
    +overdue_days(today: date): int
  }
  enum LoanStatus {
    ACTIVE
    RETURNED
    OVERDUE
  }
}
package services {
  interface LoanService {
    +borrow(student_id: str, isbn: str): Loan
    +return_book(loan_id: str): Fine?
  }
  class FinePolicy {
    +DAILY_RATE: Decimal = 0.5
    +fine_for(loan: Loan, today: date): Decimal
  }
}
Student "1" -- "0..5" Loan : holds >
Book "1" -- "*" Loan
Loan --> LoanStatus
LoanService ..> FinePolicy : uses
@enduml
```

## Component diagram: modules and interfaces

Use to show deployable/logical modules and the interfaces between them.

```plantuml
@startuml library_component_overview
package "Backend" {
  [Catalog] as catalog
  [Loans] as loans
  [Fines] as fines
  interface "REST /api" as rest
}
[Web App] as web
database "SQLite" as db
web --> rest
rest - catalog
rest - loans
loans --> fines : compute fine
catalog --> db
loans --> db
@enduml
```

## C4 diagrams: architecture at the right zoom level

Use C4 for architecture overviews: Context (system + people + external systems),
Container (apps, APIs, databases), Component (inside one container). Prefer it over
ad-hoc component diagrams for the system-design stage.

```plantuml
@startuml library_c4_context
!include <C4/C4_Context>
Person(student, "Student", "Borrows and returns books")
Person(librarian, "Librarian", "Manages the catalogue")
System(library, "Library System", "Search, loans, fines")
System_Ext(sso, "Campus SSO", "Authentication")
Rel(student, library, "Uses", "HTTPS")
Rel(librarian, library, "Administers", "HTTPS")
Rel(library, sso, "Authenticates via", "OIDC")
SHOW_LEGEND()
@enduml
```

```plantuml
@startuml library_c4_container
!include <C4/C4_Container>
Person(student, "Student")
System_Boundary(lib, "Library System") {
  Container(web, "Web App", "HTML + JS", "Search and loan pages")
  Container(api, "Loan API", "Python, FastAPI", "Business rules: limits, fines")
  ContainerDb(db, "Database", "SQLite", "Books, students, loans")
}
Rel(student, web, "Uses", "HTTPS")
Rel(web, api, "Calls", "JSON/HTTPS")
Rel(api, db, "Reads/Writes", "SQL")
SHOW_LEGEND()
@enduml
```

## Deployment diagram: where things run

Use in deployment design: nodes, containers, databases, artifacts, protocols.

```plantuml
@startuml library_deployment_single_host
node "Campus VM (Ubuntu 24.04)" as vm {
  node "Docker" {
    artifact "web (nginx)" as web
    artifact "api (uvicorn)" as api
  }
  database "SQLite file\n/data/library.db" as db
}
actor Student
Student --> web : HTTPS 443
web --> api : HTTP 8000
api --> db
@enduml
```

## State diagram: lifecycle of one object

Use for entities with a lifecycle. `<<choice>>` branches on a guard, `<<junction>>`
merges or splits transitions (1.2026.9), composite states nest.

```plantuml
@startuml library_state_loan
[*] --> Active : borrow
state Active {
  [*] --> OnTime
  OnTime --> Late : due date passed
}
state returned <<choice>>
Active --> returned : return book
returned --> Closed : [no fine]
returned --> FineDue : [late]
FineDue --> Closed : fine paid
Closed --> [*]
@enduml
```

## Entity-relationship diagrams: database schema

IE (crow's foot) notation for physical schemas; mark keys and nullability.

```plantuml
@startuml library_er_schema
hide circle
entity student {
  * id : TEXT <<PK>>
  --
  * name : TEXT
}
entity book {
  * isbn : TEXT <<PK>>
  --
  * title : TEXT
  * stock : INTEGER
}
entity loan {
  * id : INTEGER <<PK>>
  --
  * student_id : TEXT <<FK>>
  * isbn : TEXT <<FK>>
  * due_at : DATE
  returned_at : DATE
}
student ||--o{ loan
book ||--o{ loan
@enduml
```

Chen notation (`@startchen`) for conceptual models in requirement analysis:

```plantuml
@startchen library_chen_loans
entity Student {
  StudentId <<key>>
  Name
}
entity Book {
  Isbn <<key>>
  Title
}
relationship Borrows {
  DueDate
}
Student -N- Borrows
Borrows -M- Book
@endchen
```

## File structure diagram: project layout

One full relative path per line (never indentation).

```plantuml
@startfiles library_files_backend
/backend/app/main.py
/backend/app/domain/models.py
/backend/app/services/loans.py
/backend/app/services/fines.py
/backend/tests/test_loans.py
/backend/requirements.txt
@endfiles
```

## Timing diagram: protocol or state over time

```plantuml
@startuml library_timing_loan
concise "Loan" as L
robust "Fine (CNY)" as F
@0
L is Active
F is 0
@30
L is Overdue
@34
F is 2
L is Closed
@enduml
```

## Gantt diagram: sprint plan

```plantuml
@startgantt library_gantt_sprint1
Project starts 2026-12-01
[Catalogue search] requires 3 days
[Borrow / return API] requires 4 days
[Fines] requires 2 days
[Fines] starts at [Borrow / return API]'s end
[Web pages] requires 3 days
[Web pages] starts at [Catalogue search]'s end
[Sprint review] happens at [Fines]'s end
@endgantt
```

## Chart diagram: metrics such as burndown (new in 1.2026.0)

Use for sprint burndown, test pass rates, and similar numbers.

```plantuml
@startchart library_chart_burndown
h-axis [D1, D2, D3, D4, D5, D6, D7]
v-axis 0 --> 40
line "Ideal" [40, 34, 28, 22, 16, 10, 0]
line "Actual" [40, 37, 30, 26, 18, 12, 5]
legend right
@endchart
```

## Mind map and WBS: requirement decomposition

```plantuml
@startmindmap library_mindmap_scope
* Library System
** Catalogue
*** Search by title / author / ISBN
*** Stock levels
** Loans
*** 5-book limit
*** 30-day term
** Fines
*** 0.5 CNY per day
*** Block borrowing while unpaid
left side
** Administration
*** Manage books
*** Overdue list
@endmindmap
```

```plantuml
@startwbs library_wbs_release1
* Release 1
** Backend
*** Domain model
*** Loan API
*** Fine policy
** Frontend
*** Search page
*** My loans page
** Quality
*** API tests
*** Deployment script
@endwbs
```

## JSON / YAML: API payloads and configuration

```plantuml
@startjson library_json_loan_response
{
  "id": 42,
  "isbn": "978-7-111-54742-6",
  "dueDate": "2026-12-31",
  "status": "ACTIVE",
  "fine": null
}
@endjson
```

## Salt: low-fidelity UI wireframe

```plantuml
@startsalt library_salt_search
{+
  {/ <b>Search | My loans | Admin }
  Title or ISBN | "                " | [Search]
  {#
    Title | Author | Stock | .
    Clean Code | R. Martin | 3 | [Borrow]
    Refactoring | M. Fowler | 0 | [Join queue]
  }
}
@endsalt
```

## Styling with `<style>` and themes

```plantuml
@startuml library_style_example
<style>
classDiagram {
  class {
    BackgroundColor #F5F7FF
    LineColor #3355AA
    FontName Helvetica
  }
  arrow {
    LineColor #3355AA
  }
}
.external {
  BackgroundColor #EEEEEE
  LineStyle 4
}
</style>
class LoanService
class CampusSSO <<external>>
LoanService --> CampusSSO
@enduml
```

```plantuml
@startuml library_theme_example
!theme plain
participant Web
participant API
Web -> API : GET /books?q=clean
API --> Web : 200 [..]
@enduml
```

## Common errors and fixes

| Symptom from `plantuml -syntax` | Usual cause | Fix |
|---|---|---|
| `Syntax Error?` on an arrow line | `-> ->`, missing participant name, Markdown inside the block | One arrow per line; plain text only |
| Error on a line with `{` | unbalanced braces in class/state/package | Close every `{` |
| Error on a stereotype line in an activity | stereotype placed before the label | `:Label; <<stereo>>` |
| "Assumed diagram type" is wrong | non-UML content under `@startuml` | Use the dedicated `@startX` keyword |
| Unknown C4 macro | missing include, or a level mismatch | `!include <C4/C4_Container>` (Container includes Context) |
