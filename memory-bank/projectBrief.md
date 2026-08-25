
## projectBrief.md

```md
# Project Brief

## Project Name

Safe Follow-Up Handling for a Secure Employee RAG System

## What the Project Is

This project is a secure RAG-based conversational system for employees that can understand follow-up questions while preventing users from accessing information they are not permitted to see. It is designed for company-style internal documents and supports shared sessions with different users.

## Target Users

Employees.

## Core Goal

The main goal is to build a RAG system that correctly answers employee questions while maintaining access-control safety, especially when multiple users interact within a shared session.

## V1 Success Criteria

Version 1 is considered complete when it can:

- Implement a working RAG pipeline.
- Retrieve information from generated company-style internal documents.
- Identify users using a user ID.
- Apply role-based access control.
- Support shared sessions containing multiple users.
- Prevent one user from accessing information retrieved for another user when access permissions differ.
- Handle follow-up questions safely.
- Avoid automatically reusing previously retrieved information for another user's follow-up.
- Perform retrieval while respecting the current user's access permissions.
- Return a security-based response when information cannot be answered due to access restrictions.

## Primary Security Requirement

A shared session must not cause information leakage.

The system must identify the current user and apply that user's role and access permissions for each relevant request. Previously retrieved information must not automatically become available to another user.

## Test Data

The project will initially use generated company-style internal documents for testing.

These documents can include different access levels, such as:
- General employee information
- HR-related information
- Restricted information
- Management-related information

## Architecture Scope

The v1 architecture uses a single-agent system.

## Explicitly Out of Scope

The following are not planned for v1:

- Voice input
- File uploads
- Multi-agent algorithms
- Admin dashboard
- Mobile application
- Production deployment

## Not Defined Yet

The following details are intentionally not finalized:

- Exact Groq API model identifier
- Embeddings model
- Testing framework
- Linting tools
- Formatting tools
- Package managers
- Exact Next roadmap priorities
- Later project ideas