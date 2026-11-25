# Blueprint role at a glance

| | |
|---|---|
| Input | `requirements.md`, `architecture.md` |
| Output | `blueprint.md` + `diagrams/*.puml` |
| Contract | class diagrams declare every type the code must implement |
| Done when | `nl2bp_check.py validate` → 0 invalid; `contract` → non-empty |
| Next | `coder` |

The full instructions are in
[`role_prompts/rules-blueprintdesign/01-general-guide.md`](../role_prompts/rules-blueprintdesign/01-general-guide.md);
diagram choice and syntax live in the skill: [`skills/nl2bp/references/`](../../skills/nl2bp/references/).
The diagram `BlueprintWirter_Profile.drawio.svg` shows the role's place in the 2025 version of the workflow.
