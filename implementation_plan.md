# Implementation Plan

## Overview
Activate and verify durable Supabase persistence for aai-shareChat (Roadmap Next-v2, ADR-0008) using provided credentials, starting with remediation of a service-role key that was committed to `.env.example` and pushed to GitHub. Sessions/messages and the user directory persist across restarts; behavior is unchanged when unconfigured.

## Scope
No feature code changes — the Supabase implementation is already on main. This documents: (0) P0 credential remediation, (1) sanitizing `.env.example`, (2) offline suite, (3) live round-trip + full smoke, (4) optional history scrub decision deferred (rotation already invalidates the leaked key).

## State verified (2026-08-27)
- Supabase reachable: HTTP 200 on `app_users` (seed users present), `sessions` (0), `session_messages` (0).
- `resolve_supabase_client`, `SupabaseSessionStore`, `SupabaseUserDirectory`, deps wiring, and the key-gated integration test all present on main.

## Decisions
- Rotate the exposed service key now; keep the new key only in `.env` (gitignored).
- Commit a blank (sanitized) `.env.example`.
- No new dependency, no schema change, no code change for this activation.

## Steps
1. P0: user rotates the key; new key in `.env`.
2. Commit sanitized `.env.example`.
3. `pytest -q -p no:warnings` (offline) green.
4. `pytest backend/tests/test_integration_supabase.py -v` runs & passes.
5. Live uvicorn smoke: `POST /api/query` and `GET /api/sessions/{id}`.
6. Optional follow-up: scrub leaked key from history + force-push.
