# MailBoxCleaner

Move old IMAP messages to Thunderbird Local Folders (mbox archive) to free server storage quota.

## Usage

```
mailbox-cleaner --host imap.example.com --user you@example.com --password secret \
                [--folder INBOX] [--older-than 365] [--archive-name Archive] \
                [--batch-size 200] [--dry-run]
```

All options can also be set via environment variables:

| Option | Env var | Default |
|---|---|---|
| `--host` | `IMAP_HOST` | *(required)* |
| `--port` | `IMAP_PORT` | `993` |
| `--user` | `IMAP_USER` | *(required)* |
| `--password` | `IMAP_PASSWORD` | *(required)* |
| `--folder` | `IMAP_FOLDER` | `INBOX` |
| `--older-than` | `IMAP_OLDER_THAN` | `365` |
| `--archive-name` | `ARCHIVE_NAME` | `Archive` |
| `--thunderbird-profile` | `THUNDERBIRD_PROFILE` | *(auto-detected)* |
| `--batch-size` | `BATCH_SIZE` | `200` |

Use `--dry-run` to preview which messages would be archived without making any changes.

## What it does

1. Connects to IMAP over SSL
2. Searches the specified folder for messages older than `--older-than` days
3. Downloads up to `--batch-size` messages and appends them to an mbox file inside Thunderbird's **Local Folders**
4. Marks the originals as deleted and expunges them from the IMAP server
5. Prints a summary

Run again to process the next batch. After archiving, restart Thunderbird (or right-click the folder → **Repair Folder**) to rebuild the index.

## Installation

```bash
sudo dpkg -i mailbox-cleaner_*.deb
```

## Building the Debian package

```bash
dpkg-buildpackage -us -uc -b
```
