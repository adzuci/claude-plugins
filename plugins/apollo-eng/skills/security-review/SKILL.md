---
name: security-review
description: Perform security audit of Ruby controllers for IDOR vulnerabilities. Activate when user asks for security review, IDOR check, or authorization audit.
---

# Security Review - IDOR

Perform a thorough security audit of Ruby on Rails controller code to identify IDOR (Insecure Direct Object Reference) vulnerabilities.

## When to Activate

- User asks for "security review" or "security audit"
- User mentions "IDOR" or "authorization check"
- User wants to verify controller security

## Audit Focus Areas

### 1. Authorization Checks

For each endpoint where objects are accessed/modified/deleted by ID:

- Locate the authorization check (if any)
- Verify user has permission to access the specific resource
- Verify objects from different teams/accounts cannot be accessed

### 2. Cross-Team Access

Check if any endpoint allows a user to:

- View data belonging to another team or account
- Modify data belonging to another team or account
- Delete data belonging to another team or account

### 3. Authentication Bypass

Check for:

- Endpoints that skip authentication
- Insufficient authorization logic
- Missing `before_action` filters

### 4. Code Investigation

- Trace execution flow of each controller action
- Examine all `authorize` calls and what they check
- Look for `find` without team/account scope restrictions
- Check for missing authorization in any action
- Review related models, policies, and helper methods

## Output Format

### For Each Endpoint

```text
## Endpoint: POST /api/v1/contacts

Authorization: ✅/❌
- Policy: [policy name or "MISSING"]
- Team/account scoping: [present/missing]
- User verification: [present/missing]

Vulnerabilities:
- [Severity: High/Medium/Low] Description
  - Line: X
  - Code: `snippet`
  - Risk: What could happen
  - Fix: Recommended solution
```

### Summary Table

| Endpoint | Auth | Team Scope | IDOR Risk | Severity |
| -------- | ---- | ---------- | --------- | -------- |
| GET /x   | ✅   | ✅         | None      | -        |
| POST /y  | ❌   | ❌         | Yes       | High     |

### Recommended Fixes

For each vulnerability, provide:

- Specific code changes needed
- Example of secure implementation
- Related files that may need updates
