# P16 — Safe Follow-Up Handling and Cross-User Safety

You are working on my existing Secure Employee RAG project.
The only functionality to implement or verify is:

1. Safe Follow-Up Handling
2. Safe handling of shared sessions between different users

---

# Overall Goal

The system should behave like a normal conversational RAG system for the same user while ensuring that information, retrieved chunks, permissions, or context from one user are never incorrectly exposed to another user.

The key principle is:

> Conversation context may be used to understand what a follow-up question refers to, but the previous user's permissions and retrieved documents must never be inherited by the current user.

---

# Phase 1 — Audit Existing Follow-Up Handling ✅ COMPLETED

Before changing anything, inspect the existing code.

Determine:

- Whether follow-up questions are currently detected.
- Whether an `is_followup` mechanism already exists.
- Whether follow-up questions are rewritten into standalone questions.
- How conversation history is currently passed to the LLM.
- Whether previous retrieved chunks are being passed into the next request.
- How the current `user_id`, `role`, and `session_id` are handled.
- Whether the current implementation already supports multiple users in the same session.

Do NOT modify code during this phase.

Classify every relevant part as:

    IMPLEMENTED
    PARTIALLY IMPLEMENTED
    MISSING
    POTENTIALLY UNSAFE

For every finding, identify the relevant file, class, function, or endpoint.

---

# Phase 2 — Implement / Fix Follow-Up Detection ✅ COMPLETED

The system must determine whether the current question depends on previous conversation context.

Example of a new question:

    User:
    "What is the leave policy?"

Expected:

    is_followup = false

Example of a follow-up:

    Previous:
    "How many paid leave days do employees receive?"

    Current:
    "How many can I carry forward?"

Expected:

    is_followup = true

The system should NOT treat every question as a follow-up merely because conversation history exists.

Keep follow-up detection isolated and independently testable.

Do not modify the existing RAG pipeline unnecessarily.

---

# Phase 3 — Implement / Fix Standalone Question Rewriting ✅ COMPLETED

When:

    is_followup = true

rewrite the current question into a standalone query that can be passed to the existing RAG pipeline.

Example:

    Previous:
    "How many paid leave days do employees receive?"

    Current:
    "How many can I carry forward?"

Expected rewritten question:

    "How many unused paid leave days can an employee carry forward?"

The rewriting step must ONLY rewrite the question.

It must NOT:

- Answer the question.
- Retrieve documents.
- Decide whether the user is authorized.
- Invent facts.
- Add information that is not supported by the conversation context.

The output must preserve the intent of the original follow-up.

---

# Phase 4 — Limit Follow-Up Context ✅ COMPLETED

Follow-up processing must use limited conversation history.

Use the P16 requirement of a two-turn history cap.

The system should NOT continuously pass the complete conversation history to the follow-up-processing logic.

Keep these concepts strictly separate:

    Conversation Context
            !=
    Retrieved Documents

Conversation context is used to understand references such as:

    "it"
    "that"
    "the previous policy"
    "what about the previous quarter?"
    "how many can I carry forward?"

Retrieved documents are evidence used by the existing RAG pipeline.

Do not treat retrieved documents as conversation history.

Do not treat conversation history as authorization.

---

# Phase 5 — Verify Per-Turn User Identity ✅ COMPLETED

Every relevant conversation turn must preserve the identity of the current user.

The system should be able to associate each turn with:

    user_id
    role
    session_id
    message

Example:

    Turn 1
    user_id = EMP001
    role = employee

    Turn 2
    user_id = EMP001
    role = employee

    Turn 3
    user_id = MGR001
    role = manager

    Turn 4
    user_id = EMP001
    role = employee

A shared session must NOT be treated as belonging to one permanent user.

The current user's identity must always come from the current request/session state and must not accidentally be inherited from the previous turn.

Verify that changing users inside the same session does not overwrite or confuse the identity of previous turns.

---

# Phase 6 — Prevent Previous User Context Leakage ✅ COMPLETED

This is the most important phase.

Verify that a user's retrieved documents are never automatically reused for another user.

Example:

    User A
    ID = MGR001
    Role = manager

    Question:
    "What is the Engineering team's performance?"

User A is authorized.

The RAG system retrieves:

    Engineering Performance Report

Now the SAME session is used by:

    User B
    ID = EMP001
    Role = employee

User B asks:

    "What about the previous quarter?"

The system MAY use the conversation context to understand that this refers to Engineering performance.

However, it MUST NOT:

- Reuse User A's retrieved chunks automatically.
- Reuse User A's permissions.
- Assume User B has User A's access.
- Treat User A's answer as evidence available to User B.
- Answer from restricted information simply because it appeared earlier in the shared conversation.

Instead, the processing must conceptually be:

    User B
       ↓
    Detect follow-up
       ↓
    Rewrite question
       ↓
    Identify current user
       ↓
    Apply current user's role/access
       ↓
    Perform fresh retrieval
       ↓
    Return only authorized information
       ↓
    Generate answer using authorized evidence

This distinction is mandatory.

---

# Phase 7 — Verify Same-User Follow-Up ✅ COMPLETED

Test a normal follow-up for the SAME user.

Example:

    User:
    EMP001

    Question 1:
    "How many paid leave days do employees receive?"

Expected answer:

    "Employees receive 24 paid leave days."

Then:

    Question 2:
    "How many can I carry forward?"

Expected processing:

    is_followup = true

Rewrite to:

    "How many unused paid leave days can an employee carry forward?"

Then:

    Fresh retrieval
            ↓
    Using EMP001's permissions
            ↓
    Answer

Expected answer:

    "Up to 10 unused paid leave days may be carried forward."

Verify that the system behaves naturally for the same user.

---

# Phase 8 — Verify Different Users in the Same Session ✅ COMPLETED

Create a test involving multiple users sharing the SAME session.

Example:

    session_id = SESSION001

## User A

    user_id = MGR001
    role = manager

Question:

    "What is the Engineering team's performance?"

The manager is authorized.

The system retrieves the appropriate document.

## User B

Same session:

    user_id = EMP001
    role = employee

Question:

    "What about the previous quarter?"

Expected behavior:

1. Detect that the question is a follow-up.
2. Use permitted conversation context to understand the reference.
3. Rewrite the follow-up into a standalone question if required.
4. Identify the CURRENT user as EMP001.
5. Apply Employee permissions.
6. Perform fresh retrieval.
7. Do not use MGR001's previously retrieved chunks as evidence.
8. Do not inherit MGR001's permissions.
9. If the information is not accessible, return:

    This information is not answerable due to security reasons.

---

# Phase 9 — Test Direct Unauthorized Questions ✅ COMPLETED

The safety mechanism must also work when the question is NOT a follow-up.

Example:

    User:
    EMP001

    Role:
    employee

    Question:
    "Show me the confidential management financial report."

Expected result:

    This information is not answerable due to security reasons.

The system must not expose:

- Restricted document content.
- Restricted document names when those names themselves are sensitive.
- Restricted metadata.
- Another user's retrieved information.
- Another user's answer.

This test confirms that access control is not dependent only on follow-up detection.

---

# Phase 10 — Test the Critical Cross-User Attack Scenario ✅ COMPLETED

Create a test specifically designed to catch accidental reuse of previous retrieved chunks.

## Step 1 — Authorized User

    User:
    MGR001

    Role:
    manager

Ask a question that retrieves restricted information.

The test should confirm that the manager can receive the authorized result.

## Step 2 — Switch User

Keep the SAME session.

Switch to:

    User:
    EMP001

    Role:
    employee

## Step 3 — Ask a Follow-Up

Example:

    "What was the number last quarter?"

Expected behavior:

- The system may understand what "the number" refers to.
- The system must identify EMP001 as the current user.
- The system must apply EMP001's permissions.
- The system must perform fresh retrieval.
- The system must NOT use MGR001's retrieved chunks as authorized evidence.
- The system must NOT inherit MGR001's permissions.

The test MUST fail if EMP001 receives restricted information simply because MGR001 retrieved it earlier.

---

# Phase 11 — Verify Data Separation ✅ COMPLETED

Inspect the data flow and ensure the following concepts remain separate.

    Conversation History
        |
        +-- Used to understand follow-up meaning


    Retrieved Chunks
        |
        +-- Created by current user's authorized retrieval


    User Identity
        |
        +-- Current user_id + current role


    Session
        |
        +-- Shared conversation container

The implementation must NOT:

- Treat a session as belonging to one permanent user.
- Treat conversation history as authorization.
- Treat previous retrieved chunks as automatically valid evidence.
- Treat a previous user's permissions as valid for the current user.

The same session can contain multiple users.

---

# Phase 12 — Add Focused Tests ✅ COMPLETED

Add or update tests only for the P16 functionality.

Required tests:

    test_new_question_not_followup

    test_followup_detected

    test_followup_rewritten

    test_followup_uses_limited_history

    test_user_identity_preserved_per_turn

    test_same_user_followup

    test_shared_session_multiple_users

    test_previous_user_retrieval_not_reused

    test_previous_user_permissions_not_inherited

    test_unauthorized_followup_declined

    test_direct_unauthorized_question_declined

Use the existing test framework in the project if one already exists.

Do not introduce unnecessary frameworks or dependencies.

Each test should verify one focused behavior where possible.

---

# Phase 13 — Final Verification ✅ COMPLETED

After implementation, run the complete focused test suite.

Report:

    Follow-up Detection: PASS/FAIL
    Standalone Rewriting: PASS/FAIL
    Limited History: PASS/FAIL
    Per-Turn User Identity: PASS/FAIL
    Same-User Follow-Up: PASS/FAIL
    Shared Session Handling: PASS/FAIL
    Cross-User Retrieval Isolation: PASS/FAIL
    Permission Isolation: PASS/FAIL
    Unauthorized Follow-Up: PASS/FAIL
    Direct Unauthorized Query: PASS/FAIL

Only mark a requirement as PASS if it has actually been verified by tests.

---

# Implementation Order

Follow the phases in this exact order:

    Phase 1
    Audit Existing Follow-Up Handling
            ↓
    Phase 2
    Follow-Up Detection
            ↓
    Phase 3
    Standalone Question Rewriting
            ↓
    Phase 4
    Limited Follow-Up Context
            ↓
    Phase 5
    Per-Turn User Identity
            ↓
    Phase 6
    Prevent Previous User Context Leakage
            ↓
    Phase 7
    Same-User Follow-Up Test
            ↓
    Phase 8
    Different Users in Same Session Test
            ↓
    Phase 9
    Direct Unauthorized Query Test
            ↓
    Phase 10
    Critical Cross-User Attack Test
            ↓
    Phase 11
    Verify Data Separation
            ↓
    Phase 12
    Add Focused Tests
            ↓
    Phase 13
    Final Verification

Do not jump directly to later implementation phases before understanding the current code.

After each phase:

1. Make the smallest required change.
2. Run the relevant tests.
3. Confirm the behavior.
4. Only then continue to the next phase.

---

# Important Constraints

- Do NOT rebuild the RAG pipeline.
- Do NOT rebuild ChromaDB integration.
- Do NOT rebuild the existing frontend.
- Do NOT add authentication.
- Do NOT create a multi-agent system.
- Do NOT add unrelated features.
- Reuse the existing RAG retrieval pipeline.
- Make the smallest necessary code changes.
- Implement one phase at a time.
- Test each phase before moving to the next.
- Never let the LLM be the final authority for authorization.
- Never automatically reuse another user's retrieved chunks.
- Never automatically inherit another user's permissions.
- Conversation context can help understand a follow-up, but authorization must always be evaluated for the current user.
- Never hardcode API keys or credentials.
- Do not claim a security requirement is satisfied without a test demonstrating it.

---

# Final Deliverable

At the end, provide:

## Files Changed

List every file changed and why it was changed.

## Already Implemented

List the P16 requirements that were already present.

## Added or Fixed

List the functionality that was added or corrected.

## Tests Added / Modified

List all relevant tests.

## Test Results

Provide the final PASS/FAIL status for each required behavior.

## Remaining Risks

List any remaining risks specifically related to:

- Follow-up handling
- Shared sessions
- Cross-user context leakage
- Retrieval leakage
- Permission inheritance
- User identity handling

Do not report unrelated project issues.