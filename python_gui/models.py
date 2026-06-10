from dataclasses import dataclass
from typing import List


@dataclass
class Song:
    id: int = 0
    title: str = ""
    artist: str = ""
    duration_sec: int = 0
    genre: str = ""
    lyrics: str = ""
    popularity_score: float = 0.0  # Світовий рейтинг
    album_id: int = 0

    def getStyleDescription(self) -> str:
        return "General music style"

    def getRecommendedVolume(self) -> int:
        return 50


@dataclass
class RockSong(Song):
    def getStyleDescription(self) -> str:
        return "Rock: Energetic, guitar-driven sound."

    def getRecommendedVolume(self) -> int:
        return 80


@dataclass
class PopSong(Song):
    def getStyleDescription(self) -> str:
        return "Pop: Catchy melody, repetitive structure."

    def getRecommendedVolume(self) -> int:
        return 60


@dataclass
class ClassicalSong(Song):
    def getStyleDescription(self) -> str:
        return "Classical: Orchestral, complex dynamics."

    def getRecommendedVolume(self) -> int:
        return 45


@dataclass
class Album:
    id: int = 0
    title: str = ""
    artist: str = ""
    year: int = 0
    rating: float = 0.0  # Світовий рейтинг
    user_rating: float = 0.0  # Оцінка користувача (Fan)
    artist_id: int = 0


@dataclass
class Artist:
    id: int = 0
    name: str = ""
    genre: str = "Unknown"
    country: str = "Unknown"


class Fan:
    def __init__(self, id: int = 0, name: str = "New User", genres: str = "", bands: str = ""):
        self.id = id
        self.__name = name
        genres_str = genres if genres else ""
        bands_str = bands if bands else ""
        self._favorite_genres = [g.strip() for g in genres_str.split(',') if g.strip()]
        self.favorite_bands = [b.strip() for b in bands_str.split(',') if b.strip()]

    def get_name(self) -> str:
        return self.__name

    def set_name(self, name: str):
        if name: self.__name = name

    def get_genres_str(self) -> str:
        return ", ".join(self._favorite_genres)

    def set_genres_from_str(self, genres_str: str):
        self._favorite_genres = [g.strip() for g in genres_str.split(',') if g.strip()]

    def get_bands_str(self) -> str:
        return ", ".join(self.favorite_bands)

    def set_bands_from_str(self, bands_str: str):
        self.favorite_bands = [b.strip() for b in bands_str.split(',') if b.strip()]


class MusicApp:
    def __init__(self):
        self.songs: List[Song] = []
        self.albums: List[Album] = []
        self.artists: List[Artist] = []  # Список артистів
        self.current_user: Fan = None