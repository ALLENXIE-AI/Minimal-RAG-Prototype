## Application Deployment

The production application runs in Docker containers.

The service requires Python 3.12 and must be started with
the production configuration.

The application listens on port 8000.

Before deployment, all automated tests must pass.

Environment variables must be stored outside the source code.
Secrets such as API keys must never be committed to Git.