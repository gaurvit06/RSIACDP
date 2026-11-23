# Local feature walkthrough

On 22 November the signed-in investigator demonstrated consented message and email intake, screenshot and PDF uploads, extraction confirmation, local corpus matching, evidence relevance, timeline events, campaign-link confirmation, graph filtering, human disposition and both report downloads. The checklist below also includes steps awaiting live verification.

To see the updated payment assessment, refresh the desk and search for **RC-4B9B87AC**. Open **DEMO A | Fictional advance-fee offer**. Its current machine finding cites evidence #33 for the registration fee and identifies the matching character range. The earlier human disposition is a separate record. **RC-52084109** is a useful comparison. A shared email can produce a campaign lead even when the message itself gives insufficient evidence for concern. These updated findings were verified in PostgreSQL; a visual check after the rule upgrade is pending.

Open http://localhost:5175 after running `pwsh -File scripts/local.ps1`. Use synthetic demonstration cases and separate demo accounts. Never change existing real cases to demonstrate a feature. Reviewer and investigator actions require the corresponding role; sign in through the application rather than bypassing permissions.

## Suggested synthetic inputs

To demonstrate guided posting intake, open **New case**, choose **Job posting (guided form)** and give the case a synthetic title. Enter **Test manufacturing** for industry, **Pune** for location, and **Contract** for employment type. Review consent, submit, and wait for processing to complete. Open **Submitted job posting** in the case to compare the submitted wording with the extracted fields. Then open **Posting insights**, select **Industry**, choose the **Test manufacturing** bar, and open the case from the results. Confirm the industry extraction in the case to see it under **Confirmed extractions only**. Returning to the insights page refreshes the case list.

Five ready-to-use files are in [demo/](demo/). In **New case**, paste the contents of [the synthetic message](demo/offer-message.txt) under **Message** or open [the synthetic email](demo/offer-email.eml) as text and paste it under **Email**. To demonstrate uploads, attach [the screenshot](demo/offer-screenshot.png), [the text PDF](demo/offer-text.pdf), and [the scanned PDF](demo/offer-scanned.pdf) to separate cases. Each contains `recruiter@walkthrough.invalid`. Compare the extraction locations in all three cases. The searchable PDF contains a text layer. The scanned PDF contains only an image. The fixture check recovered the same address using Tesseract from both image inputs.

Case A, title `DEMO — advance-fee request`:

```text
SYNTHETIC TEST ONLY. Fictional Example Hiring Test Company offers a remote
data-entry role at INR 80000 per month with no interview. Pay INR 4999
within 30 minutes before receiving an offer letter. Contact
recruiter@walkthrough.invalid. Do not contact official HR.
This input is fictional; do not send money or personal information.
```

Case B, title `DEMO — shared recruiter identifier`:

```text
SYNTHETIC TEST ONLY. Fictional Example Hiring Test Company advertises
a warehouse assistant role in Bengaluru. Contact recruiter@walkthrough.invalid
for the details. This fabricated case reuses an identifier for campaign
link testing and makes no allegation about any real person or organization.
```

Case C, title `DEMO — ordinary vacancy without verification`:

```text
SYNTHETIC TEST ONLY. Fictional Example Engineering Test Company offers
a six-month software internship in Bengaluru at INR 25000 per month.
Applicants complete a technical interview and receive written terms.
No recruitment fees are charged. Contact careers@ordinary-vacancy.invalid.
No independent source has verified this fictional vacancy.
```

Unknown identifiers should produce neutral `no_result` checks. Suspicious wording alone does not establish authoritative confirmation; ordinary wording does not establish authenticity. Cases A and B should link through their shared identifier as an investigative lead, even when no adverse external evidence exists.

## Feature demonstration checklist

| Step | Feature and action | What to inspect |
|---|---|---|
| 1 | Sign in; separately demonstrate analyst, investigator and reviewer roles | Role-appropriate navigation/actions; account/session persistence; sign out revokes the session |
| 2 | Open Help and workflow guide | Workflow explanation, named controls, keyboard focus, Escape closes and returns focus |
| 3 | Create Case A as plain text | Consent notice/version, retention explanation, required title/input validation; decline consent prevents submission |
| 4 | Select and redact a harmless test phrase before submitting | Redaction changes submitted text; original private material is not silently retained |
| 5 | Submit Case B as pasted message/email | Queued/running/completed states, persisted case and source spans; no real email is sent |
| 6 | Submit Case C and a `.invalid` job URL as separate cases | URL intake behavior and limitations; failed/unavailable lookup remains neutral |
| 7 | Upload a synthetic image and a PDF, including a scanned PDF | File-size/type validation, private storage, OCR page/image region references; unauthorized access is denied |
| 8 | Open case summary and extracted entities | Raw/normalized values, extraction method, source text/location and uncertainty |
| 9 | Confirm/reject an extraction as investigator | Persisted review status and corresponding audit event; rejected identifiers stop contributing as valid links |
| 10 | Inspect evidence checks; review relevance with a reason | Source name, outcome, timestamp, excerpt, supporting/contradicting claims; empty/errors are not adverse evidence |
| 11 | Open Evidence corpus; add a clearly labelled synthetic source using the authorized role | Exact identifier/claim, source reference, authority and validity; never present fictional evidence as a real government record |
| 12 | Submit a fresh case matching that corpus record | Persisted retrieval result refers to the source; assessment follows the documented rules, not a fabricated classifier probability |
| 13 | Retire the synthetic corpus record | New checks stop treating retired material as active; history remains traceable |
| 14 | Inspect evidence timeline | Ordered intake, processing, checks and review/correction events; retrieval timestamps remain visible |
| 15 | Recompute links and open Campaigns for A/B | Included cases, shared identifiers, versioned reasons/strength, proposed status, investigative-lead wording |
| 16 | Review a proposed link, then reload | Confirm/reject persists; scoring is not a probability or proof of wrongdoing |
| 17 | Open Evidence graph and exercise entity/source/date/review filters | Masked identifiers, inspectable edges and evidence, reset restores the view; no public graph |
| 18 | Download Markdown and JSON reports | Actual case data, redaction, source provenance, rule versions, uncertainty and review actions; export appears in audit history |
| 19 | Submit a correction request; retain its private tracking token | Token-protected status, no unauthorized disclosure; invalid tracking credentials rejected |
| 20 | Investigator applies a correction with rationale | Entities/evidence change, findings and links recalculate, reports reflect the correction, audit history persists |
| 21 | Submit a human disposition, then review from a separate reviewer account | Human disposition stays separate from machine assessment; evidence/rationale requirements and independent review enforced |
| 22 | Reviewer account management on disposable demo accounts only | Account list, deactivation/reactivation, session revocation; password-reset issuance and redemption require a deliberate user handoff for new credentials |
| 23 | Retry processing on an eligible failed synthetic case | Retry status and eventual completion/error; no intentionally corrupted working case data |
| 24 | Narrow the browser window and use keyboard navigation | Intake, lists, graph controls, dialogs and downloads remain usable; no hidden essential controls |
| 25 | Stop and restart with `scripts/local.ps1` | Accounts/cases/uploads persist and all five services become healthy |

Retention/deletion, unsafe URL defenses, encryption, graph outage/fallback and backup/restore are operational features, not all UI buttons. Demonstrate them only in the disposable verification stack, never by expiring or restoring the working database. The existing automated suites exercise these protections; record exact results and exclusions in BUILD_STATUS.md. An optional external source being disabled is a configuration state, not a demonstrated integration. Independent real-world accuracy and the optional LLM/web-search comparison remain outside what synthetic fixtures can prove.

For each live step, record the case reference, role, action, observed result and any fix in the engineering walkthrough. Leave unperformed steps explicitly pending.
