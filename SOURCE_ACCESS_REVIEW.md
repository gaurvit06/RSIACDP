# I4C Suspect Repository access review

**Initial review:** 28 October 2026
**Rechecked:** 3 November 2026
**Scope:** Publicly accessible National Cyber Crime Reporting Portal and Ministry of Home Affairs materials reviewed for this application. This is an implementation access review, not legal advice or written authorization from I4C.

## Finding

The official portal currently documents a citizen-facing Suspect Repository search for identifiers including mobile numbers, email addresses, bank account numbers, UPI IDs, URLs and social media identifiers. The public search pages present a CAPTCHA. The repository page says entries are based on citizen complaints, I4C does not certify their authenticity, the repository is incomplete, errors are possible, and users should exercise discretion. It gives an email channel for corrections. The page still displays `Last Updated: 02/02/2024`; the portal homepage has a newer site-wide update date, which does not establish when the repository data or terms were changed.

The official public pages reviewed do **not** document a machine API for Suspect Search, a developer access process, authentication method, rate limits, bulk-data licence, or permission for automated querying. The current Ministry of Home Affairs annual-report search excerpt mentions API integration with stakeholders and separately describes the citizen Suspect Search feature; it does not identify Suspect Search as an API or grant access. The linked PDF could not be retrieved during this review, so that excerpt is not treated as API-access documentation. The CAPTCHA and citizen-facing search form are not evidence that automated access is authorized. Accordingly, this application does not scrape, automate, bypass the CAPTCHA, or claim a working I4C integration. An operator must obtain written authorization and applicable technical and legal terms before any future automated connector is considered.

The portal's public Website Policies page also states that prior permission is required before other websites or portals direct hyperlinks to the portal. The hosted application does not embed I4C links; obtain permission before adding them. This hyperlinking policy is separate from, and does not establish, API access terms.

## Relevant official material

- [I4C Suspect Search Repository](https://cybercrime.gov.in/Webform/suspect_search_repository.aspx) — public citizen form, identifier categories, CAPTCHA, repository disclaimer, and correction channel. The page states its displayed content was last updated 2 February 2024 when inspected; that page date is not represented as a 2026 repository refresh.
- [I4C Suspect Search for websites/apps](https://cybercrime.gov.in/Webform/suspect_search_websites.aspx) — public form with CAPTCHA and the same complaint-based disclaimer.
- [NCRP portal description of Suspect Repository and Report Suspect](https://cybercrime.gov.in/Default.aspx/Hindi/Defaulthn.aspx) — describes the citizen search and separately the public reporting function.
- [I4C Report Suspect form](https://cybercrime.gov.in/webform/cyber_suspect.aspx) — public reporting workflow also includes a CAPTCHA; reporting is not a machine-readable lookup API.
- [I4C Website Policies](https://cybercrime.gov.in/Webform/Wbsitepolice.aspx) — public policy page states that prior permission is required before external sites link to the portal. This does not document machine/API access.
- [MHA Annual Report 2023–24](https://www.mha.gov.in/sites/default/files/AnnualReport_27122024.pdf) — identifies the repository as one of the NCRP features.
- [MHA Annual Report 2024–25](https://www.mha.gov.in/sites/default/files/AREnglish_24032026.pdf) — a search-indexed extract mentions stakeholder API integrations separately from the citizen Suspect Search feature. The document URL returned an error in this review; do not treat that excerpt as authorization or proof of a Suspect Search API.

## Product and data-handling decisions

1. I4C is represented as a possible source to study, not a configured provider. No network request to I4C is made by the worker or API.
2. Investigators can use the local curated evidence corpus for permitted records and preserve the actual source, record reference, claim, retrieval time and excerpt. The corpus starts empty; an empty corpus produces a neutral `no_result` observation.
3. A copied or manually reviewed I4C result must retain the source URL, retrieval date, the exact result text needed to support the claim, and an authority category that reflects the repository's complaint-based and unverified status. It must not be upgraded to an authoritative confirmation merely because the portal is government-operated.
4. Any future integration requires written authorization, documented terms, an approved lawful basis and retention policy, source-specific rate limits, provenance and correction propagation. Until those prerequisites exist, the operational state remains “not checked via I4C.”
5. A person or identifier appearing in the repository is an investigative lead based on submitted complaints; it is not proof of wrongdoing. Conflicts and the portal's own correction process must remain visible to reviewers.

## Verification limit

The public webpages establish what the citizen-facing feature says and displays. They do not establish that no private or law-enforcement API exists. This review found no publicly documented API or public authorization for automated use, so automated access remains unimplemented and unauthorized unless the operator obtains separate written terms. Recheck the current official pages and obtain written authorization before any future integration or hosted hyperlink is added.

## Recheck on 3 November 2026

The current public repository search result still describes a complaint-based repository, states that I4C does not certify complaint authenticity, warns that entries can be incomplete or erroneous, and provides a correction email. Its displayed repository update date remains 2 February 2024. The website/app suspect-search page also continues to present a citizen form with CAPTCHA. Direct page retrieval exposed no readable API documentation, and the current public portal search did not surface API credentials, developer terms, bulk access, or automation permission. Search/index results are only a public-material recheck; they do not prove that private or law-enforcement interfaces do not exist. The automated connector therefore remains disabled. See the current [Suspect Repository](https://cybercrime.gov.in/Webform/suspect_search_repository.aspx), [website/app suspect search](https://cybercrime.gov.in/Webform/suspect_search_websites.aspx), and [Website Policies](https://cybercrime.gov.in/Webform/Wbsitepolice.aspx) pages before any future access or hyperlink decision.
