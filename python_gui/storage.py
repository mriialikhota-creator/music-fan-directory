import sqlite3
from typing import List
from models import Song, RockSong, PopSong, ClassicalSong, Album, Artist, Fan

DB_PATH = "musicfan_db.sqlite"

def get_conn(path=DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path=DB_PATH):
    conn = get_conn(path)
    cur = conn.cursor()

    # Таблиця Артистів (Країна, Жанр)
    cur.execute("""CREATE TABLE IF NOT EXISTS artists (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT NOT NULL UNIQUE, 
        genre TEXT, 
        country TEXT
    )""")

    # Таблиця Альбомів (Додано user_rating)
    cur.execute("""CREATE TABLE IF NOT EXISTS albums (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        title TEXT NOT NULL, 
        artist TEXT, 
        year INTEGER, 
        rating REAL,
        user_rating REAL DEFAULT 0.0
    )""")

    cur.execute(
        """CREATE TABLE IF NOT EXISTS songs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, artist TEXT, duration_sec INTEGER, genre TEXT, lyrics TEXT, popularity_score REAL, album_id INTEGER, song_type TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS playlists (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS playlist_songs (playlist_id INTEGER, song_id INTEGER)""")
    cur.execute(
        """CREATE TABLE IF NOT EXISTS fans (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, genres TEXT, bands TEXT)""")

    conn.commit()
    conn.close()


# --- ARTISTS ---
def ensure_artist_exists(name: str):
    if not name: return
    name = name.strip()  #чистимо пробіли

    conn = get_conn()
    cur = conn.cursor()
    try:
        # 1. Спочатку шукаємо, чи є такий артист (ігноруючи регістр)
        cur.execute("SELECT id FROM artists WHERE name LIKE ?", (name,))
        if cur.fetchone():
            return  #знайшли - виходимо, нічого не додаємо

        # 2. Якщо не знайшли - додаємо нового
        cur.execute("INSERT INTO artists (name, genre, country) VALUES (?, ?, ?)",
                    (name, "Unknown", "Unknown"))
        conn.commit()
    except Exception as e:
        print(f"Error adding artist: {e}")
    finally:
        conn.close()


def get_all_artists() -> List[Artist]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM artists ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [Artist(id=r['id'], name=r['name'], genre=r['genre'], country=r['country']) for r in rows]


def update_artist_details(artist: Artist):
    conn = get_conn()
    conn.execute("UPDATE artists SET genre=?, country=? WHERE name=?", (artist.genre, artist.country, artist.name))
    conn.commit()
    conn.close()

def add_artist_to_db(name, genre, country):
    conn = get_conn()
    try:
        cur = conn.cursor()
        #Перевірка на дублікати
        cur.execute("SELECT id FROM artists WHERE name LIKE ?", (name,))
        if cur.fetchone():
            raise ValueError(f"Artist '{name}' already exists!")

        #Додавання
        cur.execute("INSERT INTO artists (name, genre, country) VALUES (?, ?, ?)",
                    (name, genre, country))
        conn.commit()
    finally:
        conn.close()

def delete_artist_by_name(name):
    conn = get_conn()
    try:
        conn.execute("DELETE FROM artists WHERE name=?", (name,))
        conn.commit()
    except Exception as e:
        print(f"Error deleting artist: {e}")
    finally:
        conn.close()


# --- SONGS ---
def add_song(song: Song) -> int:
    ensure_artist_exists(song.artist)
    conn = get_conn()
    cur = conn.cursor()
    s_type = type(song).__name__
    cur.execute("""
        INSERT INTO songs (title, artist, duration_sec, genre, lyrics, popularity_score, album_id, song_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (song.title, song.artist, song.duration_sec, song.genre, song.lyrics, song.popularity_score, song.album_id,
          s_type))
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return sid


def get_all_songs() -> List[Song]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM songs")
    rows = cur.fetchall()
    conn.close()
    res = []
    for r in rows:
        data = {k: r[k] for k in r.keys() if k != 'song_type'}
        s_type = r["song_type"]
        if s_type == "RockSong":
            obj = RockSong(**data)
        elif s_type == "PopSong":
            obj = PopSong(**data)
        elif s_type == "ClassicalSong":
            obj = ClassicalSong(**data)
        else:
            obj = Song(**data)
        res.append(obj)
    return res


def update_song(song: Song):
    ensure_artist_exists(song.artist)
    conn = get_conn()
    s_type = type(song).__name__
    conn.execute("""
        UPDATE songs 
        SET title=?, artist=?, duration_sec=?, genre=?, lyrics=?, popularity_score=?, album_id=?, song_type=?
        WHERE id=?
    """, (song.title, song.artist, song.duration_sec, song.genre,
          song.lyrics, song.popularity_score, song.album_id, s_type, song.id))
    conn.commit()
    conn.close()


def delete_song_by_id(sid):
    conn = get_conn()
    conn.execute("DELETE FROM playlist_songs WHERE song_id=?", (sid,))
    conn.execute("DELETE FROM songs WHERE id=?", (sid,))
    conn.commit()
    conn.close()


# --- ALBUMS ---
def add_album(album: Album) -> int:
    ensure_artist_exists(album.artist)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO albums (title, artist, year, rating, user_rating) VALUES (?, ?, ?, ?, ?)",
                (album.title, album.artist, album.year, album.rating, album.user_rating))
    conn.commit()
    aid = cur.lastrowid
    conn.close()
    return aid


def get_all_albums() -> List[Album]:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_rating FROM albums LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute("ALTER TABLE albums ADD COLUMN user_rating REAL DEFAULT 0.0")
        conn.commit()

    cur.execute("SELECT * FROM albums")
    rows = cur.fetchall()
    conn.close()
    return [Album(id=r['id'], title=r['title'], artist=r['artist'], year=r['year'],
                  rating=r['rating'], user_rating=r['user_rating'] if 'user_rating' in r.keys() else 0.0) for r in rows]


def update_album(album: Album):
    ensure_artist_exists(album.artist)
    conn = get_conn()
    conn.execute("UPDATE albums SET title=?, artist=?, year=?, user_rating=? WHERE id=?",
                 (album.title, album.artist, album.year, album.user_rating, album.id))
    conn.commit()
    conn.close()


def delete_album_by_id(aid):
    conn = get_conn()
    conn.execute("UPDATE songs SET album_id=0 WHERE album_id=?", (aid,))
    conn.execute("DELETE FROM albums WHERE id=?", (aid,))
    conn.commit()
    conn.close()


def get_album_songs(album_id: int) -> List[str]:
    """Повертає список назв пісень для конкретного альбому"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT title FROM songs WHERE album_id=?", (album_id,))
    rows = cur.fetchall()
    conn.close()
    return [r['title'] for r in rows]


# --- PLAYLISTS & FAN ---
def create_playlist(t):
    conn = get_conn()
    conn.execute("INSERT INTO playlists (title) VALUES (?)", (t,))
    conn.commit()
    conn.close()


def get_playlists():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM playlists")
    res = [{"id": r["id"], "title": r["title"]} for r in cur.fetchall()]
    conn.close()
    return res


def add_song_to_playlist(pid, sid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM playlist_songs WHERE playlist_id=? AND song_id=?", (pid, sid))
    if not cur.fetchone():
        cur.execute("INSERT INTO playlist_songs VALUES (?, ?)", (pid, sid))
    conn.commit()
    conn.close()


def get_playlist_songs(pid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT song_id FROM playlist_songs WHERE playlist_id=?", (pid,))
    res = [r[0] for r in cur.fetchall()]
    conn.close()
    return res


def get_or_create_default_fan():
    conn = get_conn()
    try:
        cur = conn.execute("SELECT * FROM fans LIMIT 1")
    except:
        init_db()
        cur = conn.execute("SELECT * FROM fans LIMIT 1")
    row = cur.fetchone()
    if row:
        f = Fan(id=row['id'], name=row['name'], genres=row['genres'], bands=row['bands'])
    else:
        conn.execute("INSERT INTO fans (name, genres, bands) VALUES (?,?,?)", ("User", "Rock", "Queen"))
        conn.commit()
        f = Fan(1, "User", "Rock", "Queen")
    conn.close()
    return f


def update_fan_profile(fan):
    conn = get_conn()
    conn.execute("UPDATE fans SET name=?, genres=?, bands=? WHERE id=?",
                 (fan.get_name(), fan.get_genres_str(), fan.get_bands_str(), fan.id))
    conn.commit()
    conn.close()