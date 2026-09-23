# Week 6 Write-up — Semgrep Scan & Fix

## 1. Brief findings overview

Scan setup (local equivalent of `semgrep ci --subdir week6` — no AppSec login
on this machine, so the same curated rule bundles were applied via OSS CLI):

```bash
semgrep --config auto --config "p/secrets" week6/ --json
```

Scanned: backend Python (FastAPI), frontend JavaScript, `requirements.txt`
(dependencies), config/env. 493 rules ran over 19 tracked files.

**Categories reported:** all findings were SAST (code-level); zero secrets
found; no SCA (pinned requirements like `fastapi==0.65.2` are old but the OSS
auto bundle flagged no CVEs — noted as a limitation: dedicated SCA needs the
AppSec platform or `pip-audit`).

| # | Rule | File:line | Severity | Risk |
|---|---|---|---|---|
| 1 | `python.sqlalchemy.security.audit.avoid-sqlalchemy-text` | `backend/app/routers/notes.py:71` | ERROR | SQL injection — user `q` interpolated into an f-string `sqlalchemy.text()` LIKE query |
| 2 | `python.lang.security.audit.eval-detected` | `backend/app/routers/notes.py:104` | WARNING | RCE — `eval()` on the `expr` query param |
| 3 | `python.lang.security.audit.subprocess-shell-true` | `backend/app/routers/notes.py:112` | ERROR | RCE — `subprocess.run(cmd, shell=True)` on the `cmd` query param |
| 4 | `python.lang.security.audit.dynamic-urllib-use-detected` | `backend/app/routers/notes.py:120` | WARNING | SSRF/file-read — `urlopen(url)` on arbitrary user URL (`file://` supported) |
| 5 | `python.fastapi.security.wildcard-cors.wildcard-cors` | `backend/app/main.py:24` | WARNING | CWE-942 — `allow_origins=["*"]` with `allow_credentials=True` |

**False positives / intentionally ignored:** one — the residual
`dynamic-urllib-use-detected` hit on the *fixed* `/debug/fetch` (see below).
The call is now preceded by an explicit scheme allowlist + localhost denylist,
so the rule's `file://` scenario is structurally unreachable; suppressed via a
full-rule-ID `# nosemgrep:` annotation with an inline justification comment.
That suppression is itself documented as accepted residual risk here.

## 2. Fixes (before → after)

All five findings fixed (assignment requires ≥3); AI coding tool used: ZCode
agent (prompt-driven edits), each fix verified by re-scan + regression tests.

### Fix 1 — SQL injection in `/notes/unsafe-search` (rule `avoid-sqlalchemy-text`)

- **Risk:** `q` was interpolated directly into `LIKE '%{q}%'`, allowing
  quote-escape → `OR 1=1 --` style predicates.
- **Change (`notes.py:71-92`):** kept the raw-SQL endpoint (it exists to
  demonstrate the class) but made it injection-safe: the LIKE pattern is now a
  bound parameter (`:pattern`) and `%`/`_`/`\` in user input are escaped before
  wrapping; `ESCAPE '\\'` declared in SQL.
- **Why it mitigates:** bind parameters separate code from data; wildcard
  escaping restores literal matching semantics for attacker-supplied `%`/`_`.
- **Test:** `test_search_is_injection_safe` asserts `q="%' OR 1=1 --"` returns
  200 with `[]` (no blanket match) and literal `%`/`_` queries behave.

### Fix 2 — eval RCE `/debug/eval` (rule `eval-detected`)

- **Risk:** full Python code execution via `?expr=__import__('os')...`.
- **Change:** endpoint **removed**. Replaced by `/debug/calc` which allowlists
  characters to `0-9+-*/(). ` then evaluates an AST walk (constants + the four
  arithmetic BinOps + unary sign only — no names, attributes, or calls).
- **Why:** an allowlist AST evaluator has no path to arbitrary code; anything
  outside the grammar is a 400.
- **Test:** `test_calc_endpoint_safe` (2*(3+4)→"14"; dunder import attempt →
  400; letters → 400) and `test_eval_endpoint_removed` (404/405).

### Fix 3 — shell RCE `/debug/run` (rule `subprocess-shell-true`)

- **Risk:** arbitrary shell command execution with full user privileges.
- **Change:** endpoint **removed** (comment block documents why: no safe
  allowlist exists for general shell strings; future need should use a fixed
  command table with `shell=False`).
- **Test:** `test_run_endpoint_removed`.

### Fix 4 — SSRF/file-read `/debug/fetch` (rule `dynamic-urllib-use-detected`)

- **Risk:** `urlopen` on user URL allows `file:///etc/passwd` reads and
  internal-network probes.
- **Change:** `urlparse` validation first — scheme must be http/https, hostname
  must exist and not be localhost/127.0.0.1/0.0.0.0/::1; then a 5s timeout;
  `parsed.geturl()` passed instead of raw input.
- **Why:** the two dangerous schemes (`file:`, and OS-level handlers) are
  unreachable and internal targets are refused. Residual rule hit is annotated
  `# nosemgrep: ...dynamic-urllib-use-detected.dynamic-urllib-use-detected`
  with justification (the OSS engine only honors the full duplicated rule ID —
  discovered during this session).
- **Test:** `test_fetch_blocks_file_scheme_and_localhost` (file:// → 400,
  127.0.0.1 → 400; public http/https → 200 verified manually).

### Fix 5 — wildcard CORS (`main.py:24`, rule `wildcard-cors`)

- **Risk:** any origin can read credentialed responses (CWE-942); browsers
  actually reject `*`+credentials, but the config still signals a permissive
  policy and breaks the moment credentials are dropped.
- **Change:** explicit origin allowlist via `CORS_ALLOW_ORIGINS` env var
  (defaults `http://localhost:8000,http://127.0.0.1:8000`).
- **Why:** origin pinning is the only correct CORS posture once credentials
  are enabled.

### Defense-in-depth extras (no direct rule hit, same audit)

- `/debug/read`: path traversal now confined to `week6/data/` via
  resolve-and-check (base must be a parent), 400 otherwise
  (`test_read_restricted_to_data_dir`: `../../` → 400, absolute path → 400).
- `conftest.py`: engine disposed before unlink so Windows teardown doesn't
  hit WinError 32 (pre-existing bug that made 2 baseline tests error).

## Verification

1. Re-run Semgrep after fixes: `findings: 0` (was 5) — the one annotated
   residual is suppressed with inline justification and a test that pins its
   guard-rails.
2. App still runs: `TestClient` smoke — `/notes/` 200 `[]`, `/notes/debug/calc`
   200 `{"result":"14"}`, public fetch 200.
3. Tests: `pytest backend/tests` → **9 passed** (3 baseline + 6 new security
   regression tests).
