from contextlib import contextmanager
import logging
import sqlite3
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

DB_PATH = Path(__file__).resolve().with_name('soundwave.db')
logger = logging.getLogger(__name__)


@contextmanager
def _connect():
    connection = sqlite3.connect(DB_PATH)
    # SQLite foreign-key enforcement is connection-local, so enable it every time.
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def init():
    with _connect() as connection:
        cursor = connection.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
                    conversationid INTEGER PRIMARY KEY AUTOINCREMENT,
                    ppt1id TEXT,
                    ppt2id TEXT
        );
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
                messageid INTEGER PRIMARY KEY AUTOINCREMENT,
                conversationid INTEGER,
                senderid TEXT,
                body TEXT
        );
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
                userid TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                music TEXT
        );
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS music (
                musicid INTEGER PRIMARY KEY AUTOINCREMENT,
                pptid TEXT NOT NULL,
                name TEXT NOT NULL,
                link TEXT NOT NULL,
                image TEXT NOT NULL
        );
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
                songid INTEGER PRIMARY KEY AUTOINCREMENT,
                pptid TEXT NOT NULL,
                name TEXT NOT NULL,
                artist TEXT NOT NULL,
                type TEXT NOT NULL
        );
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        connection.commit()

        cursor.execute("SELECT MAX(version) FROM schema_migrations")
        version = cursor.fetchone()[0] or 0
        if version < 1:
            _migrate_to_version_1(connection)
            version = 1
        if version < 2:
            _migrate_to_version_2(connection)


def _table_exists(connection, table_name):
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone() is not None


def _migrate_to_version_1(connection):
    cursor = connection.cursor()
    users = {
        row[0]
        for row in cursor.execute("SELECT userid FROM users WHERE userid IS NOT NULL")
    }

    legacy_conversations = cursor.execute(
        "SELECT conversationid, ppt1id, ppt2id FROM conversations ORDER BY conversationid"
    ).fetchall()
    conversation_map = {}
    participants_by_id = {}
    canonical_id_by_pair = {}
    dropped_conversations = 0

    cursor.execute('''
        CREATE TABLE conversations_v1 (
            conversationid INTEGER PRIMARY KEY AUTOINCREMENT,
            ppt1id TEXT NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
            ppt2id TEXT NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (ppt1id < ppt2id),
            UNIQUE (ppt1id, ppt2id)
        )
    ''')

    for conversationid, first, second in legacy_conversations:
        if not first or not second or first == second or first not in users or second not in users:
            dropped_conversations += 1
            continue

        # Canonical ordering makes the pair unique regardless of who created it.
        pair = tuple(sorted((first, second)))
        canonical_id = canonical_id_by_pair.get(pair)
        if canonical_id is None:
            cursor.execute(
                '''
                INSERT INTO conversations_v1 (conversationid, ppt1id, ppt2id)
                VALUES (?, ?, ?)
                ''',
                (conversationid, pair[0], pair[1]),
            )
            canonical_id = conversationid
            canonical_id_by_pair[pair] = canonical_id
            participants_by_id[canonical_id] = pair
        # Redirect messages from duplicate legacy conversations to the retained one.
        conversation_map[conversationid] = canonical_id

    cursor.execute('''
        CREATE TABLE messages_v1 (
            messageid INTEGER PRIMARY KEY AUTOINCREMENT,
            conversationid INTEGER NOT NULL REFERENCES conversations_v1(conversationid) ON DELETE CASCADE,
            senderid TEXT NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (length(trim(body)) > 0),
            CHECK (length(body) <= 2000)
        )
    ''')

    dropped_messages = 0
    if _table_exists(connection, "messages"):
        for messageid, old_conversationid, senderid, body in cursor.execute(
            '''
            SELECT messageid, conversationid, senderid, body
            FROM messages
            ORDER BY messageid
            '''
        ).fetchall():
            new_conversationid = conversation_map.get(old_conversationid)
            participants = participants_by_id.get(new_conversationid, ())
            if (
                new_conversationid is None
                or senderid not in participants
                or not isinstance(body, str)
                or not body.strip()
                or len(body) > 2000
            ):
                # Keep only messages that remain valid under the new relationship rules.
                dropped_messages += 1
                continue

            cursor.execute(
                '''
                INSERT INTO messages_v1 (messageid, conversationid, senderid, body)
                VALUES (?, ?, ?, ?)
                ''',
                (messageid, new_conversationid, senderid, body),
            )

    cursor.execute('''
        CREATE TABLE music_v1 (
            musicid INTEGER PRIMARY KEY AUTOINCREMENT,
            pptid TEXT NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
            name TEXT NOT NULL,
            link TEXT NOT NULL,
            image TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE songs_v1 (
            songid INTEGER PRIMARY KEY AUTOINCREMENT,
            pptid TEXT NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
            name TEXT NOT NULL,
            artist TEXT NOT NULL,
            type TEXT NOT NULL
        )
    ''')

    dropped_music = 0
    for row in cursor.execute(
        "SELECT musicid, pptid, name, link, image FROM music ORDER BY musicid"
    ).fetchall():
        if not row[1] or row[1] not in users or any(value is None for value in row[2:]):
            dropped_music += 1
            continue
        cursor.execute(
            "INSERT INTO music_v1 (musicid, pptid, name, link, image) VALUES (?, ?, ?, ?, ?)",
            row,
        )

    dropped_songs = 0
    for row in cursor.execute(
        "SELECT songid, pptid, name, artist, type FROM songs ORDER BY songid"
    ).fetchall():
        if not row[1] or row[1] not in users or any(value is None for value in row[2:]):
            dropped_songs += 1
            continue
        cursor.execute(
            "INSERT INTO songs_v1 (songid, pptid, name, artist, type) VALUES (?, ?, ?, ?, ?)",
            row,
        )

    cursor.execute("DROP TABLE messages")
    cursor.execute("DROP TABLE conversations")
    cursor.execute("DROP TABLE music")
    cursor.execute("DROP TABLE songs")
    cursor.execute("ALTER TABLE conversations_v1 RENAME TO conversations")
    cursor.execute("ALTER TABLE messages_v1 RENAME TO messages")
    cursor.execute("ALTER TABLE music_v1 RENAME TO music")
    cursor.execute("ALTER TABLE songs_v1 RENAME TO songs")

    cursor.execute('''
        CREATE TRIGGER messages_sender_must_be_participant
        BEFORE INSERT ON messages
        WHEN NOT EXISTS (
            SELECT 1
            FROM conversations
            WHERE conversationid = NEW.conversationid
              AND NEW.senderid IN (ppt1id, ppt2id)
        )
        BEGIN
            SELECT RAISE(ABORT, 'message sender must be a conversation participant');
        END
    ''')
    cursor.execute('''
        CREATE TRIGGER messages_sender_must_remain_participant
        BEFORE UPDATE OF conversationid, senderid ON messages
        WHEN NOT EXISTS (
            SELECT 1
            FROM conversations
            WHERE conversationid = NEW.conversationid
              AND NEW.senderid IN (ppt1id, ppt2id)
        )
        BEGIN
            SELECT RAISE(ABORT, 'message sender must be a conversation participant');
        END
    ''')
    cursor.execute("CREATE INDEX messages_conversation_order ON messages (conversationid, messageid)")
    cursor.execute(
        "INSERT INTO schema_migrations (version) VALUES (1)"
    )

    dropped_rows = {
        "conversations": dropped_conversations,
        "messages": dropped_messages,
        "music": dropped_music,
        "songs": dropped_songs,
    }
    for table_name, count in dropped_rows.items():
        if count:
            logger.warning(
                "Database migration removed %d invalid %s row(s)",
                count,
                table_name,
            )


def _migrate_to_version_2(connection):
    # Prevent participant edits from making existing message authors outsiders.
    connection.execute('''
        CREATE TRIGGER conversation_participants_must_match_messages
        BEFORE UPDATE OF ppt1id, ppt2id ON conversations
        WHEN EXISTS (
            SELECT 1
            FROM messages
            WHERE conversationid = OLD.conversationid
              AND senderid NOT IN (NEW.ppt1id, NEW.ppt2id)
        )
        BEGIN
            SELECT RAISE(ABORT, 'conversation participants cannot invalidate existing messages');
        END
    ''')
    connection.execute(
        "INSERT INTO schema_migrations (version) VALUES (2)"
    )


def add_conversation(ppt1, ppt2):
    if not ppt1 or not ppt2 or ppt1 == ppt2:
        return False

    participants = sorted((ppt1, ppt2))
    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            '''
            INSERT OR IGNORE INTO conversations (ppt1id, ppt2id)
            SELECT ?, ?
            WHERE EXISTS (SELECT 1 FROM users WHERE userid = ?)
              AND EXISTS (SELECT 1 FROM users WHERE userid = ?)
            ''',
            (participants[0], participants[1], participants[0], participants[1]),
        )
        connection.commit()
        return cursor.rowcount == 1


def add_message(conversationid, sender, body):
    if (
        not conversationid
        or not sender
        or not isinstance(body, str)
        or not body.strip()
        or len(body) > 2000
    ):
        return False

    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            '''
            INSERT INTO messages (conversationid, senderid, body)
            SELECT ?, ?, ?
            WHERE EXISTS (
                SELECT 1 FROM conversations
                WHERE conversationid = ? AND ? IN (ppt1id, ppt2id)
            )
            ''',
            (conversationid, sender, body.strip(), conversationid, sender),
        )
        connection.commit()
        return cursor.rowcount == 1


def get_conversations(ppt):
    if not ppt:
        return []

    user = ppt[0] if isinstance(ppt, tuple) else ppt
    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            '''
            SELECT ppt1id, ppt2id
            FROM conversations
            WHERE ppt1id = ? OR ppt2id = ?;
            ''',
            (user, user),
        )
        rows = cursor.fetchall()

    results = []
    for row in rows:
        for value in row:
            if value != user:
                results.append(value)

    return list(dict.fromkeys(results))


def get_messages(ppt1, ppt2):
    if not ppt1 or not ppt2:
        return []

    conversation = get_conversationid(ppt1, ppt2)
    if conversation is None:
        return []

    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            '''
            SELECT senderid, body, created_at
            FROM messages
            WHERE conversationid = ?
            ORDER BY messageid;
            ''',
            (conversation[0],),
        )
        return cursor.fetchall()


def add_user(userid, password, music=None):
    if not userid or not password:
        return False

    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            '''
            INSERT OR IGNORE INTO users (userid, password, music)
            VALUES (?, ?, ?)
            ''',
            (userid, generate_password_hash(password), music),
        )
        connection.commit()
        return cursor.rowcount == 1


def checklogin(usercheck, passcheck):
    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            '''
            SELECT password FROM users WHERE userid = ?
            ''',
            (usercheck,),
        )
        result = cursor.fetchone()
        if result is None:
            return False

        stored_password = result[0]
        if stored_password.startswith(("pbkdf2:", "scrypt:")):
            return check_password_hash(stored_password, passcheck)

        if stored_password != passcheck:
            return False

        cursor.execute(
            'UPDATE users SET password = ? WHERE userid = ?',
            (generate_password_hash(passcheck), usercheck),
        )
        connection.commit()
        return True


def get_conversationid(ppt1, ppt2):
    if not ppt1 or not ppt2:
        return None

    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            '''
            SELECT conversationid
            FROM conversations
            WHERE (ppt1id = ? AND ppt2id = ?) OR (ppt1id = ? AND ppt2id = ?)
            ORDER BY conversationid
            LIMIT 1;
            ''',
            (ppt1, ppt2, ppt2, ppt1),
        )
        result = cursor.fetchone()
        return result


def can_access_conversation(userid, conversationid):
    if not userid or not conversationid:
        return False

    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            '''
            SELECT 1
            FROM conversations
            WHERE conversationid = ? AND ? IN (ppt1id, ppt2id)
            ''',
            (conversationid, userid),
        )
        return cursor.fetchone() is not None


def add_music(ppt1, name, link, image):
    if not ppt1 or not name or not link or not image:
        return False

    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            '''INSERT INTO music (pptid, name, link, image) VALUES (?, ?, ?, ?)''',
            (ppt1, name, link, image),
        )
        connection.commit()
    return True


def get_music(ppt1):
    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            '''SELECT name, link, image FROM music WHERE pptid = (?)''',
            (ppt1,),
        )
        return cursor.fetchall()


def clear_music(ppt1):
    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute('''DELETE FROM music WHERE pptid = (?)''', (ppt1,))
        connection.commit()


def add_curr(curr, ppt1):
    if curr is None or not ppt1:
        return False

    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            '''
            UPDATE users
            SET music = (?)
            WHERE userid = (?)
            ''',
            (curr, ppt1),
        )
        connection.commit()
    return True


def get_curr(ppt1):
    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            '''SELECT music FROM users WHERE userid = (?)''',
            (ppt1,),
        )
        return cursor.fetchall()


def add_song(ppt1, name, artist, song_type):
    if not ppt1 or not name or not artist or not song_type:
        return False

    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            '''INSERT INTO songs (pptid, name, artist, type) VALUES (?, ?, ?, ?)''',
            (ppt1, name, artist, song_type),
        )
        connection.commit()
    return True


def get_song(ppt1, song_type):
    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            '''SELECT name, artist FROM songs WHERE pptid = (?) AND type = (?)''',
            (ppt1, song_type),
        )
        return cursor.fetchall()


def clear_song(ppt1):
    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute('''DELETE FROM songs WHERE pptid = (?)''', (ppt1,))
        connection.commit()


def getuser(ppt):
    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute('''SELECT 1 FROM users WHERE userid = (?)''', (ppt,))
        return cursor.fetchone() is not None


def purge():
    with _connect() as connection:
        cursor = connection.cursor()
        for table in ['users', 'songs', 'music', 'messages', 'conversations']:
            cursor.execute(f'''DROP TABLE IF EXISTS {table}''')
        connection.commit()
    init()


init()
