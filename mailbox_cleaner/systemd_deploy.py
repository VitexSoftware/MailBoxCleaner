import os
import shutil
import subprocess
import sys

SERVICE_NAME = 'mailbox-cleaner'
ENV_FILE = os.path.expanduser('~/.config/mailbox-cleaner.env')
SYSTEMD_DIR = os.path.expanduser('~/.config/systemd/user')


def deploy(args):
    _write_env_file(args)
    _write_service_unit()
    _write_timer_unit(args.interval)
    _enable_timer()


def _write_env_file(args):
    os.makedirs(os.path.dirname(ENV_FILE), exist_ok=True)
    # Open with restricted permissions from the start so the password is never world-readable
    fd = os.open(ENV_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        f.write(f'IMAP_HOST={args.host}\n')
        f.write(f'IMAP_PORT={args.port}\n')
        f.write(f'IMAP_USER={args.user}\n')
        f.write(f'IMAP_PASSWORD={args.password}\n')
        f.write(f'IMAP_FOLDER={args.folder}\n')
        f.write(f'IMAP_OLDER_THAN={args.older_than}\n')
        f.write(f'ARCHIVE_NAME={args.archive_name}\n')
        f.write(f'BATCH_SIZE={args.batch_size}\n')
        if args.thunderbird_profile:
            f.write(f'THUNDERBIRD_PROFILE={args.thunderbird_profile}\n')
    print(f'Config written to {ENV_FILE} (mode 600)')


def _write_service_unit():
    os.makedirs(SYSTEMD_DIR, exist_ok=True)
    # Prefer the installed binary; fall back to running the module directly
    binary = shutil.which(SERVICE_NAME) or f'{sys.executable} -m mailbox_cleaner.cli'
    unit = f"""\
[Unit]
Description=MailBoxCleaner — archive old IMAP messages to local mbox
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
EnvironmentFile={ENV_FILE}
ExecStart={binary}
"""
    path = os.path.join(SYSTEMD_DIR, f'{SERVICE_NAME}.service')
    with open(path, 'w') as f:
        f.write(unit)
    print(f'Service unit written to {path}')


def _write_timer_unit(interval):
    unit = f"""\
[Unit]
Description=MailBoxCleaner timer ({interval})

[Timer]
OnCalendar={interval}
Persistent=true

[Install]
WantedBy=timers.target
"""
    path = os.path.join(SYSTEMD_DIR, f'{SERVICE_NAME}.timer')
    with open(path, 'w') as f:
        f.write(unit)
    print(f'Timer unit written to {path}')


def _enable_timer():
    subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
    subprocess.run(
        ['systemctl', '--user', 'enable', '--now', f'{SERVICE_NAME}.timer'],
        check=True,
    )
    result = subprocess.run(
        ['systemctl', '--user', 'status', f'{SERVICE_NAME}.timer'],
        capture_output=True, text=True,
    )
    print(result.stdout.strip())
    print(f'\nTimer enabled. Next run: systemctl --user list-timers {SERVICE_NAME}.timer')
