# room-booking blueprint

## Assumptions

- 采用 requirements.md 的 ASS-1：签到窗口为 `[startAt - 15 分钟, startAt + 15 分钟]`，未签到释放发生在 `startAt + 15 分钟`。
- `ADMIN` 可代替预订人执行签到（US-4-AC4 的例外语义）；取消接口仅允许预订人本人调用，管理员取消他人预订单走维护时段 `force=true` 流程。
- SSO 的 `sub` 直接作为 `bookedBy` / `userId`，系统不建 `users` 表；`roles` 每次请求从令牌读取。
- 数据库存 UTC `timestamptz`，业务上的自然日、`07:00–22:00`、30 天窗口一律按 `Asia/Shanghai` 折算。
- `checkInDeadline` 由 `startAt + 15 分钟` 计算得出，不单独持久化；ER 图中不建列。
- API JSON 使用 camelCase（`userId`、`roomId`、`startAt`、`checkInDeadline`），Python DTO 字段使用 snake_case 并通过别名导出。
- `MaintenanceStatus` 只定义 `ACTIVE`，因为需求只使用 `status = ACTIVE` 的维护时段参与冲突判定；本期不提供维护时段取消接口。
- 通知渠道本期不实际投递，`BookingNotifier` 默认实现为 `LoggingNotifier`，未配置时记录 `NOTIFY_SKIPPED`。
- 冲突判定同时使用应用层 `OverlapPolicy` 与 PostgreSQL GiST 排除约束；应用层负责 409 语义，数据库约束负责并发最后防线。

## Class: 领域模型

```plantuml
@startuml room_booking_class_domain
hide circle
package domain {
  enum Role {
    EMPLOYEE
    ADMIN
  }

  enum Equipment {
    PROJECTOR
    VIDEO_CONFERENCE
  }

  enum RoomStatus {
    ACTIVE
    INACTIVE
    DELETED
  }

  enum BookingStatus {
    RESERVED
    CHECKED_IN
    COMPLETED
    CANCELLED
    RELEASED
  }

  enum CancelReason {
    EMPLOYEE
    MAINTENANCE
    NO_SHOW
  }

  enum MaintenanceStatus {
    ACTIVE
  }

  enum ReportGroupBy {
    ROOM
  }

  enum AuditAction {
    ROOM_CREATED
    ROOM_UPDATED
    ROOM_DELETED
    MAINTENANCE_CREATED
    BOOKING_CANCELLED_BY_MAINTENANCE
    BOOKING_AUTO_RELEASED
  }

  enum AuditEntityType {
    ROOM
    BOOKING
    MAINTENANCE_WINDOW
  }

  class TimeInterval {
    +start_at: datetime
    +end_at: datetime
    +duration_minutes(): int
    +overlaps(other: TimeInterval): bool
    +is_aligned_to_15_minutes(): bool
    +is_within_business_hours(): bool
  }

  class Room {
    +id: UUID
    +name: str
    +floor: str
    +capacity: int
    +equipment: set[Equipment]
    +status: RoomStatus
    +is_bookable(): bool
    +has_all_equipment(required: set[Equipment]): bool
  }

  class Booking {
    +id: UUID
    +room_id: UUID
    +booked_by: str
    +start_at: datetime
    +end_at: datetime
    +attendees: int
    +title: str
    +status: BookingStatus
    +checked_in_at: datetime | None
    +cancel_reason: CancelReason | None
    +released_at: datetime | None
    +created_at: datetime
    +updated_at: datetime
    +interval(): TimeInterval
    +check_in_deadline(): datetime
    +duration_minutes(): int
    +is_active(): bool
    +is_owner(user_id: str): bool
    +check_in(now: datetime): None
    +cancel(reason: CancelReason, now: datetime): None
    +release_no_show(now: datetime): None
    +complete(now: datetime): None
  }

  class MaintenanceWindow {
    +id: UUID
    +room_id: UUID
    +start_at: datetime
    +end_at: datetime
    +reason: str
    +status: MaintenanceStatus
    +created_by: str
    +created_at: datetime
    +interval(): TimeInterval
    +is_active(): bool
    +overlaps(other: TimeInterval): bool
  }

  class AuditLog {
    +id: UUID
    +actor_id: str
    +action: AuditAction
    +entity_type: AuditEntityType
    +entity_id: UUID
    +before_state: dict[str, Any] | None
    +after_state: dict[str, Any] | None
    +created_at: datetime
  }

  class UtilizationReport {
    +room_id: UUID
    +room_name: str
    +available_minutes: int
    +booked_minutes: int
    +used_minutes: int
    +booking_rate: Decimal
    +utilization_rate: Decimal
  }
}
Room "1" -- "0..*" Booking : hosts
Room "1" -- "0..*" MaintenanceWindow : has
Room "1" -- "0..*" UtilizationReport : reported in
Room "1" -- "0..*" Equipment : requires
Booking --> BookingStatus
Booking --> CancelReason
Room --> RoomStatus
MaintenanceWindow --> MaintenanceStatus
AuditLog --> AuditAction
AuditLog --> AuditEntityType
@enduml
```

该图是领域层必须存在的类型清单：`Room`、`Booking`、`MaintenanceWindow`、`AuditLog`、`UtilizationReport` 与全部枚举。`TimeInterval` 统一承载半开区间重叠语义，避免搜索、创建预订、维护时段各自复制一套区间判定。

## Class: 服务与策略

```plantuml
@startuml room_booking_class_services
hide circle
package services {
  class AuthPrincipal {
    +user_id: str
    +display_name: str
    +roles: set[Role]
    +is_admin(): bool
    +has_role(role: Role): bool
  }

  interface TokenVerifier {
    +verify(token: str) -> AuthPrincipal
  }

  class OverlapPolicy {
    +overlaps(a: TimeInterval, b: TimeInterval): bool
  }

  class BookingRules {
    +MIN_DURATION_MINUTES: int = 15
    +MAX_DURATION_MINUTES: int = 240
    +BOOKING_WINDOW_DAYS: int = 30
    +validate_create(interval: TimeInterval, date: date, now: datetime): None
    +validate_search(date: date, interval: TimeInterval): None
    +validate_check_in(booking: Booking, principal: AuthPrincipal, now: datetime): None
    +validate_cancel(booking: Booking, principal: AuthPrincipal, now: datetime): None
    +validate_room(name: str, floor: str, capacity: int): None
    +validate_maintenance(interval: TimeInterval, now: datetime): None
    +validate_report_range(from_date: date, to_date: date): None
  }

  class BookingService {
    +search_available(date: date, interval: TimeInterval, attendees: int, equipment: set[Equipment], page: int, size: int) -> RoomPage
    +create_booking(principal: AuthPrincipal, room_id: UUID, date: date, interval: TimeInterval, attendees: int, title: str, now: datetime) -> Booking
    +check_in(principal: AuthPrincipal, booking_id: UUID, now: datetime) -> Booking
    +cancel(principal: AuthPrincipal, booking_id: UUID, now: datetime) -> Booking
    +list_mine(principal: AuthPrincipal, from_date: date, to_date: date, status: BookingStatus | None) -> list[Booking]
  }

  class RoomAdminService {
    +create_room(principal: AuthPrincipal, name: str, floor: str, capacity: int, equipment: set[Equipment]) -> Room
    +update_room(principal: AuthPrincipal, room_id: UUID, name: str | None, floor: str | None, capacity: int | None, equipment: set[Equipment] | None) -> Room
    +delete_room(principal: AuthPrincipal, room_id: UUID, now: datetime) -> None
  }

  class MaintenanceService {
    +create_window(principal: AuthPrincipal, room_id: UUID, interval: TimeInterval, reason: str, force: bool, now: datetime) -> MaintenanceWindow
  }

  class ReportService {
    +utilization(from_date: date, to_date: date, group_by: ReportGroupBy) -> list[UtilizationReport]
  }

  class AdminBookingService {
    +list_by_date(on_date: date) -> list[Booking]
  }

  class AuditService {
    +record(actor_id: str, action: AuditAction, entity_type: AuditEntityType, entity_id: UUID, before_state: dict[str, Any] | None, after_state: dict[str, Any] | None) -> None
  }

  interface BookingNotifier {
    +notify_released(booking_id: UUID, reason: CancelReason, released_at: datetime) -> None
  }

  class LoggingNotifier {
    +notify_released(booking_id: UUID, reason: CancelReason, released_at: datetime) -> None
  }

  class SchedulerResult {
    +released_count: int
    +completed_count: int
    +lag_seconds: float
  }

  class Scheduler {
    +run_once(now: datetime) -> SchedulerResult
    +run_forever() -> None
  }
}
AuthPrincipal --> Role
BookingService ..> BookingRules
BookingService ..> UnitOfWork
RoomAdminService ..> BookingRules
RoomAdminService ..> UnitOfWork
RoomAdminService ..> AuditService
MaintenanceService ..> BookingRules
MaintenanceService ..> UnitOfWork
MaintenanceService ..> AuditService
ReportService ..> BookingRules
ReportService ..> UnitOfWork
AdminBookingService ..> UnitOfWork
Scheduler ..> UnitOfWork
Scheduler ..> AuditService
Scheduler ..> BookingNotifier
LoggingNotifier ..|> BookingNotifier
BookingRules ..> OverlapPolicy
@enduml
```

该图声明业务服务、规则策略、鉴权端口和通知端口。`BookingService` 与 `MaintenanceService` 共享 `BookingRules` 与 `OverlapPolicy`，对应需求中“搜索可用”和“创建预订”不得各写一套冲突判定的约束。

## Class: 持久化端口

```plantuml
@startuml room_booking_class_persistence
hide circle
package persistence {
  interface UnitOfWork {
    +rooms: RoomRepository
    +bookings: BookingRepository
    +maintenance: MaintenanceRepository
    +audits: AuditRepository
    +commit(): None
    +rollback(): None
  }

  interface RoomRepository {
    +get(room_id: UUID) -> Room | None
    +get_for_update(room_id: UUID) -> Room | None
    +find_by_name(name: str) -> Room | None
    +list_available(date: date, interval: TimeInterval, attendees: int, equipment: set[Equipment], page: int, size: int) -> list[Room]
    +add(room: Room) -> None
    +save(room: Room) -> None
    +has_future_active_bookings(room_id: UUID, now: datetime) -> bool
    +list_future_active_bookings(room_id: UUID, now: datetime) -> list[Booking]
  }

  interface BookingRepository {
    +get(booking_id: UUID) -> Booking | None
    +get_for_update(booking_id: UUID) -> Booking | None
    +insert(booking: Booking) -> None
    +save(booking: Booking) -> None
    +list_active_overlapping(room_id: UUID, interval: TimeInterval) -> list[Booking]
    +list_mine(user_id: str, from_date: date, to_date: date, status: BookingStatus | None) -> list[Booking]
    +list_by_date(on_date: date) -> list[Booking]
    +list_reserved_candidates(now: datetime, limit: int) -> list[Booking]
    +list_completion_candidates(now: datetime, limit: int) -> list[Booking]
  }

  interface MaintenanceRepository {
    +list_active_overlapping(room_id: UUID, interval: TimeInterval) -> list[MaintenanceWindow]
    +add(window: MaintenanceWindow) -> None
    +list_active_in_range(room_id: UUID, from_at: datetime, to_at: datetime) -> list[MaintenanceWindow]
  }

  interface AuditRepository {
    +add(log: AuditLog) -> None
    +delete_older_than(cutoff: datetime) -> int
  }

  class SqlAlchemyUnitOfWork {
  }

  class SqlAlchemyRoomRepository {
  }

  class SqlAlchemyBookingRepository {
  }

  class SqlAlchemyMaintenanceRepository {
  }

  class SqlAlchemyAuditRepository {
  }
}
UnitOfWork <|.. SqlAlchemyUnitOfWork
RoomRepository <|.. SqlAlchemyRoomRepository
BookingRepository <|.. SqlAlchemyBookingRepository
MaintenanceRepository <|.. SqlAlchemyMaintenanceRepository
AuditRepository <|.. SqlAlchemyAuditRepository
@enduml
```

持久化端口把 `SELECT FOR UPDATE`、排除约束触发和审计写入封装在 `UnitOfWork` 边界内。服务层只依赖端口，不直接拼 SQL；创建预订必须先经过 `RoomRepository.get_for_update`。

## Class: API DTO 与错误码

```plantuml
@startuml room_booking_class_api
hide circle
package api {
  enum ErrorCode {
    UNAUTHENTICATED
    FORBIDDEN
    INVALID_DURATION
    INVALID_TIME_GRANULARITY
    INVALID_DATE_RANGE
    BOOKING_WINDOW_EXCEEDED
    OUT_OF_BUSINESS_HOURS
    START_IN_PAST
    ROOM_SLOT_CONFLICT
    CAPACITY_EXCEEDED
    INVALID_ATTENDEES
    INVALID_CAPACITY
    ROOM_NAME_DUPLICATED
    ROOM_HAS_FUTURE_BOOKINGS
    MAINTENANCE_CONFLICT
    INVALID_MAINTENANCE_WINDOW
    REPORT_RANGE_TOO_LARGE
    CHECKIN_NOT_OPEN
    BOOKING_NOT_ACTIVE
    CANNOT_CANCEL_AFTER_START
  }

  class ErrorResponse {
    +code: ErrorCode
    +message: str
    +details: dict[str, Any] | None
  }

  class MeResponse {
    +user_id: str
    +display_name: str
    +roles: list[Role]
  }

  class RoomItem {
    +id: UUID
    +name: str
    +floor: str
    +capacity: int
    +equipment: list[Equipment]
    +status: RoomStatus
  }

  class RoomPage {
    +items: list[RoomItem]
    +page: int
    +size: int
    +total: int
  }

  class AvailableRoomsQuery {
    +date: date
    +start: time
    +end: time
    +attendees: int
    +equipment: list[Equipment]
    +page: int
    +size: int
  }

  class CreateBookingRequest {
    +room_id: UUID
    +date: date
    +start: time
    +end: time
    +attendees: int
    +title: str
  }

  class BookingResponse {
    +id: UUID
    +room_id: UUID
    +booked_by: str
    +start_at: datetime
    +end_at: datetime
    +attendees: int
    +title: str
    +status: BookingStatus
    +check_in_deadline: datetime
    +checked_in_at: datetime | None
    +cancel_reason: CancelReason | None
    +released_at: datetime | None
  }

  class MyBookingsQuery {
    +from_date: date
    +to_date: date
    +status: BookingStatus | None
  }

  class BookingListResponse {
    +items: list[BookingResponse]
  }

  class CreateRoomRequest {
    +name: str
    +floor: str
    +capacity: int
    +equipment: list[Equipment]
  }

  class UpdateRoomRequest {
    +name: str | None
    +floor: str | None
    +capacity: int | None
    +equipment: list[Equipment] | None
  }

  class RoomResponse {
    +id: UUID
    +name: str
    +floor: str
    +capacity: int
    +equipment: list[Equipment]
    +status: RoomStatus
  }

  class CreateMaintenanceRequest {
    +start_at: datetime
    +end_at: datetime
    +reason: str
    +force: bool
  }

  class ConflictBookingItem {
    +id: UUID
    +booked_by: str
    +start_at: datetime
    +end_at: datetime
  }

  class MaintenanceConflictResponse {
    +code: ErrorCode
    +message: str
    +conflicts: list[ConflictBookingItem]
  }

  class MaintenanceWindowResponse {
    +id: UUID
    +room_id: UUID
    +start_at: datetime
    +end_at: datetime
    +reason: str
    +status: MaintenanceStatus
  }

  class UtilizationQuery {
    +from_date: date
    +to_date: date
    +group_by: ReportGroupBy
  }

  class UtilizationReportItem {
    +room_id: UUID
    +room_name: str
    +available_minutes: int
    +booked_minutes: int
    +used_minutes: int
    +booking_rate: Decimal
    +utilization_rate: Decimal
  }

  class UtilizationReportResponse {
    +items: list[UtilizationReportItem]
    +from_date: date
    +to_date: date
  }

  class AdminBookingsQuery {
    +date: date
  }

  class AdminBookingItem {
    +id: UUID
    +room_id: UUID
    +booked_by: str
    +start_at: datetime
    +end_at: datetime
    +status: BookingStatus
  }

  class AdminBookingListResponse {
    +items: list[AdminBookingItem]
  }
}
ErrorResponse --> ErrorCode
MaintenanceConflictResponse --> ErrorCode
MaintenanceConflictResponse "1" -- "0..*" ConflictBookingItem : contains
RoomPage "1" -- "0..*" RoomItem : items
BookingListResponse "1" -- "0..*" BookingResponse : items
UtilizationReportResponse "1" -- "0..*" UtilizationReportItem : items
AdminBookingListResponse "1" -- "0..*" AdminBookingItem : items
@enduml
```

该图声明 REST 层所有请求、响应和错误码类型。错误码与需求中的 `INVALID_DURATION`、`ROOM_SLOT_CONFLICT`、`CHECKIN_NOT_OPEN` 等逐一对应，避免接口返回自由文本错误。

## Sequence: 登录与当前用户（US-1）

```plantuml
@startuml room_booking_sequence_login_me
autonumber
actor Employee
participant "web (React SPA)" as Web
participant "api (FastAPI)" as API
participant "SSO (OIDC/JWKS)" as SSO
Employee -> Web : open application
Web -> API : GET /api/v1/me with Bearer token
API -> SSO : verify JWT signature and load JWKS
SSO --> API : sub, name, roles
alt token valid
  API --> Web : 200 MeResponse userId, displayName, roles
  Web --> Employee : render identity and menu
else missing or expired token
  API --> Web : 401 ErrorResponse UNAUTHENTICATED
  Web --> Employee : show login prompt
end
@enduml
```

登录流程把身份来源完全交给 SSO，业务层只接收 `AuthPrincipal`。`/me` 返回的 `userId` 直接来自令牌 `sub`，因此后续预订归属判定不依赖请求体中的 `bookedBy`。

## Sequence: 搜索空闲会议室（US-2）

```plantuml
@startuml room_booking_sequence_search_available
autonumber
actor Employee
participant "web (React SPA)" as Web
participant "api (FastAPI)" as API
participant "BookingService" as BS
participant "BookingRules" as Rules
participant "UnitOfWork" as UoW
database "PostgreSQL" as DB
Employee -> Web : submit date, start, end, attendees, equipment
Web -> API : GET /api/v1/rooms/available with query params
API -> BS : search_available(date, start, end, attendees, equipment, page, size)
BS -> Rules : validate_search(date, interval)
alt invalid duration or time granularity
  Rules --> BS : INVALID_DURATION or INVALID_TIME_GRANULARITY
  BS --> API : validation error
  API --> Web : 400 ErrorResponse
else valid query
  BS -> UoW : rooms.list_available(date, interval, attendees, equipment, page, size)
  UoW -> DB : SELECT active rooms with capacity and equipment
  UoW -> DB : EXCLUDE active bookings and active maintenance overlaps
  DB --> UoW : rows
  UoW --> BS : rooms
  BS --> API : rooms
  API --> Web : 200 RoomPage ordered by capacity, id
end
@enduml
```

搜索在同一查询中应用容量、设备、房间状态和半开区间不重叠条件。端点相接不算冲突由 `TimeInterval.overlaps` 与 SQL 的 `tstzrange &&` 共同保证，不会把 `09:00–10:00` 与 `10:00–11:00` 判成冲突。

## Sequence: 创建预订（US-3）

```plantuml
@startuml room_booking_sequence_create_booking
autonumber
actor Employee
participant "web (React SPA)" as Web
participant "api (FastAPI)" as API
participant "BookingService" as BS
participant "BookingRules" as Rules
participant "UnitOfWork" as UoW
database "PostgreSQL" as DB
Employee -> Web : choose room and submit booking
Web -> API : POST /api/v1/bookings
API -> BS : create_booking(principal, room_id, date, interval, attendees, title, now)
BS -> Rules : validate_create(interval, date, now)
alt validation fails
  Rules --> BS : INVALID_DURATION or BOOKING_WINDOW_EXCEEDED or OUT_OF_BUSINESS_HOURS or START_IN_PAST
  BS --> API : validation error
  API --> Web : 400 ErrorResponse
else validation passes
  BS -> UoW : begin()
  BS -> UoW : rooms.get_for_update(room_id)
  UoW -> DB : SELECT room FOR UPDATE
  DB --> UoW : room
  UoW --> BS : room
  alt room missing or not ACTIVE
    BS -> UoW : rollback()
    BS --> API : room not bookable
    API --> Web : 400 or 404 ErrorResponse
  else room bookable
    BS -> UoW : bookings.list_active_overlapping(room_id, interval)
    UoW -> DB : SELECT RESERVED or CHECKED_IN bookings overlapping
    DB --> UoW : bookings
    BS -> UoW : maintenance.list_active_overlapping(room_id, interval)
    UoW -> DB : SELECT ACTIVE maintenance overlapping
    DB --> UoW : maintenance
    BS -> Rules : has_overlap(bookings, maintenance, interval)
    Rules --> BS : bool
    alt overlap exists
      BS -> UoW : rollback()
      BS --> API : ROOM_SLOT_CONFLICT
      API --> Web : 409 ErrorResponse
    else no overlap
      BS -> UoW : bookings.insert(booking)
      BS -> UoW : commit()
      UoW -> DB : INSERT booking and enforce GiST exclusion constraint
      alt exclusion violation
        UoW --> BS : IntegrityError
        BS -> UoW : rollback()
        BS --> API : ROOM_SLOT_CONFLICT
        API --> Web : 409 ErrorResponse
      else commit succeeds
        UoW --> BS : booking
        BS --> API : booking
        API --> Web : 201 BookingResponse
      end
    end
  end
end
@enduml
```

创建预订把规则校验与临界区分离：所有 400 前置校验完成后，才进入 `SELECT FOR UPDATE` 与区间重叠判定。即使应用层判断被并发穿透，GiST 排除约束仍会把第二个写入打断为 409，保证同房间同时段有效预订数不超过 1。

## Sequence: 签到（US-4）

```plantuml
@startuml room_booking_sequence_check_in
autonumber
actor Employee
participant "web (React SPA)" as Web
participant "api (FastAPI)" as API
participant "BookingService" as BS
participant "UnitOfWork" as UoW
database "PostgreSQL" as DB
Employee -> Web : click check in
Web -> API : POST /api/v1/bookings/booking_id/check-in
API -> BS : check_in(principal, booking_id, now)
BS -> UoW : bookings.get_for_update(booking_id)
UoW -> DB : SELECT booking FOR UPDATE
DB --> UoW : booking
UoW --> BS : booking
alt requester is not owner and not ADMIN
  BS --> API : FORBIDDEN
  API --> Web : 403 ErrorResponse
else status is CHECKED_IN
  BS --> API : booking with original checkedInAt
  API --> Web : 200 BookingResponse
else status is CANCELLED, RELEASED or COMPLETED
  BS --> API : BOOKING_NOT_ACTIVE
  API --> Web : 409 ErrorResponse
else now is before startAt minus 15 minutes
  BS --> API : CHECKIN_NOT_OPEN
  API --> Web : 409 ErrorResponse
else now is after startAt plus 15 minutes
  BS --> API : BOOKING_NOT_ACTIVE
  API --> Web : 409 ErrorResponse
else within check-in window
  BS -> BS : booking.check_in(now)
  BS -> UoW : commit()
  UoW -> DB : UPDATE status CHECKED_IN and checked_in_at
  BS --> API : booking
  API --> Web : 200 BookingResponse
end
@enduml
```

签到以行锁读取预订单，先判越权与状态，再判时间窗。已签到重复调用直接返回 200 且不覆盖 `checkedInAt`，满足幂等要求。

## Sequence: 未签到自动释放（US-5）

```plantuml
@startuml room_booking_sequence_auto_release
autonumber
participant "scheduler (app/scheduler.py)" as S
participant "BookingNotifier" as Notifier
participant "UnitOfWork" as UoW
database "PostgreSQL" as DB
S -> DB : pg_try_advisory_lock(scheduler_key)
alt lock not acquired
  S -> S : end this round
else lock acquired
  S -> UoW : bookings.list_reserved_candidates(now, batch_size)
  UoW -> DB : SELECT RESERVED bookings with checked_in_at IS NULL and start_at <= now
  DB --> UoW : candidates
  loop each candidate
    alt now is at or after startAt plus 15 minutes
      S -> UoW : bookings.release_no_show(booking_id, now)
      UoW -> DB : UPDATE to RELEASED, NO_SHOW, released_at WHERE id and status RESERVED
      DB --> UoW : rowcount
      alt rowcount is 1
        S -> UoW : audits.add(BOOKING_AUTO_RELEASED)
        S -> UoW : commit()
        S -> Notifier : notify_released(booking_id, NO_SHOW, now)
      else rowcount is 0
        S -> S : skip duplicate state change and audit
      end
    else still inside check-in window
      S -> S : keep RESERVED
    end
  end
  S -> UoW : bookings.list_completion_candidates(now, batch_size)
  UoW -> DB : UPDATE RESERVED or CHECKED_IN to COMPLETED where end_at <= now
  S -> DB : pg_advisory_unlock(scheduler_key)
end
@enduml
```

调度器先用 advisory lock 保证多实例单活，再用带 `status = RESERVED` 条件的更新实现幂等。释放、审计与通知在同轮内完成，通知失败不阻塞状态落库。

## Sequence: 取消自己的预订（US-6）

```plantuml
@startuml room_booking_sequence_cancel_booking
autonumber
actor Employee
participant "web (React SPA)" as Web
participant "api (FastAPI)" as API
participant "BookingService" as BS
participant "UnitOfWork" as UoW
database "PostgreSQL" as DB
Employee -> Web : click cancel
Web -> API : POST /api/v1/bookings/booking_id/cancel
API -> BS : cancel(principal, booking_id, now)
BS -> UoW : bookings.get_for_update(booking_id)
UoW -> DB : SELECT booking FOR UPDATE
DB --> UoW : booking
UoW --> BS : booking
alt requester is not owner
  BS --> API : FORBIDDEN
  API --> Web : 403 ErrorResponse
else status is not RESERVED
  BS --> API : BOOKING_NOT_ACTIVE
  API --> Web : 409 ErrorResponse
else now is at or after startAt
  BS --> API : CANNOT_CANCEL_AFTER_START
  API --> Web : 409 ErrorResponse
else allowed to cancel
  BS -> BS : booking.cancel(EMPLOYEE, now)
  BS -> UoW : commit()
  UoW -> DB : UPDATE status CANCELLED and cancel_reason EMPLOYEE
  BS --> API : booking
  API --> Web : 200 BookingResponse
end
@enduml
```

取消接口只允许预订人本人调用，并在行锁内检查状态与开始时间。状态变更提交后，该时段因 `CANCELLED` 退出 GiST 排除约束，立即可被他人重新预订。

## Sequence: 查看我的预订（US-7）

```plantuml
@startuml room_booking_sequence_my_bookings
autonumber
actor Employee
participant "web (React SPA)" as Web
participant "api (FastAPI)" as API
participant "BookingService" as BS
participant "BookingRules" as Rules
participant "UnitOfWork" as UoW
database "PostgreSQL" as DB
Employee -> Web : open my bookings
Web -> API : GET /api/v1/bookings/mine with from, to, status
API -> BS : list_mine(principal, from_date, to_date, status)
BS -> Rules : validate_date_range(from_date, to_date)
alt from_date is after to_date
  Rules --> BS : INVALID_DATE_RANGE
  BS --> API : validation error
  API --> Web : 400 ErrorResponse
else valid range
  BS -> UoW : bookings.list_mine(user_id, from_date, to_date, status)
  UoW -> DB : SELECT own bookings ordered by start_at
  DB --> UoW : bookings
  UoW --> BS : bookings
  BS --> API : bookings
  API -> API : map checkInDeadline = startAt plus 15 minutes
  API --> Web : 200 BookingListResponse
end
@enduml
```

查询强制使用令牌 `sub` 作为过滤条件，跨用户不会返回数据。`checkInDeadline` 在响应映射阶段计算，保证每条 `RESERVED` 预订都带签到截止时间。

## Sequence: 管理员新增、修改、删除会议室（US-8）

```plantuml
@startuml room_booking_sequence_admin_rooms
autonumber
actor Admin
participant "web (React SPA)" as Web
participant "api (FastAPI)" as API
participant "RoomAdminService" as RoomAdmin
participant "BookingRules" as Rules
participant "UnitOfWork" as UoW
database "PostgreSQL" as DB
Admin -> Web : open /admin rooms
Web -> API : POST /api/v1/admin/rooms
API -> API : require_admin(principal)
API -> RoomAdmin : create_room(principal, name, floor, capacity, equipment)
RoomAdmin -> Rules : validate_room(name, floor, capacity)
alt invalid capacity or field
  Rules --> RoomAdmin : INVALID_CAPACITY or invalid field
  RoomAdmin --> API : validation error
  API --> Web : 400 ErrorResponse
else valid
  RoomAdmin -> UoW : rooms.find_by_name(name)
  UoW -> DB : SELECT room by name
  DB --> UoW : room or None
  alt duplicate name
    RoomAdmin --> API : ROOM_NAME_DUPLICATED
    API --> Web : 409 ErrorResponse
  else name unique
    RoomAdmin -> UoW : rooms.add(room)
    RoomAdmin -> UoW : audits.add(ROOM_CREATED)
    RoomAdmin -> UoW : commit()
    UoW -> DB : INSERT room and audit
    RoomAdmin --> API : room
    API --> Web : 201 RoomResponse
  end
end
group PATCH /api/v1/admin/rooms/room_id
  Web -> API : PATCH /api/v1/admin/rooms/room_id
  API -> RoomAdmin : update_room(principal, room_id, name, floor, capacity, equipment)
  RoomAdmin -> Rules : validate_room(name, floor, capacity)
  RoomAdmin -> UoW : rooms.get(room_id)
  UoW -> DB : SELECT room
  DB --> UoW : room
  alt duplicate new name
    RoomAdmin --> API : ROOM_NAME_DUPLICATED
    API --> Web : 409 ErrorResponse
  else valid update
    RoomAdmin -> UoW : rooms.save(room)
    RoomAdmin -> UoW : audits.add(ROOM_UPDATED)
    RoomAdmin -> UoW : commit()
    API --> Web : 200 RoomResponse
  end
end
group DELETE /api/v1/admin/rooms/room_id
  Web -> API : DELETE /api/v1/admin/rooms/room_id
  API -> RoomAdmin : delete_room(principal, room_id, now)
  RoomAdmin -> UoW : rooms.has_future_active_bookings(room_id, now)
  UoW -> DB : SELECT future active bookings
  DB --> UoW : exists
  alt future bookings exist
    RoomAdmin -> UoW : rooms.list_future_active_bookings(room_id, now)
    RoomAdmin --> API : ROOM_HAS_FUTURE_BOOKINGS with conflicts
    API --> Web : 409 ErrorResponse
  else no future bookings
    RoomAdmin -> UoW : rooms.save(status DELETED)
    RoomAdmin -> UoW : audits.add(ROOM_DELETED)
    RoomAdmin -> UoW : commit()
    API --> Web : 204 No Content
  end
end
@enduml
```

管理员会议室写操作统一先做角色检查与字段校验，再在事务内写业务数据与审计。删除采用软删除，存在未来有效预订时返回冲突清单而不是级联删除。

## Sequence: 设置维护时段（US-9）

```plantuml
@startuml room_booking_sequence_maintenance
autonumber
actor Admin
participant "web (React SPA)" as Web
participant "api (FastAPI)" as API
participant "MaintenanceService" as Maint
participant "BookingRules" as Rules
participant "UnitOfWork" as UoW
database "PostgreSQL" as DB
Admin -> Web : choose room and maintenance interval
Web -> API : POST /api/v1/admin/rooms/room_id/maintenance
API -> API : require_admin(principal)
API -> Maint : create_window(principal, room_id, interval, reason, force, now)
Maint -> Rules : validate_maintenance(interval, now)
alt invalid window or outside 30-day window
  Rules --> Maint : INVALID_MAINTENANCE_WINDOW or BOOKING_WINDOW_EXCEEDED
  Maint --> API : validation error
  API --> Web : 400 ErrorResponse
else valid window
  Maint -> UoW : rooms.get_for_update(room_id)
  Maint -> UoW : bookings.list_active_overlapping(room_id, interval)
  UoW -> DB : SELECT active bookings overlapping
  DB --> UoW : conflicts
  alt conflicts exist and force is false
    Maint --> API : MAINTENANCE_CONFLICT with conflicts
    API --> Web : 409 MaintenanceConflictResponse
  else no conflict or force is true
    Maint -> UoW : maintenance.add(window)
    opt force is true and conflicts exist
      loop each conflict
        Maint -> UoW : bookings.cancel_for_maintenance(conflict_id, now)
        Maint -> UoW : audits.add(BOOKING_CANCELLED_BY_MAINTENANCE)
      end
    end
    Maint -> UoW : audits.add(MAINTENANCE_CREATED)
    Maint -> UoW : commit()
    UoW -> DB : INSERT maintenance, update cancelled bookings, insert audits
    Maint --> API : window
    API --> Web : 201 MaintenanceWindowResponse
  end
end
@enduml
```

维护时段流程把“是否破坏既有预订”做成显式分支：`force=false` 返回 409 与冲突清单，`force=true` 才级联取消并逐条写审计。维护时段创建后立即参与可用搜索的排除条件。

## Sequence: 使用率报表（US-10）

```plantuml
@startuml room_booking_sequence_utilization_report
autonumber
actor Admin
participant "web (React SPA)" as Web
participant "api (FastAPI)" as API
participant "ReportService" as Report
participant "BookingRules" as Rules
database "PostgreSQL" as DB
Admin -> Web : open utilization report
Web -> API : GET /api/v1/admin/reports/utilization
API -> API : require_admin(principal)
API -> Report : utilization(from_date, to_date, group_by)
Report -> Rules : validate_report_range(from_date, to_date)
alt invalid range
  Rules --> Report : INVALID_DATE_RANGE or REPORT_RANGE_TOO_LARGE
  Report --> API : validation error
  API --> Web : 400 ErrorResponse
else valid range
  Report -> DB : aggregate available, booked and used minutes per room
  DB --> Report : rows
  Report --> API : list of UtilizationReport
  API --> Web : 200 UtilizationReportResponse
end
@enduml
```

报表由一条实时聚合 SQL 生成，可用分钟数扣除 ACTIVE 维护时段，比率保留 4 位小数。SQL 只按房间聚合，不选择员工姓名或 `userId` 明细。

## Sequence: 管理员查看某日全部预订（US-12）

```plantuml
@startuml room_booking_sequence_admin_bookings
autonumber
actor Admin
participant "web (React SPA)" as Web
participant "api (FastAPI)" as API
participant "AdminBookingService" as ABS
participant "UnitOfWork" as UoW
database "PostgreSQL" as DB
Admin -> Web : open daily booking board
Web -> API : GET /api/v1/admin/bookings with date
API -> API : require_admin(principal)
API -> ABS : list_by_date(on_date)
ABS -> UoW : bookings.list_by_date(on_date)
UoW -> DB : SELECT bookings on date ordered by room_id, start_at
DB --> UoW : bookings
UoW --> ABS : bookings
ABS --> API : bookings
API --> Web : 200 AdminBookingListResponse
@enduml
```

该接口只服务管理员，按 `roomId` 与 `startAt` 升序返回当天全部预订。响应包含 `bookedBy` 与 `status`，用于现场冲突排查。

## Sequence: 网页端预订全流程（US-11）

```plantuml
@startuml room_booking_sequence_web_flow
autonumber
actor Employee
participant "web (React SPA)" as Web
participant "api (FastAPI)" as API
Employee -> Web : fill search form and submit
Web -> API : GET /api/v1/rooms/available
API --> Web : 200 RoomPage
Web --> Employee : render room table
Employee -> Web : click book on a room
Web -> API : POST /api/v1/bookings
alt 201 Created
  API --> Web : 201 BookingResponse
  Web -> Web : prepend booking to my bookings list
  Web --> Employee : show check-in hint with HH:mm
else 409 ROOM_SLOT_CONFLICT
  API --> Web : 409 ErrorResponse
  Web --> Employee : show conflict message and stay on page
end
Employee -> Web : click check in
Web -> API : POST /api/v1/bookings/booking_id/check-in
API --> Web : 200 BookingResponse
Web --> Employee : update status to CHECKED_IN
Employee -> Web : click cancel
Web -> API : POST /api/v1/bookings/booking_id/cancel
API --> Web : 200 BookingResponse
Web --> Employee : remove booking from active list
@enduml
```

网页流程不等待手动刷新：创建成功后直接把返回的 `BookingResponse` 插入“我的预订”列表。409 冲突时只显示可读提示并保留当前搜索结果，符合 US-11-AC3。

## Sequence: 预订释放通知（US-13）

```plantuml
@startuml room_booking_sequence_notification
autonumber
participant "Scheduler" as S
participant "BookingNotifier" as Notifier
participant "Notification Channel" as Channel
participant "application log" as Log
S -> Notifier : notify_released(booking_id, reason, released_at)
alt notification channel configured
  Notifier -> Channel : POST BookingReleased
  Channel --> Notifier : 2xx response
else notification channel missing
  Notifier -> Log : NOTIFY_SKIPPED
end
Notifier --> S : done
@enduml
```

通知是进程内端口，不进入主事务；渠道未配置时只记录 `NOTIFY_SKIPPED`。这满足 US-13-AC2“通知失败不影响预订状态变更”。

## State: 预订生命周期

```plantuml
@startuml room_booking_state_booking
hide empty description
[*] --> RESERVED : create booking
RESERVED --> CHECKED_IN : check in within window
RESERVED --> RELEASED : auto release after startAt plus 15 minutes without check-in
RESERVED --> CANCELLED : owner cancels before startAt
RESERVED --> CANCELLED : force maintenance
RESERVED --> COMPLETED : endAt reached
CHECKED_IN --> COMPLETED : endAt reached
RELEASED --> [*]
CANCELLED --> [*]
COMPLETED --> [*]
@enduml
```

预订状态机把签到、自动释放、取消和完成四类迁移固定下来。`RELEASED` 与 `CANCELLED` 都是终态，不再参与冲突判定，也不能再次签到或取消。

## State: 会议室生命周期

```plantuml
@startuml room_booking_state_room
hide empty description
[*] --> ACTIVE : create room
ACTIVE --> INACTIVE : deactivate
INACTIVE --> ACTIVE : activate
ACTIVE --> DELETED : delete when no future active bookings
INACTIVE --> DELETED : delete when no future active bookings
DELETED --> [*]
@enduml
```

会议室只有 `ACTIVE` 可被搜索和预订；`DELETED` 为软删除终态，历史预订与报表数据仍保留。存在未来有效预订时，删除迁移被禁止并返回 `ROOM_HAS_FUTURE_BOOKINGS`。

## IE ER: 数据库 schema

```plantuml
@startuml room_booking_er_schema
hide circle
entity rooms {
  * id : UUID <<PK>>
  --
  * name : VARCHAR(50) <<unique>>
  * floor : VARCHAR(20)
  * capacity : INTEGER
  * equipment : equipment[]
  * status : room_status
  * created_at : TIMESTAMPTZ
  * updated_at : TIMESTAMPTZ
}
entity bookings {
  * id : UUID <<PK>>
  --
  * room_id : UUID <<FK>>
  * booked_by : VARCHAR(255)
  * start_at : TIMESTAMPTZ
  * end_at : TIMESTAMPTZ
  * attendees : INTEGER
  * title : VARCHAR(200)
  * status : booking_status
  checked_in_at : TIMESTAMPTZ
  cancel_reason : cancel_reason
  released_at : TIMESTAMPTZ
  * created_at : TIMESTAMPTZ
  * updated_at : TIMESTAMPTZ
}
entity maintenance_windows {
  * id : UUID <<PK>>
  --
  * room_id : UUID <<FK>>
  * start_at : TIMESTAMPTZ
  * end_at : TIMESTAMPTZ
  * reason : VARCHAR(255)
  * status : maintenance_status
  * created_by : VARCHAR(255)
  * created_at : TIMESTAMPTZ
}
entity audit_logs {
  * id : UUID <<PK>>
  --
  * actor_id : VARCHAR(255)
  * action : audit_action
  * entity_type : audit_entity_type
  * entity_id : UUID
  before_state : JSONB
  after_state : JSONB
  * created_at : TIMESTAMPTZ
}
rooms ||--o{ bookings : has
rooms ||--o{ maintenance_windows : has
@enduml
```

ER 图给出物理表与 PostgreSQL 类型：时间列统一 `TIMESTAMPTZ`，`bookings` 与 `maintenance_windows` 通过 `room_id` 关联 `rooms`。`audit_logs` 使用多态 `entity_id`，不建外键，以保留 365 天历史审计。

## Interfaces

| Endpoint / method | Request | Response | Errors |
|---|---|---|---|
| `GET /api/v1/me` | `Authorization: Bearer <token>` | `200 {userId, displayName, roles[]}` | `401 UNAUTHENTICATED` |
| `GET /api/v1/rooms/available` | Query: `date`, `start`, `end`, `attendees`, `equipment`, `page`, `size` | `200 {items[], page, size, total}`；无结果时 `items=[]` | `400 INVALID_DURATION`, `INVALID_TIME_GRANULARITY`, `OUT_OF_BUSINESS_HOURS`, `BOOKING_WINDOW_EXCEEDED`; `401 UNAUTHENTICATED` |
| `POST /api/v1/bookings` | Body: `{roomId, date, startTime, endTime, attendees, title}` | `201 BookingResponse`，含 `id`, `status`, `bookedBy`, `checkInDeadline` | `400 INVALID_DURATION`, `INVALID_TIME_GRANULARITY`, `BOOKING_WINDOW_EXCEEDED`, `OUT_OF_BUSINESS_HOURS`, `START_IN_PAST`, `CAPACITY_EXCEEDED`, `INVALID_ATTENDEES`; `401`; `403 FORBIDDEN`; `409 ROOM_SLOT_CONFLICT` |
| `POST /api/v1/bookings/{id}/check-in` | Path: `id` | `200 BookingResponse`，`status=CHECKED_IN`，`checkedInAt=now` | `401`; `403 FORBIDDEN`; `409 CHECKIN_NOT_OPEN`, `BOOKING_NOT_ACTIVE` |
| `POST /api/v1/bookings/{id}/cancel` | Path: `id` | `200 BookingResponse`，`status=CANCELLED`，`cancelReason=EMPLOYEE` | `401`; `403 FORBIDDEN`; `409 CANNOT_CANCEL_AFTER_START`, `BOOKING_NOT_ACTIVE` |
| `GET /api/v1/bookings/mine` | Query: `from`, `to`, `status` | `200 BookingListResponse`，按 `startAt` 升序，含 `checkInDeadline` | `400 INVALID_DATE_RANGE`; `401` |
| `POST /api/v1/admin/rooms` | Body: `{name, floor, capacity, equipment[]}` | `201 RoomResponse`，`status=ACTIVE` | `400 INVALID_CAPACITY`; `401`; `403 FORBIDDEN`; `409 ROOM_NAME_DUPLICATED` |
| `PATCH /api/v1/admin/rooms/{id}` | Path: `id`; Body: 可选 `{name, floor, capacity, equipment[]}` | `200 RoomResponse` | `400 INVALID_CAPACITY`; `401`; `403`; `409 ROOM_NAME_DUPLICATED` |
| `DELETE /api/v1/admin/rooms/{id}` | Path: `id` | `204 No Content`，`status=DELETED` | `401`; `403`; `409 ROOM_HAS_FUTURE_BOOKINGS`，响应含冲突预订 `id` 与 `startAt` |
| `POST /api/v1/admin/rooms/{roomId}/maintenance` | Path: `roomId`; Body: `{startAt, endAt, reason, force}` | `201 MaintenanceWindowResponse` | `400 INVALID_MAINTENANCE_WINDOW`, `BOOKING_WINDOW_EXCEEDED`, `OUT_OF_BUSINESS_HOURS`, `INVALID_TIME_GRANULARITY`; `401`; `403`; `409 MAINTENANCE_CONFLICT`，响应含 `conflicts[]` |
| `GET /api/v1/admin/reports/utilization` | Query: `from`, `to`, `groupBy=ROOM` | `200 {items[], from, to}`，含 `availableMinutes`, `bookedMinutes`, `usedMinutes`, `bookingRate`, `utilizationRate` | `400 INVALID_DATE_RANGE`, `REPORT_RANGE_TOO_LARGE`; `401`; `403` |
| `GET /api/v1/admin/bookings` | Query: `date` | `200 AdminBookingListResponse`，按 `roomId`, `startAt` 升序 | `401`; `403` |
| `GET /healthz` | 无 | `200` 健康状态 | 无 |
| `GET /metrics` | 无 | `200` Prometheus 文本 | 无 |

## Data flow

### 1. 登录与鉴权

1. 浏览器携带 `Authorization: Bearer <token>` 调用 `/api/v1/me`。
2. FastAPI 依赖调用 `TokenVerifier.verify`，从 JWKS 校验签名与过期时间。
3. 校验通过后构造 `AuthPrincipal(user_id=sub, display_name=name, roles=roles)`，写入请求上下文。
4. 业务层只读取 `AuthPrincipal.roles`，不接触原始令牌。
5. 缺失或过期令牌统一返回 `401 UNAUTHENTICATED`。

### 2. 搜索空闲会议室

1. 前端把日期、开始时间、结束时间、人数、设备提交到 `/api/v1/rooms/available`。
2. `BookingRules.validate_search` 校验时长 15–240 分钟、15 分钟粒度、业务时段与日期范围。
3. `RoomRepository.list_available` 查询 `status=ACTIVE`、容量足够、设备为所需集合超集的房间。
4. 同一 SQL 排除与 `RESERVED` / `CHECKED_IN` 预订及 `ACTIVE` 维护时段重叠的房间，按半开区间判定。
5. 结果按 `capacity` 升序、`id` 升序返回；无结果返回 `items=[]`。

### 3. 创建预订

1. 前端提交 `roomId`、日期、时段、人数、标题。
2. `BookingRules.validate_create` 执行 BR-1 至 BR-5 的全部前置校验，失败返回对应 400。
3. `UnitOfWork` 开启事务，`RoomRepository.get_for_update` 对会议室行加排他锁。
4. `BookingRepository.list_active_overlapping` 与 `MaintenanceRepository.list_active_overlapping` 读取冲突对象。
5. `OverlapPolicy.overlaps` 判定区间是否重叠；重叠则回滚并返回 `409 ROOM_SLOT_CONFLICT`。
6. 不重叠则插入 `Booking(status=RESERVED, booked_by=principal.user_id)`，提交事务。
7. 数据库 GiST 排除约束兜底并发；违反时同样返回 409。
8. 响应返回 `201`、`bookedBy` 与 `checkInDeadline=startAt+15min`。

### 4. 签到

1. 前端调用 `/api/v1/bookings/{id}/check-in`。
2. `BookingRepository.get_for_update` 锁定预订单。
3. 校验调用者为预订人或 `ADMIN`，否则 `403 FORBIDDEN`。
4. 若已是 `CHECKED_IN`，直接返回 200 且不覆盖 `checkedInAt`。
5. 若状态为 `CANCELLED` / `RELEASED` / `COMPLETED`，返回 `409 BOOKING_NOT_ACTIVE`。
6. 若 `now < startAt-15min` 返回 `409 CHECKIN_NOT_OPEN`；若 `now > startAt+15min` 返回 `409 BOOKING_NOT_ACTIVE`。
7. 窗口内更新 `status=CHECKED_IN`、`checked_in_at=now`，提交事务并返回 200。

### 5. 未签到自动释放

1. `Scheduler` 每 60 秒执行 `run_once`，先取 PostgreSQL advisory lock。
2. 查询 `status=RESERVED`、`checked_in_at IS NULL`、`start_at <= now` 的候选预订。
3. 对 `now >= start_at+15min` 的候选，条件更新为 `RELEASED`、`cancel_reason=NO_SHOW`、`released_at=now`。
4. 更新影响行数为 1 时写审计日志并调用 `BookingNotifier.notify_released`。
5. 更新影响行数为 0 时视为重复触发，跳过审计与通知。
6. 同轮把 `status IN (RESERVED, CHECKED_IN)` 且 `end_at <= now` 的预订置为 `COMPLETED`。
7. 释放 advisory lock，等待下一轮。

### 6. 取消自己的预订

1. 前端调用 `/api/v1/bookings/{id}/cancel`。
2. `BookingRepository.get_for_update` 锁定预订单。
3. 调用者不是 `booked_by` 时返回 `403 FORBIDDEN`。
4. 状态不是 `RESERVED` 时返回 `409 BOOKING_NOT_ACTIVE`。
5. `now >= start_at` 时返回 `409 CANNOT_CANCEL_AFTER_START`。
6. 否则更新 `status=CANCELLED`、`cancel_reason=EMPLOYEE`，提交事务，该时段立即退出冲突集合。

### 7. 查看我的预订

1. 前端带 `from`、`to`、可选 `status` 调用 `/api/v1/bookings/mine`。
2. `BookingRules.validate_date_range` 校验 `from <= to`，否则 `400 INVALID_DATE_RANGE`。
3. `BookingRepository.list_mine` 强制使用 `principal.user_id` 过滤，并按 `start_at` 升序。
4. 响应映射为 `BookingResponse`，对每条 `RESERVED` 计算 `checkInDeadline=startAt+15min`。

### 8. 管理员管理会议室

1. 管理员调用 `/api/v1/admin/rooms` 的 POST / PATCH / DELETE。
2. API 先执行 `require_admin`，非 ADMIN 返回 `403 FORBIDDEN`。
3. 创建与修改执行字段校验：名称 1–50、楼层 1–20、容量 1–100、设备枚举白名单。
4. 名称冲突返回 `409 ROOM_NAME_DUPLICATED`。
5. 删除前检查 `start_at > now` 且 `status IN (RESERVED, CHECKED_IN)` 的预订；存在则返回 `409 ROOM_HAS_FUTURE_BOOKINGS`。
6. 创建、修改、软删除均在事务内写 `audit_logs`。

### 9. 设置维护时段

1. 管理员提交 `{startAt, endAt, reason, force}`。
2. `BookingRules.validate_maintenance` 校验 `startAt < endAt`、15 分钟粒度、07:00–22:00、30 天提前期。
3. 锁定会议室行，查询与维护时段重叠的 `RESERVED` / `CHECKED_IN` 预订。
4. `force=false` 且存在冲突时返回 `409 MAINTENANCE_CONFLICT`，响应列出冲突预订。
5. `force=true` 时逐条把冲突预订置为 `CANCELLED`、`cancel_reason=MAINTENANCE`，并写审计。
6. 插入 `MaintenanceWindow(status=ACTIVE)` 并写审计，提交事务；该时段立即从可用搜索中剔除。

### 10. 使用率报表

1. 管理员调用 `/api/v1/admin/reports/utilization`。
2. `BookingRules.validate_report_range` 校验 `from <= to` 且跨度不超过 366 天。
3. `ReportService` 执行聚合 SQL：按每日 07:00–22:00 计算 `available_minutes`，扣除 ACTIVE 维护时段。
4. 同一 SQL 计算 `used_minutes`（CHECKED_IN + COMPLETED）与 `booked_minutes`（RESERVED + CHECKED_IN + COMPLETED）。
5. 比率用 `round(x, 4)` 输出；`available_minutes = 0` 时比率置 0.0。
6. 响应只含房间聚合值与房间信息，不含员工姓名或 `userId`。

### 11. 管理员查看某日全部预订

1. 管理员调用 `/api/v1/admin/bookings?date=YYYY-MM-DD`。
2. `require_admin` 通过后，`AdminBookingService.list_by_date` 查询当天全部预订。
3. 结果按 `room_id`、`start_at` 升序排列。
4. 响应包含 `bookedBy` 与 `status`，不返回其他员工敏感信息。

### 12. 网页端预订全流程

1. 搜索表单提交到可用会议室接口，表格渲染名称、楼层、容量、设备和预订按钮。
2. 点击预订后调用创建预订接口；201 时把返回记录插入“我的预订”列表并显示签到提示。
3. 409 `ROOM_SLOT_CONFLICT` 时显示“该时段已被预订，请重新搜索”，不跳转页面。
4. 点击签到调用签到接口，成功后更新该条状态为 `CHECKED_IN`。
5. 点击取消调用取消接口，成功后从有效列表移除该条。
6. `/admin` 入口根据 `roles` 控制显示；EMPLOYEE 访问时展示 403 页面。

### 13. 预订释放通知

1. 自动释放成功更新状态后，`Scheduler` 调用 `BookingNotifier.notify_released`。
2. 默认 `LoggingNotifier` 检查通知渠道是否配置。
3. 已配置时向通知渠道发送 `BookingReleased` 事件，事件含 `bookingId`、`reason`、`releasedAt`。
4. 未配置时记录 `NOTIFY_SKIPPED`，不影响主事务与预订状态。