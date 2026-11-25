# Project status: room-booking

## Measured checks
- PlantUML 语法检查：共 27 张图，检查 27 张，修复前不合法 0 张，修复后不合法 0 张
- 蓝图契约符合度：类图声明 66 个类型，代码中找到 66 个（1.0），缺失：无
- 后端测试（Docker 隔离运行）：passed，退出码 0
- 测试输出末尾：
```
........................................................................ [ 49%]
........................................................................ [ 99%]
.                                                                        [100%]
145 passed in 2.50s

```

## Stage timings
requirement_analysis 88.7s, system_design 40.8s, sprint_planning 78.7s, blueprint_design 174.8s, frontend_design 187.2s, backend_design 578.2s

## Git history of this run
```
62c617a chore: verification results

 verify/backend_tests.log |  4 +++
 verify/quality.json      | 72 ++++++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 76 insertions(+)
163990c feat(backend_design): room-booking

 backend/README.md                                  |  54 ++
 backend/app/__init__.py                            |   5 +
 backend/app/api/__init__.py                        |   5 +
 backend/app/api/deps.py                            | 107 ++++
 backend/app/api/errors.py                          | 101 +++
 backend/app/api/mappers.py                         | 120 ++++
 backend/app/api/routes.py                          | 343 ++++++++++
 backend/app/api/schemas.py                         | 260 ++++++++
 backend/app/clock.py                               |  34 +
 backend/app/config.py                              |  39 ++
 backend/app/domain/__init__.py                     |  41 ++
 backend/app/domain/enums.py                        |  82 +++
 backend/app/domain/errors.py                       |  14 +
 backend/app/domain/interval.py                     |  71 +++
 backend/app/domain/models.py                       | 244 ++++++++
 backend/app/domain/timeutil.py                     | 121 ++++
 backend/app/main.py                                | 135 ++++
 backend/app/metrics.py                             |  49 ++
 backend/app/persistence/__init__.py                |  49 ++
 backend/app/persistence/db.py                      |  57 ++
 backend/app/persistence/ports.py                   | 176 ++++++
 backend/app/persistence/sqlalchemy_repositories.py | 689 +++++++++++++++++++++
 backend/app/persistence/tables.py                  | 164 +++++
 backend/app/services/__init__.py                   |  48 ++
 backend/app/services/admin_booking_service.py      |  23 +
 backend/app/services/audit_service.py              |  45 ++
 backend/app/services/auth.py                       | 143 +++++
 backend/app/services/booking_service.py            | 185 ++++++
 backend/app/services/maintenance_service.py        | 125 ++++
 backend/app/services/notification.py               |  69 +++
 backend/app/services/report_service.py             | 112 ++++
 backend/app/services/room_admin_service.py         | 179 ++++++
 backend/app/services/rules.py                      | 245 ++++++++
 backend/app/services/scheduler.py                  | 149 +++++
 backend/pytest.ini                                 |   6 +
 backend/requirements.txt                           |   9 +
 backend/tests/conftest.py                          | 226 +++++++
 backend/tests/test_admin_bookings.py               |  92 +++
 backend/tests/test_admin_rooms.py                  | 198 ++++++
 backend/tests/test_auto_release.py                 | 231 +++++++
 backend/tests/test_cancel_booking.py               | 154 +++++
 backend/tests/test_check_in.py                     | 192 ++++++
 backend/tests/test_create_booking.py               | 284 +++++++++
 backend/tests/test_domain.py                       | 313 ++++++++++
 backend/tests/test_health.py                       |  22 +
 backend/tests/test_maintenance.py                  | 209 +++++++
 backend/tests/test_me.py                           |  62 ++
 backend/tests/test_my_bookings.py                  | 121 ++++
 backend/tests/test_report.py                       | 157 +++++
 backend/tests/test_search_available.py             | 219 +++++++
 docs/backend_design.md                             |  62 ++
 51 files changed, 6840 insertions(+)
c9299e9 feat(frontend_design): room-booking

 docs/frontend_design.md |  54 ++++
 frontend/README.md      |  92 +++++++
 frontend/admin.html     |  17 ++
 frontend/css/styles.css | 493 ++++++++++++++++++++++++++++++++++
 frontend/index.html     |  17 ++
 frontend/js/admin.js    | 696 ++++++++++++++++++++++++++++++++++++++++++++++++
 frontend/js/api.js      | 206 ++++++++++++++
 frontend/js/app.js      | 591 ++++++++++++++++++++++++++++++++++++++++
 frontend/js/config.js   |  50 ++++
 frontend/js/format.js   | 189 +++++++++++++
 frontend/js/ui.js       |  88 ++++++
 11 files changed, 2493 insertions(+)
cbf0f56 docs(blueprint_design): room-booking

 diagrams/room_booking_class_api.puml               |  197 +++
 diagrams/room_booking_class_domain.puml            |  147 +++
 diagrams/room_booking_class_persistence.puml       |   67 +
 diagrams/room_booking_class_services.puml          |   99 ++
 diagrams/room_booking_er_schema.puml               |   54 +
 diagrams/room_booking_sequence_admin_bookings.puml |   19 +
 diagrams/room_booking_sequence_admin_rooms.puml    |   69 ++
 diagrams/room_booking_sequence_auto_release.puml   |   34 +
 diagrams/room_booking_sequence_cancel_booking.puml |   32 +
 diagrams/room_booking_sequence_check_in.puml       |   38 +
 diagrams/room_booking_sequence_create_booking.puml |   58 +
 diagrams/room_booking_sequence_login_me.puml       |   18 +
 diagrams/room_booking_sequence_maintenance.puml    |   42 +
 diagrams/room_booking_sequence_my_bookings.puml    |   27 +
 diagrams/room_booking_sequence_notification.puml   |   15 +
 .../room_booking_sequence_search_available.puml    |   27 +
 .../room_booking_sequence_utilization_report.puml  |   24 +
 diagrams/room_booking_sequence_web_flow.puml       |   28 +
 diagrams/room_booking_state_booking.puml           |   13 +
 diagrams/room_booking_state_room.puml              |    9 +
 docs/blueprint_design.md                           | 1304 ++++++++++++++++++++
 21 files changed, 2321 insertions(+)
c168793 docs(sprint_planning): room-booking

 diagrams/room_booking_gantt_sprint1.puml |  43 ++++++
 docs/sprint_planning.md                  | 227 +++++++++++++++++++++++++++++++
 2 files changed, 270 insertions(+)
6502a81 docs(system_design): room-booking

 diagrams/room_booking_c4_container.puml |  22 ++++
 diagrams/room_booking_c4_context.puml   |  19 ++++
 docs/system_design.md                   | 180 ++++++++++++++++++++++++++++++++
 3 files changed, 221 insertions(+)
ff0926f docs(requirement_analysis): room-booking

 diagrams/room_booking_activity_auto_release.puml   |  30 ++
 diagrams/room_booking_activity_create_booking.puml |  42 ++
 .../room_booking_activity_maintenance_window.puml  |  36 ++
 diagrams/room_booking_usecase_overview.puml        |  38 ++
 docs/requirement_analysis.md                       | 478 +++++++++++++++++++++
 5 files changed, 624 insertions(+)
f018d8a chore: input

 input.md | 1 +
 1 file changed, 1 insertion(+)
```

## Human review
（无）