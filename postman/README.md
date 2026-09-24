# Postman API regression suite

`BatchGuard.postman_collection.json` (14 requests, 24 assertions): auth, role permissions, input validation,
out-of-spec deviation, no double entry, ALCOA+ report, audit-trail integrity. Import it and
`local.postman_environment.json` into Postman, or run headless with Newman:

```bash
uvicorn batchguard.web:app --port 8600
cd postman
npm install
npx newman run BatchGuard.postman_collection.json -e local.postman_environment.json
```
Last run: 14/14 requests, 24/24 assertions passed (`newman_last_run.json`).
