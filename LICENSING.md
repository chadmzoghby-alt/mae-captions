# Mae Captions Licensing Guide

Mae Captions is source-available software. It is not offered under an OSI-approved open-source license.

The legal terms are the [PolyForm Noncommercial License 1.0.0](LICENSE), together with the [Independent Freelancer Exception](FREELANCER_EXCEPTION.md). This guide explains the intended boundary in plain language; the legal terms control if this summary conflicts with them.

The **Official Repository** is <https://github.com/chadmzoghby-alt/mae-captions>. Its controlling GitHub account is the **Project Contact** for routing inquiries only; that role does not itself identify a rights holder or contracting party. Any separate commercial agreement expressly identifies the applicable rights holder and contracting party.

## At a glance

| Use | Permission |
| --- | --- |
| Personal study, experiments, hobbies, and evaluation without anticipated commercial application | Allowed under the base license |
| Use by qualifying charities, educational institutions, public research, public safety or health, environmental protection, and government institutions | Allowed under the base license |
| One independent freelancer personally producing static caption or localization deliverables for clients | Allowed only within the Freelancer Exception |
| Commercial or business use by a company, employer, agency, partnership, or team | Separate commercial license required, except for the single-person business vehicle allowed by the Freelancer Exception |
| Operating Mae Captions as a hosted service or providing hosted access, SaaS or API access, third-party-operated, continuously running, client-triggered, or customer-facing automation, or customer job submission | Separate commercial license required; see the narrow personally initiated batch allowance below |
| Embedding or incorporating Mae Captions into another commercial product or workflow | Separate commercial license required |
| Selling, renting, white-labeling, or commercially distributing Mae Captions or a modified version | Separate commercial license required |
| Commercial use of a modified version | Separate commercial license required |

## Freelancer boundary

The freelancer permission is deliberately narrow. A single independent professional may personally use an Unmodified Official Copy as a tool and charge for the static files or media work they create. A sole proprietorship or single-member business does not independently receive this permission; it is covered only through its natural-person owner while every condition in the exception is met.

The exception does not cover an agency, a team, employees using it for an employer, subcontractors sharing an installation, or a client-facing system that accepts jobs. It also does not permit selling or providing Mae Captions itself.

The base license separately permits genuine noncommercial purposes and the qualifying organizations it lists. A company's internal evaluation or proof of concept for anticipated business use is not covered unless the company has a commercial license or a separate written evaluation grant.

“Noncommercial purpose” and the qualifying-organization categories come from the base license. Funding alone does not disqualify an organization in a listed category. Nonprofit registration alone does not automatically qualify an organization that is not in a listed category. For people and entities outside those categories, sponsored, monetized, donation-supported, grant-funded, portfolio, mixed-purpose, or future-commercial activity can be fact-specific; obtain written permission before relying on the base license when the use does not clearly fit its text.

The freelancer may personally start a private, non-customer-facing batch script on a controlled local system or cloud virtual machine. Clients may exchange files through email, file transfer, an unconnected upload or download portal, or an unconnected shared drive, but may not trigger Mae Captions or submit jobs to a system connected to it.

## Commercial licenses

A commercial license from the applicable rights holder can authorize company or team use, modifications, redistribution, hosting, embedding, automation, white-labeling, or other negotiated rights it owns or controls. Commercial terms, fees, and the contracting party are set in a separate written agreement.

To request commercial terms, open an issue in the Official Repository titled `Commercial licensing contact request`. Include only your GitHub handle and a request for a private contact channel. Do not post business details, customer information, proposed pricing, or proposed terms. The Project Contact may then provide a private route. No commercial permission exists until a written license has been granted by the applicable rights holder.

## External contributions

The initial alpha does not accept external code, documentation, design, or test contributions. This avoids accepting rights under incomplete or ambiguous terms. If contributions open later, the project will first publish contributor terms that name the legal recipient and grant the rights needed for both source-available and commercial distribution. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Third-party components

Mae Captions' license applies only to rights controlled by its licensors. Dependencies remain under their own terms, listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Provider services and models also have their own terms.

## Package metadata

Python package metadata uses `LicenseRef-Mae-Captions-Source-Available` to identify the combined terms in [LICENSE](LICENSE) and [FREELANCER_EXCEPTION.md](FREELANCER_EXCEPTION.md). Both files are included in source and wheel distributions.
