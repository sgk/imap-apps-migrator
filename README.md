imap-apps-migrator
==================

IMAP4 to Google Apps email migration tool

```
usage: migrate.py [-h] [--domain DOMAIN] [--admin ADMIN] [--password PASSWORD]
                  --server SERVER [--label LABEL]
                  [--user login password username] [--csv CSV] [--dry-run]

IMAP4 to Google Apps email migration tool.

optional arguments:
  -h, --help            show this help message and exit
  --domain DOMAIN       Google Apps hosted domain name.
  --admin ADMIN         Google Apps domain admin account.
  --password PASSWORD   Password for admin account.
  --server SERVER       IMAP4 server hostname.
  --label LABEL         Label for migrated messages if no "/label" for
                        username.
  --user login password username
                        User information for migration; IMAP4 login name,
                        password, Google Apps username. Username can have
                        "/label" suffix to set the label to migrated messages.
  --csv CSV             Read user information from CSV file.
  --dry-run             Only check IMAP server, no message will be migrated.

Dry run if domain or admin is not given.
```

## TODO

 * Process multiple accounts in parallel (multi-thread).
 * Retry if the Google API exceeds the limit.
 * Error handling.
