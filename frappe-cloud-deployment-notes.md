# Naqil Backend Hosting Status

## Current verified access

The Naqil Frappe backend is publicly reachable at `https://naqil-api-production.up.railway.app/`.

The public root returned the Frappe login interface, and `GET /api/method/ping` returned HTTP 200 with `{"message":"pong"}` on 16 August 2026. This verifies Railway edge routing, Frappe site resolution, the web process, and the public API route.

| Check | Result | Evidence |
|---|---|---|
| Public Frappe interface | Passed | The public URL opens the Frappe login page. |
| Basic API health | Passed | `GET /api/method/ping` returns HTTP 200 and `{"message":"pong"}`. |
| Clean image build | Passed | GitHub Actions run `31978824140` completed successfully for commit `afdeae4`. |
| Production-ready managed host | Pending | Frappe Cloud requires an activated payment method or credit balance before it permits creation of a bench or site. |

## Production hosting recommendation

Frappe Cloud remains the preferred long-term Frappe-specific hosting path once the account has a funding method or usable credit. It manages Frappe installation, setup, upgrades, monitoring, backups, SSL, and support. The Naqil app already declares its Frappe 15 compatibility in `naqil/pyproject.toml`.

Before moving to Frappe Cloud, connect the Frappe Cloud GitHub App to the private `Panther12321/saudifreight_be` repository. Then create a private bench compatible with Frappe 15, add the `main` branch of Naqil, create the production site, install Naqil, and verify the same `ping` endpoint plus roles, scheduler, file uploads, and CORS from the React frontend.

## References

1. [Frappe Cloud – Hassle-free hosting for Frappe Apps](https://frappe.io/cloud)
2. [Frappe Cloud – How to install a custom app](https://docs.frappe.io/cloud/benches/custom-app)
3. [Frappe Cloud – Attention required in Custom Apps](https://docs.frappe.io/cloud/faq/custom_apps)
