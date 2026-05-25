import email
import glob
import mailbox
import os


def detect_thunderbird_local_folders():
    patterns = [
        os.path.expanduser('~/.thunderbird/*/Mail/Local Folders'),
        os.path.expanduser('~/.thunderbird-esr/*/Mail/Local Folders'),
    ]
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    return None


def append_messages(archive_dir, folder_name, raw_messages):
    os.makedirs(archive_dir, exist_ok=True)
    mbox_path = os.path.join(archive_dir, folder_name)
    mbox = mailbox.mbox(mbox_path, create=True)
    mbox.lock()
    try:
        for raw in raw_messages:
            msg = email.message_from_bytes(raw)
            mbox.add(msg)
        mbox.flush()
    finally:
        mbox.unlock()
        mbox.close()
