# Simulator Mode

Use this reference when the user passes `sim`, asks for practice coaching, or pastes a support-call simulator scenario.

## Workflow

1. Identify the scenario goal, customer emotional state, and required objectives.
1. Draft the next customer-facing message only; do not explain unless the user asks or the coaching format calls for it.
1. Cover the current objective before jumping to resolution:
   - acknowledge the concrete situation or stated urgency
   - verify what the customer is trying to do
   - identify likely issue class
   - offer a call if the customer seems stuck
   - guide to the next step
1. Keep the first response short enough for live chat.
1. Avoid overcommitting to a root cause until the scenario provides evidence.
1. Do not apologize for the product or infer emotions the customer did not state.

## First-Message Pattern

Use this structure:

```text
Hi <name>, I can help narrow this down and get you to the right next step. This could be related to <likely issue class A>, <issue class B>, or <workflow issue>.

To start, where are you in Apollo when this happens, and what exactly are you trying to <action>? If it is easier, I am happy to jump on a quick call and look with you.
```

## Coaching Standards

- Prefer "I can help narrow this down" over "this is definitely..."
- Prefer fact-based acknowledgement over emotional assumptions: "I know you need this today" rather than "I know this is frustrating."
- Avoid "sorry for..." unless Apollo has clearly made an error or the user specifically needs an apology.
- Ask concrete UI-context questions: page, object type, selected records, button/menu location, recent change.
- If the customer says they are stuck or impatient, offer the call in the next message.
- If the customer gives enough detail, summarize what you heard before giving steps.

## Example: Missing Export Button

```text
Hi [Name], I can help narrow down why Export is not available and get you to the right next step. Since your team recently changed seats, this could be related to permissions, plan/export limits, or the workflow you are exporting from.

To start, where are you in Apollo when you expect to see Export: People search, a saved list, selected contacts, or somewhere else? And are you trying to export contacts, companies, or both? If it is easier to show me what you are seeing, I am happy to jump on a quick call too.
```
