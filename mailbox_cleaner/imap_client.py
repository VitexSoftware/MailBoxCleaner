import datetime
import imaplib


class IMAPClient:
    def __init__(self, host, port=993):
        self.conn = imaplib.IMAP4_SSL(host, port)

    def login(self, user, password):
        self.conn.login(user, password)

    def logout(self):
        try:
            self.conn.close()
        except Exception:
            pass
        self.conn.logout()

    def search_older_than(self, folder, days):
        self.conn.select(folder, readonly=False)
        cutoff = datetime.date.today() - datetime.timedelta(days=days)
        date_str = cutoff.strftime('%d-%b-%Y')
        typ, data = self.conn.uid('SEARCH', None, f'BEFORE {date_str}')
        if typ != 'OK' or not data[0]:
            return []
        return data[0].split()

    def fetch_raw(self, uid):
        typ, data = self.conn.uid('FETCH', uid, '(RFC822)')
        if typ != 'OK' or not data or data[0] is None:
            return None
        return data[0][1]

    def delete_uid(self, uid):
        self.conn.uid('STORE', uid, '+FLAGS', r'(\Deleted)')

    def expunge(self):
        self.conn.expunge()
