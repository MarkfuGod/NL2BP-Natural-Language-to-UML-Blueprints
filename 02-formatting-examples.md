# Formatting Examples
This document provides examples of various diagram types that can be created using PlantUML. Each example includes the basic syntax and structure for creating the diagram.
### **PlantUML Diagram Examples**
1. Sequence Diagram:
```plantuml 
@startuml DiagramName(Don't forget to name it)
participant ParticipantName
ParticipantName -> AnotherParticipant: Message
@enduml
```
```plantuml
@startuml
autoactivate on
alice -> bob : hello
bob -> bob : self call
bill -> bob #005500 : hello from thread 2
bob -> george ** : create
return done in thread 2
return rc
bob -> george !! : delete
return success

@enduml
```

Use `->` for messages, `-->` for dotted arrows, and `<-` or `<--` for reverse arrows.

2. Use Case Diagram:
```plantuml
@startuml
(UseCaseName) as UC
ActorName -- UC
@enduml
```
```plantuml
@startuml
left to right direction
actor Guest as g
package Professional {
  actor Chef as c
  actor "Food Critic" as fc
}
package Restaurant {
  usecase "Eat Food" as UC1
  usecase "Pay for Food" as UC2
  usecase "Drink" as UC3
  usecase "Review" as UC4
}
fc --> UC4
g --> UC1
g --> UC2
g --> UC3
@enduml
```

3. Class Diagram:
```plantuml
@startuml
class ClassName {
  -attribute: Type
  +method(): ReturnType
}
ClassName "1" *-- "many" AnotherClass: relationship
@enduml
```

```plantuml
@startuml
' Class declaration
class ClassName {
  -attribute: Type
  +method(param: Type): ReturnType
}

' Abstract class
abstract AbstractClass

' Interface
interface InterfaceName

' Relationships
ClassName "1" *-- "many" AnotherClass: "relationship description"
InterfaceName <|.. ClassName: "implements"
AbstractClass <|-- ConcreteClass: "extends"

' Packages
package "Package Name" {
  class ClassInPackage
}

' Notes
note right of ClassName
  This is a note about the class
end note

' Visibility modifiers
' + Public
' - Private
' # Protected
' ~ Package private
' * Mandatory (for attributes)
@enduml
```

4. Object Diagram:
```plantuml
@startuml
object ObjectName
ObjectName --> AnotherObject : relationship
@enduml
```
```plantuml
@startuml
object Object01
object Object02
object Object03
object Object04
object Object05
object Object06
object Object07
object Object08

Object01 <|-- Object02
Object03 *-- Object04
Object05 o-- "4" Object06
Object07 .. Object08 : some labels
@enduml

```

5. Activity Diagram (new syntax):
```plantuml
@startuml
start
:Activity Name;
if (condition?) then (yes)
  :Action;
else (no)
  :Another Action;
endif
stop
@enduml
```
```plantuml
@startuml
skinparam colorArrowSeparationSpace 1
start
-[#red;#green;#orange;#blue]->
if(a?)then(yes)
-[#red]->
:activity;
-[#red]->
if(c?)then(yes)
-[#maroon,dashed]->
else(no)
-[#red]->
if(b?)then(yes)
-[#maroon,dashed]->
else(no)
-[#blue,dashed;dotted]->
:do a;
-[#red]->
:do b;
-[#red]->
endif
-[#red;#maroon,dashed]->
endif
-[#red;#maroon,dashed]->
elseif(e?)then(yes)
-[#green]->
if(c?)then(yes)
-[#maroon,dashed]->
else(no)
-[#green]->
if(d?)then(yes)
-[#maroon,dashed]->
else(no)
-[#green]->
:do something; <<continuous>>
-[#green]->
endif
-[#green;#maroon,dashed]->
partition dummy {
:some function;
}
-[#green;#maroon,dashed]->
endif
-[#green;#maroon,dashed]->

elseif(f?)then(yes)
-[#orange]->
:activity; <<continuous>>
-[#orange]->
else(no)
-[#blue,dashed;dotted]->
endif
stop
@enduml
```

6. Component Diagram:
```plantuml
@startuml
[ComponentName] as C
C --> AnotherComponent
@enduml
```

```plantuml
@startuml

package "Some Group" {
  HTTP - [First Component]
  [Another Component]
}

node "Other Groups" {
  FTP - [Second Component]
  [First Component] --> FTP
}

cloud {
  [Example 1]
}


database "MySql" {
  folder "This is my folder" {
    [Folder 3]
  }
  frame "Foo" {
    [Frame 4]
  }
}


[Another Component] --> [Example 1]
[Example 1] --> [Folder 3]
[Folder 3] --> [Frame 4]

@enduml
```

7. Deployment Diagram:
```plantuml
@startuml
node NodeName {
  component ComponentName
}
NodeName -- AnotherNode
@enduml
```
```plantuml
@startuml
action action
actor actor
actor/ "actor/"
agent agent
artifact artifact
boundary boundary
card card
circle circle
cloud cloud
collections collections
component component
control control
database database
entity entity
file file
folder folder
frame frame
hexagon hexagon
interface interface
label label
node node
package package
person person
process process
queue queue
rectangle rectangle
stack stack
storage storage
usecase usecase
usecase/ "usecase/"
@enduml
```

8. State Diagram:
```plantuml
@startuml
[*] --> State1
State1 --> State2 : Event
State2 --> [*]
@enduml
```
```plantuml
@startuml
scale 600 width

[*] -> State1
State1 --> State2 : Succeeded
State1 --> [*] : Aborted
State2 --> State3 : Succeeded
State2 --> [*] : Aborted
state State3 {
  state "Accumulate Enough Data\nLong State Name" as long1
  long1 : Just a test
  [*] --> long1
  long1 --> long1 : New Data
  long1 --> ProcessData : Enough Data
}
State3 --> State3 : Failed
State3 --> [*] : Succeeded / Save Result
State3 --> [*] : Aborted

@enduml
```

9. Timing Diagram:
```plantuml
@startuml
robust "Element" as E
E is idle
E is processing
E is done
@enduml
```

10.  JSON Data:
```plantuml
@startjson
{
  "key": "value"
}
@endjson
```

11.  YAML Data:
```plantuml
@startyaml
key: value
@endyaml
```

12.  Network Diagram (nwdiag):
```plantuml
@startuml
nwdiag {
  network NetworkName {
    address = "IP Address"
    element [address = "Specific IP"];
  }
}
@enduml
```

13.  Wireframe Graphical Interface (SALT):
```plantuml
@startsalt
{+
  Button Label | Field Name
}
@endsalt
```

14.  Archimate Diagram:
```plantuml
@startuml
archimate #Business "Label" as Element
Element -> AnotherElement
@enduml
```
15.  Ditaa Diagram:
```plantuml
@startditaa
+--------+        +--------+
|        |        |        |
|  Box1  +------->+  Box2  |
|        |        |        |
+--------+        +--------+
@endditaa
```

16.  Gantt Diagram:
```plantuml
@startgantt
Project starts 2020-07-01
[Prototype design] starts 2020-07-01
[Test prototype] starts 2020-07-16
[Prototype design] ends 2020-07-15
[Test prototype] ends 2020-07-25

@endgantt
```

17.  MindMap Diagram:
```plantuml
@startmindmap
* Central Idea
** Branch1
*** SubBranch1
** Branch2
@endmindmap
```

18.  Work Breakdown Structure (WBS):
```plantuml
@startwbs
* Project
** Task1
*** Subtask1
** Task2
@endwbs
```

19.  Entity Relationship Diagram:
```plantuml
@startuml
entity EntityName {
  * PrimaryKey
  attribute: Type
}
EntityName }|..|| AnotherEntity
@enduml
```

For all diagrams, you can use:
- `skinparam` to customize colors and fonts
- Comments with `'` or `/' ... '/`
- Notes with `note left`, `note right`, etc.
- Titles with `title TitleText`
- Legends with `legend` and `endlegend`

Remember that these are just basic examples. Each diagram type has more advanced features and options available in [PlantUML](www.plantuml.com).
