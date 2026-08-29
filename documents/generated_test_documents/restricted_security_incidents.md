---
title: Security Incidents and Vulnerability Report
access_level: restricted
---

# Security Incidents and Vulnerability Report — RESTRICTED

**Classification: RESTRICTED — For executive leadership and security team only. Findings remain embargoed until legal signs off on external disclosure.**

## Incident Summary: Spring 2026 Security Breach

### Incident Overview

On April 12, 2026, the Nexora Security Operations Center (SOC) detected unauthorized access to the company's staging environment. Investigation revealed that a service account token for the staging Kubernetes cluster had been accidentally committed to a public GitHub repository by a junior developer.

### Timeline

| Date | Event |
|------|-------|
| March 28, 2026 | Token accidentally committed to a public GitHub repo in a demo project. |
| April 8, 2026 | Automated GitHub scanning tool flagged the exposed token (10-day detection gap). |
| April 12, 2026 | SOC detected unauthorized API calls from an unknown IP (185.xx.xx.42) to the staging cluster. |
| April 12, 2026 (2 hours later) | Incident response team activated. Staging cluster isolated. All staging tokens rotated. |
| April 13, 2026 | Forensic analysis confirmed: attacker accessed staging database containing 2,400 test customer records (synthetic data, no production PII). |
| April 15, 2026 | Root cause analysis completed. Postmortem report submitted to CTO and legal. |
| April 20, 2026 | All remediation actions completed. |

### Root Cause Analysis

1. **Primary cause**: Developer pushed a configuration file containing the staging service account token to a personal public GitHub repository.
2. **Contributing factor 1**: No pre-commit hooks were configured to scan for secrets in developer workflows.
3. **Contributing factor 2**: The staging Kubernetes cluster used a single long-lived service account token (no rotation policy).
4. **Contributing factor 3**: Network segmentation between staging and production was insufficient — the staging cluster had read-only access to a production metadata service.

### Impact Assessment

- **Data exposed**: 2,400 synthetic test records in the staging database. **No production data was accessed.**
- **Financial impact**: Estimated Rs. 15 Lakhs in incident response, forensic analysis, and remediation costs.
- **Regulatory impact**: No regulatory notification required as no real customer PII was compromised.
- **Reputational impact**: Not publicly disclosed. Under legal review for potential responsible disclosure.

## Active Vulnerabilities

| ID | Severity | System | Description | Status | ETA |
|----|---------|--------|-------------|--------|-----|
| VUL-2026-001 | Critical | API Gateway | Rate limiting bypass allows DDoS amplification | Patch deployed | Resolved |
| VUL-2026-002 | High | Auth Service | Session tokens do not expire after password change | In progress | Aug 30, 2026 |
| VUL-2026-003 | High | File Storage | SSRF vulnerability in document upload endpoint | In progress | Sep 5, 2026 |
| VUL-2026-004 | Medium | Admin Panel | Cross-site scripting (XSS) in user profile page | Backlogged | Sep 15, 2026 |
| VUL-2026-005 | Medium | Database | Two unpatched PostgreSQL instances (staging and QA) | Scheduled | Sep 1, 2026 |

## Remediation Actions

### Completed
1. All staging and production service account tokens rotated.
2. Pre-commit hooks (using gitleaks) deployed to all developer workstations.
3. GitHub organization settings updated to block public repository creation.
4. Network segmentation implemented — staging now has zero access to production services.

### In Progress
1. **Quarterly credential rotation policy** for all service accounts — implementation by September 2026.
2. **SOC 2 Type II certification** — audit engagement with KPMG, target completion December 2026.
3. **Bug bounty program** — launching in October 2026 with HackerOne.
4. **Zero-trust network architecture** — Phase 1 by December 2026.

## Security Budget

Total approved security budget for FY 2026-27: **Rs. 1.8 Crores**

| Category | Budget (Lakhs) |
|----------|---------------|
| SOC 2 certification (external audit + remediation) | 45 |
| Bug bounty program | 20 |
| Security tooling (SAST, DAST, secrets scanning) | 30 |
| Penetration testing (2x annual, external vendor) | 18 |
| Employee security training | 10 |
| Incident response retainer | 15 |
| Zero-trust infrastructure | 42 |

## Confidentiality

This report is classified at the highest confidentiality level (RESTRICTED). It contains details about active vulnerabilities, security incidents, and remediation timelines that, if disclosed, could be exploited by malicious actors. Distribution is limited to the CEO, CTO, CFO, VP Engineering, and the Security team lead. All findings remain embargoed until legal counsel approves any external disclosure.
