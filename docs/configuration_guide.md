# Configuration guide

| Setting | Where | Default | Notes |
|---|---|---|---|
| Database | env `BATCHGUARD_DB` | `sqlite:///batchguard.sqlite3` | Any SQLAlchemy URL (e.g. PostgreSQL) |
| Session secret | env `BATCHGUARD_SECRET` | dev value | **Must** be set to a random value outside demos |
| Session timeout | `web.py` `max_age` | 15 min | Part 11 automatic logoff |
| Lockout threshold | `services.MAX_FAILED_LOGINS` | 3 | |
| Contemporaneous window | `services.CONTEMPORANEOUS_WINDOW` | 30 min | |
| Role permissions | `services.PERMISSIONS` | see user guide | Change requires re-running OQ |
| Master batch record | `services.seed()` | Paracetamol 500 mg demo, 5 steps | Steps, specs and critical flags |

**Change control:** any change to permissions, specs, time windows or signature rules is a validated-state change.
Update `validation/requirements.yaml` if requirements change, then run `python -m tools.run_validation` and keep the new executed package.
