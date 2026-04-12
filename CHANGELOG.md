CHANGELOG.md

# [1.0.0] - 12.04.2026

## Added
- **Seller Management:** Implemented full CRUD functionality for sellers to manage product catalogs, including adding, editing, and deleting products.
- **Buyer Experience:** Added core buyer features including product browsing, shopping cart management, and order placement.
- **Authentication System:** Integrated JWT-based authentication and HTTP Bearer schemes to manage seller and buyer roles.
- **Docker Integration:** Containerized the application and configured database volumes for persistent storage.
- **CI/CD Pipeline:** Configured GitHub Actions to enforce quality gates for style (flake8), security (bandit), and test coverage (pytest-cov).

## Quality & Performance

- **Performance Evaluation:** Integrated Locust for performance testing to ensure P95 response times remain under 200ms.
- **Test Suite:** Achieved 80% line coverage across unit and integration tests.
- **E2E Validation:** Automated end-to-end tests covering registration, product management, and order flows.

## Security

- **Vulnerability Scanning:** Integrated Bandit into the pre-commit and pre-merge gates to block high-severity security issues.
