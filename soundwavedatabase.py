import sqlite3
with sqlite3.connect('./soundwave.db') as connection:
    cursor = connection.cursor()
    query = '''
    CREATE TABLE IF NOT EXISTS conversations (
                    conversationid INTEGER PRIMARY KEY AUTOINCREMENT,
                    ppt1id TEXT,
                    ppt2id TEXT
    );
    '''

    cursor.execute(query)

    query = '''
    CREATE TABLE IF NOT EXISTS messages (
                messageid INTEGER PRIMARY KEY AUTOINCREMENT,
                conversationid INTEGER,
                senderid TEXT,
                body TEXT
    );
    '''
    cursor.execute(query)

    query = '''
    CREATE TABLE IF NOT EXISTS users (
                userid text UNIQUE NOT NULL,
                password text NOT NULL,
                music text
    );
    '''
    cursor.execute(query)
    connection.commit()


    query = '''
    CREATE TABLE IF NOT EXISTS music (
                musicid INTEGER PRIMARY KEY AUTOINCREMENT,
                pptid text NOT NULL,
                name text NOT NULL,
                link text NOT NULL,
                image text NOT NULL
    );
    '''
    cursor.execute(query)
    connection.commit()

    query = '''
    CREATE TABLE IF NOT EXISTS songs (
                songid INTEGER PRIMARY KEY AUTOINCREMENT,
                pptid text NOT NULL,
                name text NOT NULL,
                artist text NOT NULL,
                type text NOT NULL
    );
    '''
    cursor.execute(query)
    connection.commit()

def add_conversation(ppt1, ppt2):
    results = get_conversations((ppt1,))
    if ppt2 not in results:
        with sqlite3.connect('./soundwave.db') as connection:
            cursor = connection.cursor()
            query = '''
                INSERT INTO conversations (ppt1id, ppt2id)
                VALUES (?,?);
                '''
        cursor.execute(query, (ppt1, ppt2))
        connection.commit()
    else:
        print("Already exists")

def add_message(conversationid, sender, body):
    with sqlite3.connect('./soundwave.db') as connection:
        cursor = connection.cursor()
        query = '''
            INSERT INTO messages (conversationid, senderid, body)
            VALUES (?,?,?);
            '''
        cursor.execute(query, (conversationid, sender, body))
        connection.commit()

def get_conversations(ppt):
    with sqlite3.connect('./soundwave.db') as connection:
        cursor = connection.cursor()
        query = '''
        SELECT ppt1id, ppt2id
        FROM conversations
        WHERE ? IN (ppt1id, ppt2id);
'''
    cursor.execute(query, ppt)
    results = cursor.fetchall()
    newresults = []
    for i in results:
        for j in range (0, 2):
            if i[j] != ppt[0]:
                newresults.append(i[j])
    return(newresults)

def get_messages(ppt1, ppt2):
    with sqlite3.connect('./soundwave.db') as connection:
        cursor = connection.cursor()
        query = '''
        SELECT senderid, body
        FROM messages
        INNER JOIN conversations ON messages.conversationid = conversations.conversationid
        WHERE conversations.ppt1id in (?, ?) AND conversations.ppt2id in (?, ?);
        '''
        cursor.execute(query, (ppt1, ppt2, ppt1, ppt2))
        results = cursor.fetchall()
        return results

def add_user(userid, password):
    with sqlite3.connect('./soundwave.db') as connection:
        cursor = connection.cursor()
        query = '''
        INSERT INTO users (userid, password)
        VALUES (?,?)
'''
        cursor.execute(query, (userid, password))
        connection.commit()

def checklogin(usercheck, passcheck):
    with sqlite3.connect('./soundwave.db') as connection:
        cursor = connection.cursor()
        query = '''
        SELECT * FROM users WHERE userid = ? AND password = ?'''
        cursor.execute(query, (usercheck, passcheck))
        result = cursor.fetchone()
        if result == None:
            return(False)
        else:
            return(True)



def get_conversationid(ppt1, ppt2):
    with sqlite3.connect('./soundwave.db') as connection:
        cursor = connection.cursor()
        query = '''
            SELECT conversationid
            FROM conversations
            WHERE ? IN (ppt1id, ppt2id) AND ? IN (ppt1id, ppt2id);
            '''
        cursor.execute(query, (ppt1, ppt2))
        results = cursor.fetchone()
        return results

def add_music(ppt1, name, link, image):
    with sqlite3.connect('./soundwave.db') as connection:
        cursor = connection.cursor()
        query = '''INSERT INTO music (pptid, name, link, image) VALUES (?, ?, ?, ?)
        '''
        cursor.execute(query, [ppt1, name, link, image])
        results = cursor.fetchall()

def get_music(ppt1):
    with sqlite3.connect('./soundwave.db') as connection:
        cursor = connection.cursor()
        query = '''SELECT name, link, image FROM music WHERE pptid = (?)'''
        cursor.execute(query, [ppt1])
        results = cursor.fetchall()
        return results

def clear_music(ppt1):
    with sqlite3.connect('./soundwave.db') as connection:
        cursor = connection.cursor()
        query = '''DELETE FROM music WHERE pptid = (?)'''
        cursor.execute(query, [ppt1])

def add_curr(curr, ppt1):
    with sqlite3.connect('./soundwave.db') as connection:
        cursor = connection.cursor()
        query = '''
        UPDATE users
        SET music = (?)
        WHERE userid = (?)
'''
        cursor.execute(query, (curr, ppt1))
        connection.commit()


def get_curr(ppt1):
    with sqlite3.connect('./soundwave.db') as connection:
        cursor = connection.cursor()
        query = '''SELECT music FROM users
        WHERE userid = (?)
        '''
        cursor.execute(query, [ppt1])
        results = cursor.fetchall()
        return results

def dowhatever():
    with sqlite3.connect('./soundwave.db') as connection:
        cursor = connection.cursor()
        query = '''DROP TABLE songs
        '''
        cursor.execute(query)
        results = cursor.fetchall()
        print(results)


#add_user("Lucian", "pass123")
#add_user("Isaac", "pass123")
#add_user("Khiemeron", "pass123")
#add_user("Natalie", "pass123")



def add_song(ppt1, name, artist, type):
    with sqlite3.connect('./soundwave.db') as connection:
        cursor = connection.cursor()
        query = '''INSERT INTO songs (pptid, name, artist, type) VALUES (?, ?, ?, ?)
        '''
        cursor.execute(query, [ppt1, name, artist, type])
        results = cursor.fetchall()


def get_song(ppt1, type):
    with sqlite3.connect('./soundwave.db') as connection:
        cursor = connection.cursor()
        query = '''SELECT name, artist FROM songs WHERE pptid = (?) AND type = (?)'''
        cursor.execute(query, [ppt1, type])
        results = cursor.fetchall()
        return results

def clear_song(ppt1):
    with sqlite3.connect('./soundwave.db') as connection:
        cursor = connection.cursor()
        query = '''DELETE FROM songs WHERE pptid = (?)'''
        cursor.execute(query, [ppt1])

def getuser(ppt):
    with sqlite3.connect('./soundwave.db') as connection:
        cursor = connection.cursor()
        query = '''SELECT * FROM users WHERE userid = (?)'''
        cursor.execute(query, [ppt])
        results = cursor.fetchall()
        if len(results) != 0:
            return(True)

