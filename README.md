imap-apps-migrator
==================

IMAP4 to Google Apps email migration tool

```
usage: migrate.py [-h] --domain DOMAIN --admin ADMIN [--password PASSWORD]
                  --server SERVER [--user login password username] [--csv CSV]

optional arguments:
  -h, --help            show this help message and exit
  --domain DOMAIN       Google Apps hosted domain name.
  --admin ADMIN         Google Apps domain admin account.
  --password PASSWORD   Password for admin account.
  --server SERVER       IMAP4 server FQDN.
  --user login password username
                        User information for migration; IMAP4 login name,
                        password, Google Apps username
  --csv CSV             Read user information from CSV file.
```

## TODO

 * Process multiple accounts in parallel (multi-thread).
 * Retry if the Google API exceeds the limit.
 * Command line option to set the migration label prefix.
 * Error handling.
