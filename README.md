# Composor

**Composor — effortless orchestration of multi-app Docker Compose projects.**

### Description:

Composor helps you build, manage, and deploy multiple Docker Compose applications from a single Python tool. 
It supports automated environment generation, versioned builds, rollbacks, and orchestration of multiple services.

### Features

- Build multiple applications with Docker images from Git repositories.
- Generate `.env` files automatically for Docker Compose.
- Deploy services using Docker Compose with rollback support.
- Supports multiple Compose YAML files per project.
- Dry-run mode for previewing actions before execution.
- Logging and verbose mode for full transparency.


### Use Case:
Perfect for developers and small teams
managing multiple microservices or applications locally or in staging environments,
without needing a full CI/CD pipeline.

## Requirements

- Python 3.10+  
- Docker & Docker Compose  
- Poetry

---

## Installation

### Using Poetry

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies and activate virtual environment
poetry install
poetry env activate

poetry run build-manager -h
poetry run deploy-manager -h
```