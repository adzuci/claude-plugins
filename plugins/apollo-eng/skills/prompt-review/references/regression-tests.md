# Regression References

Deterministic findings use stable `prompt-review/<rule>` references. These resolve
to the following executable tests, relative to this skill. Run them with
`python -m pytest plugins/apollo-eng/skills/prompt-review/tests -q` from the repository.

| Finding reference | Executable regression |
| --- | --- |
| `prompt-review/undefined-section` | `tests/test_prompt_review.py::test_missing_step_survives_extraction`; fence controls in `tests/test_protocol_hardening.py` |
| `prompt-review/unavailable-tool` | `tests/test_prompt_review.py::test_tool_contract_failures[tool-unavailable-tool]` |
| `prompt-review/tool-arguments` | `tests/test_prompt_review.py::test_tool_contract_failures[arguments-tool-arguments]` |
| `prompt-review/tool-result-field` | `tests/test_prompt_review.py::test_tool_contract_failures[result-tool-result-field]` |
| `prompt-review/tool-prerequisite` | `tests/test_prompt_review.py::test_tool_contract_failures[prerequisite-tool-prerequisite]` |
| `prompt-review/output-example` | `tests/test_prompt_review.py::test_output_schema_and_missing_schema` |

A semantic review's `regression_test` describes the proposed scenario and expected
behavior unless it cites an existing test. It is not evidence that a new test was
written or run. Before applying a repair, instantiate that scenario against the
changed prompt and preserve the required calls. Keep the executed test or trace
reference with the repair report.
