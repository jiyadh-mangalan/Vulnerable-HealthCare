## Security Learning Guide for the Healthcare Management System

This document is a **security learning aid**.  
The application code is written with security in mind; this guide describes
**where classes of vulnerabilities could appear in similar systems** and **how to defend against them**.

It is **not** a manual for exploiting systems.

---

### 1. Authentication & Session Management

1. **Weak password policy** – Enforce minimum length, complexity, and reuse rules.
2. **No rate limiting on login** – Add IP/user-based throttling and lockouts.
3. **Brute-forceable usernames/emails** – Return generic error messages and throttle.
4. **Missing MFA** – Support TOTP/SMS/app MFA for privileged roles (admin/doctor).
5. **Long-lived tokens** – Use short-lived access tokens and rotating refresh tokens.
6. **Token storage in insecure locations** – Prefer secure cookies with `HttpOnly` and `Secure` flags.
7. **Predictable session identifiers** – Always use cryptographically strong randomness.
8. **Improper session invalidation on logout** – Revoke tokens / server-side session records.
9. **Missing session timeout / inactivity** – Expire idle sessions and require re-authentication.
10. **Session fixation** – Regenerate tokens/session IDs after login and privilege changes.

### 2. Access Control & Authorization

11. **Broken object-level authorization (IDOR)** – Always validate that the caller is allowed to access a resource by checking owner/role mappings in the database.
12. **Missing checks on nested resources** – Ensure child resources (appointments, invoices) are linked to an entity the user can legitimately access.
13. **Relying solely on client-side role information** – Never trust client-sent role or user IDs; derive from server-side auth context.
14. **Hard-coded admin bypasses** – Avoid magic query parameters or headers that skip checks.
15. **Vertical privilege escalation** – Ensure each endpoint validates allowed roles explicitly.
16. **Horizontal privilege escalation** – Avoid accepting arbitrary `user_id` in requests without ownership checks.
17. **Overly broad “admin” roles** – Use granular permissions and least privilege.
18. **Missing authorization on background jobs** – Validate that scheduled or async jobs execute with scoped, appropriate privileges.
19. **Resource enumeration** – Filter lists to only records belonging to the caller, and avoid disclosing identifiers for others.
20. **Misconfigured CORS** – Avoid `*` on credentials; restrict origins and allowed methods/headers.

### 3. Input Validation & Injection

21. **SQL Injection** – Always use parameterized queries/ORM, never string concatenation with user input.
22. **No server-side validation** – Validate schemas and types on the backend (e.g., Pydantic models).
23. **Hidden field trust** – Ignore any security-sensitive information from hidden form fields.
24. **Mass assignment** – Whitelist allowed fields for updates, avoid direct mapping of all user input to model fields.
25. **Command injection** – Avoid passing user input to shell commands; if needed, use safe APIs and strict validation.
26. **LDAP/NoSQL injection** – Sanitize and parameterize directory or document store queries.
27. **Deserialization of untrusted data** – Avoid pickling/unpickling user input; prefer structured formats with strict schemas.
28. **Improper numeric validation** – Enforce ranges and types; don’t rely on client-side checks.
29. **File path traversal** – Normalize paths and restrict to whitelisted directories for file access.
30. **Improper use of regex (ReDoS)** – Avoid catastrophic backtracking patterns for user-input-driven regexes.

### 4. Cross-Site Scripting (XSS) & Content Handling

31. **Reflected XSS** – Escape and encode all user-provided data in HTML responses.
32. **Stored XSS in notes/comments** – Sanitize rich text fields and/or store in safe subsets (e.g., markdown with whitelist).
33. **DOM-based XSS** – Avoid unsafe `innerHTML`/`eval` in any JavaScript-based UI.
34. **Unescaped data in attributes** – Properly escape attribute contexts (`href`, `src`, `on*` handlers).
35. **Missing Content Security Policy (CSP)** – Add CSP to limit script sources and inline execution.
36. **Unvalidated redirects with unescaped targets** – Validate and encode any redirect URLs.
37. **Untrusted HTML emails** – Sanitize any user-generated content included in HTML emails.
38. **Auto-rendering rich text** – Use libraries that sanitize HTML and block scripts/iframes.

### 5. Cross-Site Request Forgery (CSRF)

39. **Missing CSRF protection on state-changing endpoints** – Use CSRF tokens for cookie-based sessions.
40. **CSRF-exposed payment actions** – Require CSRF tokens and explicit user confirmations for payment steps.
41. **CSRF on profile updates** – Enforce same-site cookies and per-form tokens.
42. **GET requests changing state** – Restrict side effects to `POST/PUT/PATCH/DELETE` only.
43. **Missing SameSite cookie attribute** – Enable `SameSite=Lax` or `Strict` for auth cookies.

### 6. Cryptography & Secrets Management

44. **Hard-coded secrets in source control** – Load keys from environment variables or secret management systems.
45. **Using weak hashing for passwords** – Use strong, adaptive hashing (e.g., bcrypt/argon2).
46. **Reusing symmetric keys across environments** – Separate keys per environment (dev/stage/prod).
47. **Insufficient key rotation** – Plan for and implement key rotation procedures.
48. **Custom crypto algorithms** – Always rely on vetted libraries and standardized algorithms.
49. **Insecure random number generation** – Use cryptographically secure RNG for tokens and identifiers.
50. **Unencrypted sensitive data at rest** – Encrypt particularly sensitive fields (e.g., medical notes) where appropriate.
51. **Lack of TLS/HTTPS** – Enforce HTTPS in production; use HSTS and secure ciphers.
52. **Exposing JWT signing keys** – Keep signing keys in dedicated secret storage; never log or return them.

### 7. Logging, Monitoring, and Error Handling

53. **Sensitive data in logs** – Avoid logging passwords, tokens, full card numbers, or medical content.
54. **Verbose error messages in production** – Return generic errors to clients; log detailed traces server-side only.
55. **Lack of audit logging** – Log security-sensitive actions (logins, role changes, record access).
56. **No alerting on suspicious activity** – Add alerts for repeated login failures, access anomalies, and unusual payment activity.
57. **Log injection** – Sanitize log messages to avoid control characters that could corrupt logs.
58. **Missing correlation IDs** – Add request IDs to trace activity across services.

### 8. Data Protection & Privacy (Healthcare-specific)

59. **Excessive data collection** – Collect only data necessary for care and operations (data minimization).
60. **Unnecessary exposure of PHI in APIs** – Limit fields returned to what’s needed per role and endpoint.
61. **Insecure backups** – Encrypt and protect backup media and storage locations.
62. **Lack of data retention policies** – Define and implement deletion/anonymization rules for old data.
63. **Improper data sharing with third parties** – Validate business/legal need and secure integration; anonymize where possible.
64. **Unprotected exports (CSV/PDF)** – Control access to exports, log their generation, and consider watermarks.
65. **Insecure email notifications** – Avoid including PHI in email content; direct users to secure portals.
66. **Debug data leaks** – Ensure debug endpoints or tools do not expose PHI or internal configuration.

### 9. Business Logic & Workflow Vulnerabilities

67. **Bypassing approval steps** – Enforce state transitions (e.g., from `draft` to `approved`) only via authorized roles.
68. **Double-booking appointments** – Add constraints/checks to avoid overlapping time slots for doctors/resources.
69. **Skipping payment before confirming appointments** – Validate payment status before confirming or delivering services.
70. **Race conditions in state transitions** – Use transactions and state checks to prevent inconsistent states.
71. **Improper fee calculation** – Centralize billing logic; avoid duplicate/contradictory calculations.
72. **Unauthorized discounting or write-offs** – Restrict discount operations to authorized roles and log them.
73. **Refund logic abuse** – Enforce clear rules and authorization for refunds and partial refunds.
74. **Inconsistent cancellation policies** – Ensure fees and refunds follow consistent, validated business rules.
75. **Bypassing consent or authorization checks** – Explicitly model and verify patient consent for particular operations.

### 10. Payment & Financial Flows

76. **Storing raw card numbers** – Use tokenization and never store PANs unless absolutely required and compliant.
77. **Improper handling of payment provider callbacks** – Verify signatures and origins of callbacks/webhooks.
78. **Trusting client-side price calculations** – Recalculate totals server-side based on authoritative data.
79. **Missing currency and rounding handling** – Normalize currency and rounding logic to avoid discrepancies.
80. **Race conditions in charge capture** – Guard against double-charging by checking current invoice/payment status.
81. **Weak reconciliation between provider and internal records** – Periodically reconcile and log discrepancies.
82. **Exposed test payment endpoints in production** – Isolate sandbox and production keys and URLs.
83. **Unvalidated refunds** – Ensure refunds validate original payment and are approved by appropriate roles.

### 11. API Design & Integration

84. **Overly broad APIs leaking internal models** – Use DTO/schemas that only expose necessary fields.
85. **Lack of pagination/limits** – Add pagination to prevent resource exhaustion from large result sets.
86. **Missing input size limits** – Restrict payload sizes to reasonable values.
87. **Inconsistent versioning** – Use API versioning to avoid breaking integrations.
88. **No authentication on internal endpoints** – Secure internal/admin APIs with strong auth and network controls.
89. **Insecure third-party integrations** – Validate and sanitize data coming from external services.
90. **Lack of idempotency on critical endpoints** – Use idempotency keys for payment and booking operations.

### 12. Frontend & UI Security Considerations

91. **Exposing too much state in the client** – Keep sensitive logic on the server.
92. **Client-side trust in role or ownership checks** – Never rely solely on UI to hide forbidden actions.
93. **Insecure local storage usage** – Avoid storing tokens or secrets in local/session storage where possible.
94. **Clickjacking** – Use `X-Frame-Options` / `frame-ancestors` to prevent framing.
95. **Mixed content** – Ensure all assets use HTTPS to avoid downgrade of security.
96. **Autocomplete of sensitive fields** – Use appropriate `autocomplete` attributes on critical inputs.

### 13. Infrastructure, Deployment & Docker

97. **Running containers as root** – Use non-root users inside containers where feasible.
98. **Exposed management ports** – Restrict DB/management ports to internal networks only.
99. **Missing security updates** – Regularly update base images and dependencies.
100. **Unrestricted volume mounts** – Limit mounts to necessary paths and avoid leaking host secrets.
101. **Lack of resource limits** – Use CPU/memory limits to mitigate DoS and runaway processes.
102. **Default credentials on services** – Change default DB/admin credentials and rotate periodically.

### 14. Configuration & Environment Management

103. **Debug mode enabled in production** – Ensure debug flags are off in live environments.
104. **Overly permissive CORS and headers** – Configure only what’s needed per environment.
105. **Misconfigured time zones** – Normalize time handling to avoid logic issues around scheduling.
106. **Inconsistent environment-specific settings** – Validate that dev/test/stage/prod use appropriate URLs and secrets.

### 15. Secure Development Lifecycle

107. **No code review for security-critical changes** – Enforce reviews for auth, payments, and PHI-related code.
108. **Lack of automated security testing** – Integrate SAST/DAST and dependency scanning into CI/CD.
109. **Missing dependency management policies** – Keep dependencies up to date and remove unused ones.
110. **Insufficient documentation of security controls** – Document role models, access rules, and data flows clearly.

---

This list is intentionally focused on **understanding and preventing** security issues in a healthcare management system.  
Use it as a checklist when designing features, writing code, and reviewing deployments.


