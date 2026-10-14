## Database Operations

The application uses PostgreSQL as its primary database.

Production database backups run automatically every night
at 2:00 AM UTC.

Backups are retained for 30 days.

If the database becomes unavailable, engineers should first
check the database service status and connection credentials.

Database migrations must be tested in staging before production.