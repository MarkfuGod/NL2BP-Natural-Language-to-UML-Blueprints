# Meeting room booking: architecture

> `skills/nl2bp` step 2.

## Stack

| Part | Choice | Reason |
|---|---|---|
| Backend | Python 3.12, FastAPI | Small JSON API, typed models, built-in OpenAPI |
| Storage | SQLite (WAL) | 300 users, 40 rooms; one writer is enough |
| Frontend | Static HTML + vanilla JS | Three pages; no build step needed |
| Jobs | APScheduler inside the API process | One periodic job (BR-3); no queue required |
| Auth | Company SSO via OIDC | NFR: no local passwords |
| Deploy | One Docker container on the internal VM | Single service |

## Decisions

- **ADR-1 Overlap check in the database.** Context: BR-1 must hold under concurrent requests.
  Decision: insert inside an `IMMEDIATE` transaction that re-checks overlap. Consequence:
  serialised writes, which SQLite handles easily at this scale.
- **ADR-2 Releases as a 1-minute job.** Context: BR-3. Decision: a scheduler job releases
  bookings whose start + 15 min has passed without check-in. Consequence: release happens
  within 1 minute of the deadline.

## C4 context

```plantuml
@startuml booking_c4_context
!include <C4/C4_Context>
Person(employee, "Employee", "Finds, books and checks in")
Person(admin, "Administrator", "Manages rooms, reads reports")
System(booking, "Room Booking", "Search, booking, check-in, reports")
System_Ext(sso, "Company SSO", "OIDC identity provider")
Rel(employee, booking, "Uses", "HTTPS")
Rel(admin, booking, "Administers", "HTTPS")
Rel(booking, sso, "Authenticates users via", "OIDC")
SHOW_LEGEND()
@enduml
```

## C4 container

```plantuml
@startuml booking_c4_container
!include <C4/C4_Container>
Person(employee, "Employee")
Person(admin, "Administrator")
System_Ext(sso, "Company SSO", "OIDC")
System_Boundary(sys, "Room Booking") {
  Container(web, "Web pages", "HTML + JS", "Search, my bookings, admin")
  Container(api, "Booking API", "Python, FastAPI", "Rules BR-1..BR-4, reports")
  Container(jobs, "Release job", "APScheduler", "Releases no-shows every minute")
  ContainerDb(db, "Database", "SQLite", "Rooms, bookings, maintenance")
}
Rel(employee, web, "Uses", "HTTPS")
Rel(admin, web, "Uses", "HTTPS")
Rel(web, api, "Calls", "JSON/HTTPS")
Rel(api, sso, "Validates tokens", "OIDC")
Rel(api, db, "Reads/Writes", "SQL")
Rel(jobs, db, "Releases bookings", "SQL")
SHOW_LEGEND()
@enduml
```

The release job runs inside the API process but is drawn separately because it acts without a
request.
