import ctypes
import os
from typing import List, Dict, Optional
from models import Song, Album

# Визначаємо шлях до DLL
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "libs", "libbackend_logic.dll")

cpp_lib = None
if os.path.exists(lib_path):
    try:
        cpp_lib = ctypes.CDLL(lib_path)
    except OSError as e:
        print(f"Error loading DLL: {e}")
else:
    # Спроба знайти в тій самій папці (на випадок, якщо dll лежить поруч)
    lib_path_alt = os.path.join(current_dir, "libbackend_logic.dll")
    if os.path.exists(lib_path_alt):
        try:
            cpp_lib = ctypes.CDLL(lib_path_alt)
        except OSError as e:
            print(f"Error loading DLL: {e}")

# Визначення структур C++ для Python
if cpp_lib:
    class SongC(ctypes.Structure):
        _fields_ = [
            ("id", ctypes.c_int),
            ("popularity", ctypes.c_double),
            ("duration", ctypes.c_int),
            ("title", ctypes.c_char * 100),
            ("artist", ctypes.c_char * 100),
            ("genre", ctypes.c_char * 50),
            ("album", ctypes.c_char * 100)
        ]


    class AlbumC(ctypes.Structure):
        _fields_ = [
            ("id", ctypes.c_int),
            ("year", ctypes.c_int),
            ("title", ctypes.c_char * 100)
        ]


    # Налаштування аргументів функцій C++

    # void sort_songs(SongC* songs, int count, int mode, int ascending)
    cpp_lib.sort_songs.argtypes = [ctypes.POINTER(SongC), ctypes.c_int, ctypes.c_int, ctypes.c_int]
    cpp_lib.sort_songs.restype = None

    # int filter_songs(SongC* songs, int count, const char* query, int* out_indices, int max_results, int search_mode)
    cpp_lib.filter_songs.argtypes = [ctypes.POINTER(SongC), ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int),
                                     ctypes.c_int, ctypes.c_int]
    cpp_lib.filter_songs.restype = ctypes.c_int

    # void sort_albums_by_year(AlbumC* albums, int count)
    cpp_lib.sort_albums_by_year.argtypes = [ctypes.POINTER(AlbumC), ctypes.c_int]
    cpp_lib.sort_albums_by_year.restype = None

    # int binary_search_album(AlbumC* albums, int count, const char* query)
    cpp_lib.binary_search_album.argtypes = [ctypes.POINTER(AlbumC), ctypes.c_int, ctypes.c_char_p]
    cpp_lib.binary_search_album.restype = ctypes.c_int

    # void get_top_n_greedy(SongC* songs, int count, int n)
    cpp_lib.get_top_n_greedy.argtypes = [ctypes.POINTER(SongC), ctypes.c_int, ctypes.c_int]
    cpp_lib.get_top_n_greedy.restype = None


# Допоміжні функції конвертації

def get_album_map(albums: List[Album]) -> Dict[int, str]:
    return {a.id: a.title for a in albums}


def songs_to_c(songs: List[Song], album_map: Dict[int, str]):
    arr = (SongC * len(songs))()
    for i, s in enumerate(songs):
        arr[i].id = s.id
        arr[i].popularity = s.popularity_score
        arr[i].duration = s.duration_sec

        # Кодування рядків (обрізка до розміру буфера - 1 байт на null-термінатор)
        t_enc = s.title.encode('utf-8')[:99]
        a_enc = s.artist.encode('utf-8')[:99]
        g_enc = s.genre.encode('utf-8')[:49]
        alb_enc = album_map.get(s.album_id, "-").encode('utf-8')[:99]

        arr[i].title = t_enc
        arr[i].artist = a_enc
        arr[i].genre = g_enc
        arr[i].album = alb_enc
    return arr


def albums_to_c(albums: List[Album]):
    arr = (AlbumC * len(albums))()
    for i, a in enumerate(albums):
        arr[i].id = a.id
        arr[i].year = a.year
        t_enc = a.title.encode('utf-8')[:99]
        arr[i].title = t_enc
    return arr


# ОСНОВНІ ФУНКЦІЇ
def search_songs_advanced(songs: List[Song], albums: List[Album], query: str, mode: int) -> List[Song]:
    """mode: 0=All, 1=Title, 2=Artist, 3=Genre, 4=Album"""
    if not songs or not cpp_lib: return []

    album_map = get_album_map(albums)
    c_arr = songs_to_c(songs, album_map)
    query_bytes = query.encode('utf-8')

    max_results = len(songs)
    results_ids = (ctypes.c_int * max_results)()

    # Виклик С++
    count = cpp_lib.filter_songs(c_arr, len(songs), query_bytes, results_ids, max_results, mode)

    found_songs = []
    song_map = {s.id: s for s in songs}
    for i in range(count):
        s_id = results_ids[i]
        if s_id in song_map:
            found_songs.append(song_map[s_id])
    return found_songs


def sort_songs_wrapper(songs: List[Song], albums: List[Album], mode: int, ascending: bool) -> List[Song]:
    """mode: 0=Pop, 1=Dur, 2=Title, 3=Art, 4=Genre, 5=Alb, 6=ID"""
    if not songs or not cpp_lib: return songs

    album_map = get_album_map(albums)
    c_arr = songs_to_c(songs, album_map)

    # Виклик С++ (QuickSort)
    cpp_lib.sort_songs(c_arr, len(songs), mode, 1 if ascending else 0)

    # Відновлення порядку
    song_map = {s.id: s for s in songs}
    res = []
    for i in range(len(songs)):
        if c_arr[i].id in song_map:
            res.append(song_map[c_arr[i].id])
    return res


def mergesort_albums_by_year(albums: List[Album]) -> List[Album]:
    if not albums or not cpp_lib: return albums
    c_arr = albums_to_c(albums)

    # Виклик С++ (MergeSort)
    cpp_lib.sort_albums_by_year(c_arr, len(albums))

    album_map = {a.id: a for a in albums}
    res = []
    for i in range(len(albums)):
        if c_arr[i].id in album_map:
            res.append(album_map[c_arr[i].id])
    return res


def binary_search_album(albums: List[Album], query_title: str) -> Optional[Album]:
    """
    Виконує бінарний пошук альбому за назвою через C++.
    УВАГА: Список albums має бути попередньо відсортований за назвою!
    """
    if not albums or not cpp_lib: return None

    # Конвертуємо в C-структури
    c_arr = albums_to_c(albums)
    query_bytes = query_title.encode('utf-8')

    # Виклик C++
    found_id = cpp_lib.binary_search_album(c_arr, len(albums), query_bytes)

    if found_id != -1:
        for a in albums:
            if a.id == found_id:
                return a
    return None


def greedy_top_n_songs(songs: List[Song], n: int) -> List[Song]:
    if not songs or not cpp_lib: return songs[:n]
    c_arr = songs_to_c(songs, {})

    # Виклик С++ (Greedy)
    cpp_lib.get_top_n_greedy(c_arr, len(songs), n)

    song_map = {s.id: s for s in songs}
    res = []
    for i in range(min(n, len(songs))):
        if c_arr[i].id in song_map:
            res.append(song_map[c_arr[i].id])
    return res