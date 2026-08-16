# Naqil Backend CI Validation

The `Naqil Frappe CI` GitHub Actions workflow is the required release gate for this repository. It runs on every push to `main` and every pull request. It validates the backend contract tests, parses the local Docker Compose topology, builds the production Docker image, and imports the packaged `naqil` module from that image.

This workflow deliberately does **not** create a production site, attach a database, or contact Railway. Those actions require persistent infrastructure and secrets. A deployment may proceed only after the workflow is green, and a hosted environment must then perform the documented site migration against its own MariaDB and Redis services.

The workflow proves that the source tree can produce a Frappe-compatible container image in a clean Docker environment. It replaces the unreliable practice of discovering basic build errors only after a hosting platform has started a deployment.
