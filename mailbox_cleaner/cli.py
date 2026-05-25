import argparse
import email
import os
import sys

from mailbox_cleaner.imap_client import IMAPClient
from mailbox_cleaner.mbox_writer import append_messages, detect_thunderbird_local_folders
from mailbox_cleaner.systemd_deploy import deploy


def _env(key, default=None):
    return os.environ.get(key, default)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Move old IMAP messages to Thunderbird Local Folders (mbox archive)'
    )
    parser.add_argument('--host', default=_env('IMAP_HOST'),
                        help='IMAP server hostname [env: IMAP_HOST]')
    parser.add_argument('--port', type=int, default=int(_env('IMAP_PORT', '993')),
                        help='IMAP SSL port (default: 993) [env: IMAP_PORT]')
    parser.add_argument('--user', default=_env('IMAP_USER'),
                        help='IMAP username [env: IMAP_USER]')
    parser.add_argument('--password', default=_env('IMAP_PASSWORD'),
                        help='IMAP password [env: IMAP_PASSWORD]')
    parser.add_argument('--folder', default=_env('IMAP_FOLDER', 'INBOX'),
                        help='IMAP folder to archive from (default: INBOX) [env: IMAP_FOLDER]')
    parser.add_argument('--older-than', type=int, default=int(_env('IMAP_OLDER_THAN', '365')),
                        metavar='DAYS',
                        help='Archive messages older than N days (default: 365) [env: IMAP_OLDER_THAN]')
    parser.add_argument('--archive-name', default=_env('ARCHIVE_NAME', 'Archive'),
                        help='Folder name inside Thunderbird Local Folders (default: Archive) [env: ARCHIVE_NAME]')
    parser.add_argument('--thunderbird-profile', default=_env('THUNDERBIRD_PROFILE'),
                        metavar='PATH',
                        help='Path to Thunderbird "Local Folders" directory (auto-detected if omitted)')
    parser.add_argument('--batch-size', type=int, default=int(_env('BATCH_SIZE', '200')),
                        metavar='N',
                        help='Max messages to process per run (default: 200) [env: BATCH_SIZE]')
    parser.add_argument('--dry-run', action='store_true',
                        help='Report what would be archived without making any changes')
    parser.add_argument('--verbose', action='store_true',
                        default=_env('VERBOSE', '').lower() in ('1', 'true', 'yes'),
                        help='Print subject and sender for each archived message [env: VERBOSE]')
    parser.add_argument('--deploy', action='store_true',
                        help='Install a systemd user timer to run automatically on the chosen interval')
    parser.add_argument('--interval', default='daily',
                        metavar='CALENDAR',
                        help='Systemd OnCalendar expression for --deploy '
                             '(default: daily). Examples: weekly, hourly, '
                             '"Mon *-*-* 02:00:00"')

    args = parser.parse_args()

    missing = []
    if not args.host:
        missing.append('--host / IMAP_HOST')
    if not args.user:
        missing.append('--user / IMAP_USER')
    if not args.password:
        missing.append('--password / IMAP_PASSWORD')
    if missing:
        parser.error('Missing required arguments: ' + ', '.join(missing))

    return args


def main():
    args = parse_args()

    if args.deploy:
        deploy(args)
        return

    local_folders = args.thunderbird_profile or detect_thunderbird_local_folders()
    if not local_folders:
        print(
            'ERROR: Thunderbird Local Folders directory not found.\n'
            'Use --thunderbird-profile to specify the path manually.',
            file=sys.stderr,
        )
        sys.exit(1)

    print(f'Connecting to {args.host}:{args.port} as {args.user}...')
    client = IMAPClient(args.host, args.port)
    client.login(args.user, args.password)

    print(f'Searching "{args.folder}" for messages older than {args.older_than} days...')
    uids = client.search_older_than(args.folder, args.older_than)

    if not uids:
        print('No messages found matching the criteria.')
        client.logout()
        return

    batch = uids[:args.batch_size]
    print(f'Found {len(uids)} message(s); processing {len(batch)} (--batch-size={args.batch_size})')

    if args.dry_run:
        print('[DRY RUN] Would archive the following UIDs:')
        for uid in batch:
            print(f'  UID {uid.decode()}')
        client.logout()
        return

    raw_messages = []
    failed_uids = []
    for uid in batch:
        raw = client.fetch_raw(uid)
        if raw is None:
            print(f'  WARNING: could not fetch UID {uid.decode()}, skipping')
            failed_uids.append(uid)
        else:
            if args.verbose:
                msg = email.message_from_bytes(raw)
                print(f'  {msg.get("From", "(no sender)")}  |  {msg.get("Subject", "(no subject)")}')
            raw_messages.append((uid, raw))

    if raw_messages:
        append_messages(local_folders, args.archive_name, [r for _, r in raw_messages])
        for uid, _ in raw_messages:
            client.delete_uid(uid)
        client.expunge()

    client.logout()

    archived = len(raw_messages)
    failed = len(failed_uids)
    print(f'Done: {archived} archived, {failed} failed.')
    if archived:
        print(f'Saved to: {local_folders}/{args.archive_name}')
        if len(uids) > args.batch_size:
            remaining = len(uids) - args.batch_size
            print(f'{remaining} message(s) remain — run again to continue.')
        print('Restart Thunderbird (or right-click folder → Repair) to refresh the index.')


if __name__ == '__main__':
    main()
