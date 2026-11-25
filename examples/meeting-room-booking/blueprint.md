# Meeting room booking: blueprint

> `skills/nl2bp` step 3, following `references/output-contract.md`.

## Assumptions

- Times are stored as UTC ISO strings and shown in the office time zone.
- One booking covers exactly one room.

## Class diagram: domain (the implementation contract)

```plantuml
@startuml booking_class_domain
package domain {
  class Room {
    +id: int
    +name: str
    +capacity: int
    +equipment: set[Equipment]
  }
  enum Equipment {
    PROJECTOR
    VIDEO_CONFERENCE
    WHITEBOARD
  }
  class Booking {
    +id: int
    +room_id: int
    +owner_email: str
    +start: datetime
    +end: datetime
    +status: BookingStatus
    +overlaps(start: datetime, end: datetime): bool
  }
  enum BookingStatus {
    CONFIRMED
    CHECKED_IN
    CANCELLED
    RELEASED
    COMPLETED
  }
  class MaintenanceWindow {
    +id: int
    +room_id: int
    +start: datetime
    +end: datetime
    +reason: str
  }
  class BookingPolicy {
    +MAX_DURATION: timedelta = 4h
    +MAX_ADVANCE: timedelta = 30d
    +CHECK_IN_GRACE: timedelta = 15min
    +validate(start: datetime, end: datetime, now: datetime): None
  }
}
Room "1" -- "*" Booking
Room "1" -- "*" MaintenanceWindow
Room --> Equipment
Booking --> BookingStatus
@enduml
```

`BookingPolicy` holds the numbers from BR-2 and BR-3 so they live in one place. `overlaps` is the
predicate the repository uses for BR-1.

## Class diagram: services and API

```plantuml
@startuml booking_class_services
package services {
  class BookingService {
    +search(day: date, start: time, end: time, people: int, equipment: set[Equipment]): list[Room]
    +book(owner_email: str, room_id: int, start: datetime, end: datetime): Booking
    +check_in(booking_id: int, user_email: str, now: datetime): Booking
    +cancel(booking_id: int, user: CurrentUser): Booking
    +release_no_shows(now: datetime): int
  }
  class RoomService {
    +create(room: RoomCreate): Room
    +update(room_id: int, change: RoomUpdate): Room
    +delete(room_id: int): None
    +add_maintenance(room_id: int, start: datetime, end: datetime, reason: str): MaintenanceWindow
  }
  class ReportService {
    +utilisation(week_start: date): list[UtilisationRow]
  }
  interface BookingRepository {
    +find_conflicts(room_id: int, start: datetime, end: datetime): list[Booking]
    +add(booking: Booking): Booking
    +due_for_release(cutoff: datetime): list[Booking]
  }
  class CurrentUser {
    +email: str
    +is_admin: bool
  }
  class UtilisationRow {
    +room_name: str
    +booked_hours: float
    +used_hours: float
  }
  class RoomCreate {
    +name: str
    +capacity: int
    +equipment: set[Equipment]
  }
  class RoomUpdate {
    +name: str?
    +capacity: int?
    +equipment: set[Equipment]?
  }
}
BookingService --> BookingRepository
BookingService ..> domain.BookingPolicy
ReportService --> BookingRepository
@enduml
```

The services are what the HTTP routes call; `BookingRepository` hides SQLite so the rules can
be tested with an in-memory fake.

## Sequence: book a room (US-2)

```plantuml
@startuml booking_sequence_book
autonumber
actor Employee
participant "Web pages" as Web
participant "Booking API" as API
participant BookingService as Svc
database SQLite as DB

Employee -> Web : pick room and slot
Web -> API ++ : POST /bookings {room_id, start, end}
API -> Svc ++ : book(owner, room_id, start, end)
Svc -> Svc : BookingPolicy.validate (BR-2)
Svc -> DB ++ : BEGIN IMMEDIATE; find_conflicts (BR-1)
return conflicts
alt no conflict
  Svc -> DB : INSERT booking CONFIRMED; COMMIT
  Svc --> API : Booking
  API --> Web : 201 Created
else conflict
  Svc --> API : ConflictError
  API --> Web : 409 Conflict {conflicting_booking_id}
end
deactivate Svc
deactivate API
Web --> Employee : show result
@enduml
```

The conflict check and the insert share one `IMMEDIATE` transaction (ADR-1), so two concurrent
requests cannot both succeed.

## Sequence: release no-shows (BR-3)

```plantuml
@startuml booking_sequence_release
participant "Release job" as Job
participant BookingService as Svc
database SQLite as DB
loop every minute
  Job -> Svc ++ : release_no_shows(now)
  Svc -> DB : due_for_release(now - 15 min)
  Svc -> DB : UPDATE status = RELEASED
  return released count
end
@enduml
```

## State diagram: booking lifecycle

```plantuml
@startuml booking_state_booking
[*] --> CONFIRMED : book
CONFIRMED --> CHECKED_IN : check in\n[start - 5 min .. start + 15 min]
CONFIRMED --> CANCELLED : cancel [owner or admin]
CONFIRMED --> RELEASED : no check-in by start + 15 min
CHECKED_IN --> COMPLETED : end time passed
CANCELLED --> [*]
RELEASED --> [*]
COMPLETED --> [*]
@enduml
```

Only `CONFIRMED` and `CHECKED_IN` count as active for the overlap rule.

## Entity-relationship: database schema

```plantuml
@startuml booking_er_schema
hide circle
entity room {
  * id : INTEGER <<PK>>
  --
  * name : TEXT <<unique>>
  * capacity : INTEGER
  * equipment : TEXT
}
entity booking {
  * id : INTEGER <<PK>>
  --
  * room_id : INTEGER <<FK>>
  * owner_email : TEXT
  * start_utc : TEXT
  * end_utc : TEXT
  * status : TEXT
}
entity maintenance_window {
  * id : INTEGER <<PK>>
  --
  * room_id : INTEGER <<FK>>
  * start_utc : TEXT
  * end_utc : TEXT
  reason : TEXT
}
room ||--o{ booking
room ||--o{ maintenance_window
@enduml
```

Index `booking(room_id, start_utc)` serves the overlap query.

## API payload: booking

```plantuml
@startjson booking_json_booking
{
  "id": 812,
  "room_id": 4,
  "owner_email": "li.wei@example.com",
  "start": "2026-12-03T02:00:00Z",
  "end": "2026-12-03T03:30:00Z",
  "status": "CONFIRMED"
}
@endjson
```

## File structure

```plantuml
@startfiles booking_files_layout
/code/app/main.py
/code/app/domain.py
/code/app/policy.py
/code/app/services/booking_service.py
/code/app/services/room_service.py
/code/app/services/report_service.py
/code/app/repository.py
/code/app/jobs.py
/code/web/index.html
/code/web/app.js
/code/tests/test_booking_rules.py
/code/requirements.txt
@endfiles
```

## Wireframe: search page

```plantuml
@startsalt booking_salt_search
{+
  {/ <b>Find a room | My bookings | Admin }
  Date | "2026-12-03" | From | "10:00" | To | "11:30"
  People | "6" | [X] Projector | [ ] Video conference | [Search]
  {#
    Room | Capacity | Equipment | .
    Aurora | 8 | Projector, VC | [Book]
    Birch | 6 | Projector | [Book]
  }
}
@endsalt
```

## Interfaces

| Endpoint | Request | Response | Errors |
|---|---|---|---|
| `GET /rooms/free` | `date, start, end, people, equipment[]` | `Room[]` | 422 |
| `POST /bookings` | `{room_id, start, end}` | `201 Booking` | 409 overlap, 422 BR-2 |
| `POST /bookings/{id}/check-in` | — | `Booking` | 403, 409 outside window |
| `DELETE /bookings/{id}` | — | `Booking (CANCELLED)` | 403 not owner/admin |
| `POST /rooms`, `PATCH /rooms/{id}`, `DELETE /rooms/{id}` | `RoomCreate` / `RoomUpdate` | `Room` | 403 not admin |
| `POST /rooms/{id}/maintenance` | `{start, end, reason}` | `MaintenanceWindow` | 409 overlaps a booking |
| `GET /reports/utilisation?week=` | — | `UtilisationRow[]` | 403 |

## Data flow

1. **Book:** validate BR-2 → in one transaction, check overlap with active bookings and
   maintenance (BR-1) → insert `CONFIRMED`.
2. **Check in:** owner only, inside [start − 5 min, start + 15 min] → `CHECKED_IN`.
3. **Release:** every minute, `CONFIRMED` bookings with start + 15 min < now → `RELEASED`.
4. **Report:** booked hours = sum of non-cancelled durations; used hours = checked-in durations.
