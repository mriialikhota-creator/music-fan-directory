import sys
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox,
                             QHeaderView, QStackedWidget, QLabel, QListWidget, QFrame, QComboBox,
                             QInputDialog, QListWidgetItem, QTextEdit, QDialog, QFormLayout)
from PyQt5.QtCore import QSettings, Qt

from storage import (init_db, add_song, get_all_songs, delete_song_by_id, update_song,
                     add_album, get_all_albums, delete_album_by_id, update_album, get_album_songs,
                     create_playlist, get_playlists, add_song_to_playlist, get_playlist_songs,
                     get_or_create_default_fan, update_fan_profile,
                     get_all_artists, update_artist_details, add_artist_to_db, delete_artist_by_name)

from dialogs import SongDialog, AlbumDialog
from algorithms import (sort_songs_wrapper, search_songs_advanced,
                        greedy_top_n_songs, mergesort_albums_by_year,
                        binary_search_album)
from models import Song, MusicApp, Album, RockSong, PopSong, ClassicalSong, Artist

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Fan Directory")
        self.resize(1250, 800)
        self.settings = QSettings("MyCourseWork", "MusicApp")

        init_db()
        self.app_logic = MusicApp()
        self.sort_asc = {}
        self.current_playlist_id = None

        # Завантаження профілю користувача
        try:
            self.app_logic.current_user = get_or_create_default_fan()
        except Exception as e:
            print(f"Error loading user: {e}")

        # Головний віджет
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- 1. SIDEBAR (ЛІВА ПАНЕЛЬ) ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(240)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(15, 25, 15, 25)
        self.sidebar_layout.setSpacing(10)

        # Логотип
        self.lbl_logo = QLabel("🎵 FAN CABINET")
        self.lbl_logo.setObjectName("lbl_logo")
        self.lbl_logo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_logo.setFixedHeight(40)
        self.sidebar_layout.addWidget(self.lbl_logo)

        # Навігація
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("nav_list")
        self.nav_list.setFixedHeight(320)
        self.nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.nav_list.addItem(" Songs Library")
        self.nav_list.addItem(" Albums")
        self.nav_list.addItem(" Artists")
        self.nav_list.addItem(" Recommendations ⭐️")
        self.nav_list.addItem(" Coursework Tech")
        self.nav_list.addItem(" 👤 User Profile")

        self.sidebar_layout.addWidget(self.nav_list)

        # Плейлисти
        lbl_pl = QLabel("YOUR PLAYLISTS")
        lbl_pl.setObjectName("lbl_pl")
        self.sidebar_layout.addWidget(lbl_pl)

        self.playlist_list = QListWidget()
        self.playlist_list.setObjectName("playlist_list")
        self.playlist_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.sidebar_layout.addWidget(self.playlist_list)

        # Обробники кліків меню
        self.nav_list.currentRowChanged.connect(self.switch_page)
        self.playlist_list.itemClicked.connect(self.on_playlist_clicked)

        # Кнопки внизу сайдбару
        self.sidebar_layout.addStretch()

        btn_new_pl = QPushButton("+ New Playlist")
        btn_new_pl.clicked.connect(self.create_playlist_action)
        self.sidebar_layout.addWidget(btn_new_pl)

        self.sidebar_layout.addSpacing(10)

        self.btn_theme = QPushButton("🌗 Switch Theme")
        self.btn_theme.clicked.connect(self.toggle_theme)
        self.sidebar_layout.addWidget(self.btn_theme)

        main_layout.addWidget(self.sidebar)

        # --- 2. MAIN CONTENT (ПРАВА ЧАСТИНА) ---
        self.pages = QStackedWidget()
        main_layout.addWidget(self.pages)

        # Ініціалізація сторінок
        self.page_songs = QWidget()
        self.page_albums = QWidget()
        self.page_artists = QWidget()
        self.page_recs = QWidget()
        self.page_tech = QWidget()
        self.page_profile = QWidget()
        self.page_single_playlist = QWidget()

        self.pages.addWidget(self.page_songs)  # Index 0
        self.pages.addWidget(self.page_albums)  # Index 1
        self.pages.addWidget(self.page_artists)  # Index 2
        self.pages.addWidget(self.page_recs)  # Index 3
        self.pages.addWidget(self.page_tech)  # Index 4
        self.pages.addWidget(self.page_profile)  # Index 5
        self.pages.addWidget(self.page_single_playlist)  # Index 6

        # Налаштування UI для кожної сторінки
        self.setup_songs_ui()
        self.setup_albums_ui()
        self.setup_artists_ui()
        self.setup_recs_ui()
        self.setup_tech_ui()
        self.setup_profile_ui()
        self.setup_playlist_ui()

        # Завантаження даних
        self.load_songs()
        self.load_albums()
        self.load_artists()
        self.load_playlists()
        self.load_theme_state()

    def switch_page(self, index):
        # Якщо клікнули на основне меню, знімаємо виділення з плейлистів
        if self.nav_list.hasFocus():
            self.playlist_list.setCurrentItem(None)
            self.current_playlist_id = None

        # Оновлюємо дані при перемиканні
        if index == 1: self.load_albums()
        if index == 2: self.load_artists()
        if index == 3: self.refresh_recs()

        self.pages.setCurrentIndex(index)

    # ==================== SONGS PAGE ====================
    def setup_songs_ui(self):
        layout = QVBoxLayout(self.page_songs)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(80)
        header.setObjectName("header_frame")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(30, 20, 30, 20)

        title = QLabel("Songs Library")
        title.setObjectName("page_title")
        hl.addWidget(title)

        hl.addStretch()

        # Пошук (Лінійний)
        self.search_type = QComboBox()
        self.search_type.addItems(["All", "Title", "Artist", "Genre"])
        self.search_type.setFixedWidth(120)
        self.search_type.setCursor(Qt.PointingHandCursor)
        hl.addWidget(self.search_type)

        lbl_search = QLabel("🔍")
        lbl_search.setStyleSheet("font-size: 20px; color: #888;")
        hl.addWidget(lbl_search)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search songs (Linear)...")
        self.search_input.textChanged.connect(self.search_song_live)
        self.search_input.setFixedWidth(250)
        self.search_input.setFixedHeight(35)
        hl.addWidget(self.search_input)

        layout.addWidget(header)

        # Таблиця
        content_box = QVBoxLayout()
        content_box.setContentsMargins(30, 20, 30, 20)
        content_box.setSpacing(15)

        self.table_songs = QTableWidget(0, 8)
        cols = ["ID", "Title", "Artist", "Album", "Genre", "Rating", "Style Info (Poly)", "Rec. Vol"]
        self.table_songs.setHorizontalHeaderLabels(cols)
        self.table_songs.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_songs.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_songs.setSelectionMode(QTableWidget.SingleSelection)
        self.table_songs.doubleClicked.connect(self.edit_song_action)
        self.table_songs.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        content_box.addWidget(self.table_songs)

        # Кнопки
        controls = QHBoxLayout()

        btn_add = QPushButton("+ Add Song")
        btn_add.setObjectName("btn_add_song")
        btn_add.setFixedSize(140, 45)
        btn_add.clicked.connect(self.add_song_action)

        btn_edit = QPushButton("Edit")
        btn_edit.setFixedSize(100, 45)
        btn_edit.clicked.connect(self.edit_song_action)

        btn_pl = QPushButton("Add to Playlist")
        btn_pl.setFixedSize(140, 45)
        btn_pl.clicked.connect(self.add_to_playlist_action)

        btn_del = QPushButton("Delete")
        btn_del.setObjectName("btn_delete")
        btn_del.setFixedSize(100, 45)
        btn_del.clicked.connect(self.delete_song_action)

        controls.addWidget(btn_add)
        controls.addWidget(btn_edit)
        controls.addWidget(btn_pl)
        controls.addStretch()
        controls.addWidget(btn_del)

        content_box.addLayout(controls)
        layout.addLayout(content_box)

    def load_songs(self, songs=None):
        if songs is None:
            self.app_logic.songs = get_all_songs()
            songs = self.app_logic.songs

        # Кешуємо альбоми для швидкого доступу
        albums_dict = {a.id: a.title for a in get_all_albums()}

        self.table_songs.setRowCount(len(songs))
        for i, s in enumerate(songs):
            self.table_songs.setItem(i, 0, QTableWidgetItem(str(s.id)))
            self.table_songs.setItem(i, 1, QTableWidgetItem(s.title))
            self.table_songs.setItem(i, 2, QTableWidgetItem(s.artist))
            # Відображаємо назву альбому замість ID
            alb_name = albums_dict.get(s.album_id, "-")
            self.table_songs.setItem(i, 3, QTableWidgetItem(alb_name))
            self.table_songs.setItem(i, 4, QTableWidgetItem(s.genre))

            pop_text = f"{s.popularity_score}"
            if s.popularity_score >= 9.0: pop_text += " 🔥"
            self.table_songs.setItem(i, 5, QTableWidgetItem(pop_text))

            # Поліморфізм: Style Description
            self.table_songs.setItem(i, 6, QTableWidgetItem(s.getStyleDescription()))
            # Поліморфізм: Recommended Volume
            self.table_songs.setItem(i, 7, QTableWidgetItem(str(s.getRecommendedVolume())))

    def search_song_live(self):
        query = self.search_input.text()
        mode = self.search_type.currentIndex()
        if not query:
            self.load_songs()
            return
        # Використовуємо C++ для лінійного пошуку
        albums = get_all_albums()
        found = search_songs_advanced(self.app_logic.songs, albums, query, mode)
        self.load_songs(found)

    def on_header_clicked(self, index):
        # Логіка сортування пісень через C++ QuickSort
        mode_map = {0: 6, 1: 2, 2: 3, 3: 5, 4: 4, 5: 0}  # Mapping індексів колонок
        mode = mode_map.get(index, -1)
        if mode == -1: return

        current_asc = self.sort_asc.get(index, True)
        self.sort_asc[index] = not current_asc

        albums = get_all_albums()
        sorted_list = sort_songs_wrapper(self.app_logic.songs, albums, mode, current_asc)
        self.load_songs(sorted_list)

    def add_song_action(self):
        current_albums = get_all_albums()
        current_artists = get_all_artists()  # Отримуємо список артистів

        # Передаємо artists_list у діалог
        dlg = SongDialog(self, albums_list=current_albums, artists_list=current_artists)

        if dlg.exec_():
            try:
                data = dlg.get_song_data()
                final_album_id = data["album_id"]

                # Логіка створення альбому (без змін)
                if final_album_id == 0 and data["album_text"] and "No Album" not in data["album_text"]:
                    existing = next((a for a in current_albums if a.title.lower() == data["album_text"].lower()), None)
                    if existing:
                        final_album_id = existing.id
                    else:
                        # Важливо використати правильного артиста
                        new_album = Album(title=data["album_text"], artist=data["artist"], year=2025)
                        final_album_id = add_album(new_album)

                # Вибір класу пісні (без змін)
                genre = data["genre"].lower()
                if "rock" in genre:
                    SongClass = RockSong
                elif "pop" in genre:
                    SongClass = PopSong
                elif "classic" in genre:
                    SongClass = ClassicalSong
                else:
                    SongClass = Song

                args = {k: v for k, v in data.items() if k not in ['album_text', 'album_id']}
                args['album_id'] = final_album_id

                new_song = SongClass(**args)
                add_song(new_song)

                self.load_songs()
                self.load_artists()
                self.refresh_recs()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not add song: {str(e)}")

    def edit_song_action(self):
        row = self.table_songs.currentRow()
        if row < 0: return QMessageBox.warning(self, "Warning", "Select a song to edit!")

        try:
            sid = int(self.table_songs.item(row, 0).text())
            target = next((s for s in self.app_logic.songs if s.id == sid), None)

            if target:
                # Тут теж передаємо список артистів
                dlg = SongDialog(self, song=target,
                                 albums_list=get_all_albums(),
                                 artists_list=get_all_artists())

                if dlg.exec_():
                    data = dlg.get_song_data()
                    target.title = data['title']
                    target.artist = data['artist']
                    target.genre = data['genre']
                    target.duration_sec = data['duration_sec']
                    target.popularity_score = data['popularity_score']
                    target.lyrics = data['lyrics']
                    target.album_id = data['album_id']

                    update_song(target)
                    self.load_songs()
                    self.load_artists()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Edit error: {e}")

    def delete_song_action(self):
        row = self.table_songs.currentRow()
        if row >= 0:
            sid = int(self.table_songs.item(row, 0).text())
            if QMessageBox.question(self, "Confirm", "Delete this song?",
                                    QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                delete_song_by_id(sid)
                self.load_songs()
                self.load_artists()
                self.refresh_recs()

    # ==================== ALBUMS PAGE ====================
    def setup_albums_ui(self):
        layout = QVBoxLayout(self.page_albums)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QFrame()
        header.setFixedHeight(80)
        header.setObjectName("header_frame")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(30, 20, 30, 20)

        title = QLabel("Albums Library")
        title.setObjectName("page_title")
        hl.addWidget(title)
        hl.addStretch()

        # Кнопка Binary Search
        btn_bin = QPushButton("Binary Search (Year)")
        btn_bin.setFixedWidth(200)  # Збільшив ширину
        btn_bin.clicked.connect(self.binary_search_album_action)
        hl.addWidget(btn_bin)

        btn_add = QPushButton("+ Add Album")
        btn_add.setObjectName("btn_add_song")
        btn_add.setFixedSize(140, 40)
        btn_add.clicked.connect(self.add_album_action)
        hl.addWidget(btn_add)

        layout.addWidget(header)

        content = QVBoxLayout()
        content.setContentsMargins(30, 20, 30, 20)

        # Таблиця: 6 колонок (ID, Title, Artist, Year, User Rating)
        self.table_albums = QTableWidget(0, 5)
        self.table_albums.setHorizontalHeaderLabels(["ID", "Title", "Artist", "Year", "User Rating"])
        self.table_albums.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_albums.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_albums.setSelectionMode(QTableWidget.SingleSelection)
        self.table_albums.doubleClicked.connect(self.show_album_tracks)

        # Підключаємо сортування по року (Mergesort)
        self.table_albums.horizontalHeader().sectionClicked.connect(self.on_album_header_clicked)

        content.addWidget(self.table_albums)

        # Кнопки
        box = QHBoxLayout()
        btn_edit = QPushButton("Edit Album & Rating")
        btn_edit.setFixedSize(180, 45)
        btn_edit.clicked.connect(self.edit_album_action)

        btn_tracks = QPushButton("Show Tracks")
        btn_tracks.setFixedSize(140, 45)
        btn_tracks.clicked.connect(self.show_album_tracks)

        btn_del = QPushButton("Delete")
        btn_del.setObjectName("btn_delete")
        btn_del.setFixedSize(100, 45)
        btn_del.clicked.connect(self.delete_album_action)

        box.addWidget(btn_tracks)
        box.addWidget(btn_edit)
        box.addStretch()
        box.addWidget(btn_del)

        content.addLayout(box)
        layout.addLayout(content)

    def load_albums(self, albums=None):
        if albums is None: albums = get_all_albums()
        self.app_logic.albums = albums

        self.table_albums.setRowCount(len(albums))
        for i, a in enumerate(albums):
            self.table_albums.setItem(i, 0, QTableWidgetItem(str(a.id)))
            self.table_albums.setItem(i, 1, QTableWidgetItem(a.title))
            self.table_albums.setItem(i, 2, QTableWidgetItem(a.artist))
            self.table_albums.setItem(i, 3, QTableWidgetItem(str(a.year)))

            ur = getattr(a, 'user_rating', 0.0)
            self.table_albums.setItem(i, 4, QTableWidgetItem(f"{ur:.1f}"))

    def on_album_header_clicked(self, index):
        if index == 3:  # Year column
            # Сортування злиттям (Mergesort) через C++
            sorted_albums = mergesort_albums_by_year(self.app_logic.albums)
            self.load_albums(sorted_albums)
            QMessageBox.information(self, "Sort", "Albums sorted by Year using Mergesort (C++)")

    def binary_search_album_action(self):
        # 1. Сортуємо (обов'язково для бінарного пошуку)
        self.app_logic.albums.sort(key=lambda x: x.title.lower())

        text, ok = QInputDialog.getText(self, "Binary Search", "Enter EXACT Album Title:")
        if ok and text:
            # 2. Шукаємо
            import bisect
            titles = [a.title.lower() for a in self.app_logic.albums]
            idx = bisect.bisect_left(titles, text.lower())

            if idx != len(titles) and titles[idx] == text.lower():
                found = self.app_logic.albums[idx]
                self.load_albums([found])
                QMessageBox.information(self, "Result", f"Found: {found.title} ({found.year})")
            else:
                QMessageBox.warning(self, "Result", "Not found via Binary Search")
                self.load_albums()  # Скидаємо фільтр

    def add_album_action(self):
        dlg = AlbumDialog(self)
        if dlg.exec_():
            data = dlg.get_data()
            if data['title']:
                # Також беремо рейтинг одразу з діалогу
                a = Album(
                    title=data['title'],
                    artist=data['artist'],
                    year=data['year'],
                    rating=0.0,
                    user_rating=data['user_rating']
                )
                add_album(a)
                self.load_albums()
                self.load_artists()

    def edit_album_action(self):
        row = self.table_albums.currentRow()
        if row < 0: return QMessageBox.warning(self, "Warning", "Select album!")

        aid = int(self.table_albums.item(row, 0).text())
        target = next((a for a in self.app_logic.albums if a.id == aid), None)

        if target:
            dlg = AlbumDialog(self, album=target)
            if dlg.exec_():
                data = dlg.get_data()
                target.title = data['title']
                target.artist = data['artist']
                target.year = data['year']
                target.user_rating = data['user_rating']

                update_album(target)
                self.load_albums()
                self.load_artists()

    def show_album_tracks(self):
        row = self.table_albums.currentRow()
        if row < 0: return
        aid = int(self.table_albums.item(row, 0).text())
        title = self.table_albums.item(row, 1).text()

        # Отримуємо пісні з БД
        songs = get_album_songs(aid)

        if songs:
            msg = "<ul>" + "".join([f"<li>{s}</li>" for s in songs]) + "</ul>"
        else:
            msg = "<i>No songs in this album.</i>"

        QMessageBox.information(self, f"Album: {title}", f"<h3>Tracks:</h3>{msg}")

    def delete_album_action(self):
        row = self.table_albums.currentRow()
        if row >= 0:
            aid = int(self.table_albums.item(row, 0).text())
            if QMessageBox.question(self, "Confirm", "Delete this album?",
                                    QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                delete_album_by_id(aid)
                self.load_albums()
                self.load_songs()  # Оновити пісні (бо вони втратили альбом)

    # ==================== ARTISTS PAGE ====================
    def setup_artists_ui(self):
        layout = QVBoxLayout(self.page_artists)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QFrame()
        header.setFixedHeight(80)
        header.setObjectName("header_frame")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(30, 20, 30, 20)

        title = QLabel("Artists Library")
        title.setObjectName("page_title")
        hl.addWidget(title)
        layout.addWidget(header)

        content = QVBoxLayout()
        content.setContentsMargins(30, 20, 30, 20)

        # Таблиця Артистів
        self.table_artists = QTableWidget(0, 3)
        self.table_artists.setHorizontalHeaderLabels(["Name", "Genre", "Country"])
        self.table_artists.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_artists.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_artists.setSelectionMode(QTableWidget.SingleSelection)
        self.table_artists.doubleClicked.connect(self.edit_artist_action)
        content.addWidget(self.table_artists)

        btn_box = QHBoxLayout()

        btn_add = QPushButton("+ Add Artist")
        btn_add.setObjectName("btn_add_song")
        btn_add.setFixedSize(140, 45)
        btn_add.clicked.connect(self.add_artist_action)
        btn_box.addWidget(btn_add)

        btn_edit = QPushButton("View Albums / Edit Info")
        btn_edit.setFixedSize(220, 45)
        btn_edit.clicked.connect(self.edit_artist_action)

        btn_del_art = QPushButton("Delete Artist")
        btn_del_art.setObjectName("btn_delete")
        btn_del_art.setFixedSize(120, 45)
        btn_del_art.clicked.connect(self.delete_artist_action)

        btn_box.addStretch()
        btn_box.addWidget(btn_edit)
        btn_box.addWidget(btn_del_art)  # Додаємо кнопку в макет

        content.addLayout(btn_box)
        layout.addLayout(content)

    def add_artist_action(self):
        d = QDialog(self)
        d.setWindowTitle("Add New Artist")
        d.setMinimumWidth(300)

        form = QFormLayout(d)

        name_input = QLineEdit()
        genre_input = QLineEdit()
        country_input = QLineEdit()

        form.addRow("Name:", name_input)
        form.addRow("Genre:", genre_input)
        form.addRow("Country:", country_input)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Add")
        btn_ok.clicked.connect(d.accept)
        btn_ok.setStyleSheet("background-color: #198754; color: white;")  # Зелена

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(d.reject)

        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        form.addRow(btn_layout)

        if d.exec_():
            name = name_input.text().strip()
            genre = genre_input.text().strip()
            country = country_input.text().strip()

            if not name:
                QMessageBox.warning(self, "Error", "Name is required!")
                return

            try:
                add_artist_to_db(name, genre, country)
                self.load_artists()
                QMessageBox.information(self, "Success", f"Artist '{name}' added!")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def load_artists(self):
        try:
            artists = get_all_artists()
            self.app_logic.artists = artists
            self.table_artists.setRowCount(len(artists))
            for i, art in enumerate(artists):
                self.table_artists.setItem(i, 0, QTableWidgetItem(art.name))
                self.table_artists.setItem(i, 1, QTableWidgetItem(art.genre))
                self.table_artists.setItem(i, 2, QTableWidgetItem(art.country))
        except Exception as e:
            print(f"Artist load error: {e}")

    def edit_artist_action(self):
        row = self.table_artists.currentRow()
        if row < 0: return QMessageBox.warning(self, "Info", "Select an artist first")

        name = self.table_artists.item(row, 0).text()
        target = next((a for a in self.app_logic.artists if a.name == name), None)

        if target:
            # Створюємо діалог для редагування деталей та перегляду альбомів
            d = QDialog(self)
            d.setWindowTitle(f"Details: {name}")
            d.setMinimumWidth(400)
            form = QFormLayout(d)

            # Поля для редагування
            gen_edit = QLineEdit(target.genre)
            ctr_edit = QLineEdit(target.country)

            form.addRow("Genre:", gen_edit)
            form.addRow("Country:", ctr_edit)

            # СПИСОК АЛЬБОМІВ
            lbl_albums = QLabel("Albums by this Artist:")
            lbl_albums.setStyleSheet("font-weight: bold; margin-top: 10px;")
            form.addRow(lbl_albums)

            albums_list = QListWidget()
            # Знаходимо всі альбоми цього артиста
            artist_albums = [a for a in get_all_albums() if a.artist == name]

            if artist_albums:
                for a in artist_albums:
                    albums_list.addItem(f"{a.title} ({a.year})")
            else:
                albums_list.addItem("No albums found.")

            form.addRow(albums_list)

            # Кнопки
            bbox = QHBoxLayout()
            b_save = QPushButton("Save Info")
            b_save.setStyleSheet("background-color: #e49ed0; color: white;")
            b_save.clicked.connect(d.accept)

            b_close = QPushButton("Close")
            b_close.clicked.connect(d.reject)

            bbox.addWidget(b_save)
            bbox.addWidget(b_close)
            form.addRow(bbox)

            # Якщо натиснули Save
            if d.exec_():
                target.genre = gen_edit.text()
                target.country = ctr_edit.text()
                try:
                    update_artist_details(target)
                    self.load_artists()
                    QMessageBox.information(self, "Success", "Artist details updated!")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Save failed: {e}")

    def delete_artist_action(self):
        row = self.table_artists.currentRow()
        if row < 0: return QMessageBox.warning(self, "Info", "Select an artist to delete")

        name = self.table_artists.item(row, 0).text()

        if QMessageBox.question(self, "Confirm",
                                f"Delete artist '{name}'? \n(Songs will remain but won't be linked to this artist entry)",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            delete_artist_by_name(name)
            self.load_artists()
            QMessageBox.information(self, "Success", "Artist deleted.")

    # RECOMMENDATIONS
    def setup_recs_ui(self):
        layout = QVBoxLayout(self.page_recs)
        lbl = QLabel("Recommendations ⭐️")
        lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #ff70db; margin: 20px;")
        layout.addWidget(lbl, alignment=Qt.AlignCenter)

        self.recs_label = QLabel("Add songs to see recommendations!")
        self.recs_label.setStyleSheet("font-size: 16px; margin: 20px;")
        self.recs_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.recs_label)
        layout.addStretch()

    def refresh_recs(self):
        songs = get_all_songs()
        if not songs: return
        # Жадібний алгоритм: бере топ-5 найкращих
        top = greedy_top_n_songs(songs, 5)

        txt = "<h2 style='text-align:center;'>Top 5 Trending Songs</h2>"
        for i, s in enumerate(top):
            desc = s.getStyleDescription()
            txt += f"<p style='text-align:center; font-size:14px;'>{i + 1}. <b>{s.title}</b> - {s.artist} <br><span style='color:#ff70db'>Rating: {s.popularity_score}</span> | <i>{desc}</i></p>"
        self.recs_label.setText(txt)

    # TECH CONSOLE
    def setup_tech_ui(self):
        layout = QVBoxLayout(self.page_tech)
        lbl = QLabel("Technical Coursework Requirements")
        lbl.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(lbl)

        self.tech_console = QTextEdit()
        self.tech_console.setReadOnly(True)
        self.tech_console.setStyleSheet(
            "background-color: #1e1e1e; color: #00ff00; font-family: Consolas; font-size: 16px; padding: 10px;")
        layout.addWidget(self.tech_console)

        controls = QFrame()
        controls.setStyleSheet("background-color: #ccc; border-radius: 5px; margin: 10px;")
        cl = QHBoxLayout(controls)

        b1 = QPushButton("1. OOP & Poly")
        b1.clicked.connect(self.run_tech_oop)
        b1.setStyleSheet("background-color: #e49ed0; color: white;")

        b2 = QPushButton("2. Sorting")
        b2.clicked.connect(self.run_tech_sorting)
        b2.setStyleSheet("background-color: #E91E63; color: white;")

        b3 = QPushButton("3. Linear Search (C++)")
        b3.setStyleSheet("background-color: #ff9800; color: white;")
        b3.clicked.connect(self.run_tech_search)

        b4 = QPushButton("4. Binary Search")
        b4.setStyleSheet("background-color: #177822; color: white;")
        b4.clicked.connect(self.run_tech_binary_search)

        cl.addWidget(b1)
        cl.addWidget(b2)
        cl.addWidget(b3)
        cl.addWidget(b4)
        layout.addWidget(controls)

    def log_tech(self, text):
        self.tech_console.append(f">> {text}")

    def run_tech_oop(self):
        self.tech_console.clear()
        self.log_tech(">>> Testing OOP Polymorphism (Dynamic Binding)...")

        all_songs = get_all_songs()
        # Шукаємо в базі хоча б по одному представнику різних класів
        showcase = []
        types_found = set()
        for s in all_songs:
            s_type = type(s).__name__
            if s_type not in types_found:
                showcase.append(s)
                types_found.add(s_type)

        if len(showcase) < 2:
            showcase.append(RockSong(title="Demo Rock", artist="System of a Down"))
            showcase.append(ClassicalSong(title="Demo Classic", artist="Mozart"))

        for s in showcase:
            self.log_tech(f"Object: '{s.title}' | Class: {type(s).__name__}")
            self.log_tech(f"Style Description: {s.getStyleDescription()}")
            self.log_tech(f"Recommended Volume: {s.getRecommendedVolume()}%")
            self.log_tech("-" * 25)

    def run_tech_sorting(self):
        self.tech_console.clear()
        self.log_tech(">>> Testing C++ Quicksort (Sorting by Rating)...")
        songs = get_all_songs()
        if not songs: return self.log_tech("Error: Song database is empty.")

        start = time.perf_counter()
        # Call C++ wrapper (0 = popularity mode, False = descending)
        sorted_list = sort_songs_wrapper(songs, get_all_albums(), 0, False)
        end = time.perf_counter()

        duration = (end - start) * 1000
        self.log_tech(f"Sorted {len(songs)} items in {duration:.4f} ms.")
        self.log_tech("TOP-5 Songs after sorting:")
        for s in sorted_list[:5]:
            self.log_tech(f" -> {s.title} (Rating: {s.popularity_score})")

    def run_tech_search(self):
        text, ok = QInputDialog.getText(self, "Linear Search", "Enter search query:")
        if ok and text:
            self.tech_console.clear()
            self.log_tech(f">>> C++ Linear Search (Core): '{text}'...")
            songs = get_all_songs()

            start = time.perf_counter()
            # Call C++ filtering logic
            found = search_songs_advanced(songs, get_all_albums(), text, 0)
            end = time.perf_counter()

            duration = (end - start) * 1000
            self.log_tech(f"Found {len(found)} results in {duration:.4f} ms.")
            for s in found:
                self.log_tech(f" [+] Found: {s.title} — {s.artist} ({s.genre})")

    def run_tech_binary_search(self):
        text, ok = QInputDialog.getText(self, "Binary Search", "Exact Album Title:")
        if ok and text:
            self.tech_console.clear()
            self.log_tech(f"Binary searching for album: {text}...")
            # Prepare data
            albums = get_all_albums()
            albums.sort(key=lambda x: x.title)  # Must be sorted

            start = time.perf_counter()
            res = binary_search_album(albums, text)
            end = time.perf_counter()

            if res:
                self.log_tech(f"FOUND: {res.title} ({res.year})")
            else:
                self.log_tech("NOT FOUND.")
            self.log_tech(f"Time: {(end - start) * 1000:.4f} ms")

    # PROFILE
    def setup_profile_ui(self):
        layout = QVBoxLayout(self.page_profile)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("User Profile")
        title.setObjectName("page_title")
        layout.addWidget(title)

        frame = QFrame()
        frame.setObjectName("profile_frame")
        fl = QFormLayout(frame)

        self.prof_name = QLineEdit()
        self.prof_genres = QLineEdit()
        self.prof_bands = QLineEdit()

        # Load user data
        u = self.app_logic.current_user
        if u:
            self.prof_name.setText(u.get_name())
            self.prof_genres.setText(u.get_genres_str())
            self.prof_bands.setText(u.get_bands_str())

        fl.addRow("Name:", self.prof_name)
        fl.addRow("Favorite Genres:", self.prof_genres)
        fl.addRow("Favorite Bands:", self.prof_bands)

        layout.addWidget(frame)

        btn_save = QPushButton("Save Profile")
        btn_save.setFixedSize(150, 45)
        btn_save.setStyleSheet("background-color: #e49ed0; color: white; font-weight: bold;")
        btn_save.clicked.connect(self.save_profile_action)

        layout.addWidget(btn_save, alignment=Qt.AlignRight)
        layout.addStretch()

    def save_profile_action(self):
        u = self.app_logic.current_user
        if u:
            u.set_name(self.prof_name.text())
            u.set_genres_from_str(self.prof_genres.text())
            u.set_bands_from_str(self.prof_bands.text())
            try:
                update_fan_profile(u)
                QMessageBox.information(self, "Success", "Profile Updated!")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    # PLAYLISTS
    def create_playlist_action(self):
        t, ok = QInputDialog.getText(self, "New Playlist", "Name:")
        if ok and t:
            create_playlist(t)
            self.load_playlists()

    def load_playlists(self):
        self.playlist_list.clear()
        for p in get_playlists():
            item = QListWidgetItem(p['title'])
            item.setData(Qt.UserRole, p['id'])
            self.playlist_list.addItem(item)

    def add_to_playlist_action(self):
        row = self.table_songs.currentRow()
        if row < 0: return QMessageBox.warning(self, "Info", "Select a song first")
        sid = int(self.table_songs.item(row, 0).text())

        pls = get_playlists()
        if not pls: return QMessageBox.warning(self, "Info", "Create a playlist first!")

        names = [p['title'] for p in pls]
        pname, ok = QInputDialog.getItem(self, "Add to Playlist", "Select Playlist:", names, 0, False)
        if ok and pname:
            pid = next(p['id'] for p in pls if p['title'] == pname)
            add_song_to_playlist(pid, sid)
            QMessageBox.information(self, "Success", f"Added to {pname}")

    def on_playlist_clicked(self, item):
        self.current_playlist_id = item.data(Qt.UserRole)
        self.pages.setCurrentWidget(self.page_single_playlist)
        self.lbl_pl_title.setText(item.text())

        sids = get_playlist_songs(self.current_playlist_id)
        all_s = get_all_songs()
        pl_songs = [s for s in all_s if s.id in sids]
        self.load_playlist_songs(pl_songs)

    def setup_playlist_ui(self):
        layout = QVBoxLayout(self.page_single_playlist)
        layout.setContentsMargins(30, 20, 30, 20)

        self.lbl_pl_title = QLabel("Playlist")
        self.lbl_pl_title.setObjectName("page_title")
        layout.addWidget(self.lbl_pl_title)

        self.table_pl = QTableWidget(0, 3)
        self.table_pl.setHorizontalHeaderLabels(["Title", "Artist", "Duration"])
        self.table_pl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_pl.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table_pl)

        btn_back = QPushButton("Back to Library")
        btn_back.setFixedSize(150, 45)
        btn_back.clicked.connect(lambda: self.nav_list.setCurrentRow(0))
        layout.addWidget(btn_back)

    def load_playlist_songs(self, songs):
        self.table_pl.setRowCount(len(songs))
        for i, s in enumerate(songs):
            self.table_pl.setItem(i, 0, QTableWidgetItem(s.title))
            self.table_pl.setItem(i, 1, QTableWidgetItem(s.artist))
            mins = s.duration_sec // 60
            secs = s.duration_sec % 60
            self.table_pl.setItem(i, 2, QTableWidgetItem(f"{mins}:{secs:02d}"))

    # THEME
    def load_theme_state(self):
        self.is_dark_mode = self.settings.value("is_dark", False, type=bool)
        self.apply_theme()

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.settings.setValue("is_dark", self.is_dark_mode)
        self.apply_theme()

    def apply_theme(self):
        app = QApplication.instance()
        if self.is_dark_mode:
            # DARK THEME
            app.setStyleSheet("""
                 QMainWindow { background-color: #121212; color: white; }
                 QFrame#profile_frame { background-color: #333; border-radius: 10px; }
                 QLineEdit { background-color: #282828; color: white; border: 1px solid #444; }
                 QLabel { color: white; background: transparent; }
                 QLabel#lbl_logo { background-color: #181818; color: white; font-weight: bold; font-size: 22px; }
                 QLabel#page_title { font-weight: bold; color: white; font-size: 28px; }

                 QListWidget { background-color: #181818; border: none; font-size: 16px; color: white; outline: none; }
                 QListWidget::item { padding: 14px; color: #b3b3b3; border: none; }
                 QListWidget::item:selected { background-color: #282828; color: white; border-left: 4px solid #ff70db; }

                 QTableWidget { background-color: #121212; gridline-color: #333; color: white; border: none; }
                 QHeaderView::section { background-color: #181818; color: #b3b3b3; padding: 6px; font-weight: bold; border: none; }
                 QTableCornerButton::section { background-color: #181818; border: none; }
                 QTableWidget::item:selected { background-color: #ff70db; color: black; }

                 /* --- SCROLLBAR --- */
                 QScrollBar:vertical { border: none; background: #181818; width: 10px; margin: 0px; }
                 QScrollBar::handle:vertical { background: #444; min-height: 20px; border-radius: 5px; }
                 QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
                 QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

                 QLineEdit { 
                     background-color: #282828; color: white; 
                     border-radius: 5px; padding: 6px; border: 1px solid #444; 
                     font-size: 16px;
                 }

                 /* --- COMBO BOX FIX (Виправлення чорного тексту) --- */
                 QComboBox { 
                     background-color: #282828; color: white; 
                     border: 1px solid #444; padding: 5px; border-radius: 5px; font-size: 16px;
                 }
                 
                 /* Велике текстове поле (Lyrics), щоб було ТЕМНИМ */
                 QTextEdit {
                     background-color: #282828; color: white;
                     border-radius: 5px; padding: 6px; border: 1px solid #444;
                     font-size: 16px;
                 }
                 
                 /* Поле вводу всередині комбобоксу */
                 QComboBox QLineEdit { 
                     background-color: #282828; color: white; border: none; font-size: 16px;
                 }
                 /* Випадаючий список (Dropdown) */
                 QComboBox QAbstractItemView {
                     background-color: #282828; 
                     color: white;
                     border: 1px solid #444;
                     selection-background-color: #ff70db;
                     selection-color: black;
                     outline: none;
                     font-size: 16px;
                 }

                 QPushButton { background-color: #333; color: white; border-radius: 5px; padding: 8px; font-weight: bold; }
                 QPushButton:hover { background-color: #444; }
                 QPushButton#btn_add_song { background-color: #ff70db; color: black; }
                 QPushButton#btn_delete { background-color: #dc3545; color: white; }

                 QDialog { background-color: #2b2b2b; color: white; }
                 QDialog QLabel { color: white; font-size: 14px; }
                 QSpinBox, QDoubleSpinBox { background-color: #282828; color: white; border: 1px solid #444; padding: 5px; }
             """)
        else:
            # LIGHT THEME
            app.setStyleSheet("""
                 QMainWindow { background-color: #f5f5f5; color: black; }
                 QFrame#profile_frame { background-color: #ffffff; border: 1px solid #ddd; border-radius: 10px; }
                 QLineEdit { background-color: #fff; color: black; border: 1px solid #ccc; }
                 QLabel { color: black; background: transparent; }
                 QLabel#lbl_logo { color: black; font-weight: bold; font-size: 22px; }
                 QLabel#page_title { font-weight: bold; color: black; font-size: 28px; }

                 QListWidget { background-color: #ffffff; border: none; font-size: 16px; color: black; outline: none; }
                 QListWidget::item { padding: 12px; color: #333; }
                 QListWidget::item:selected { background-color: #e0e0e0; color: black; border-left: 4px solid #ff70db; }

                 QTableWidget { background-color: white; gridline-color: #eee; color: black; border: none; }
                 QHeaderView::section { background-color: #f9f9f9; color: #555; padding: 6px; font-weight: bold; }
                 QTableWidget::item:selected { background-color: #e0e0e0; color: black; }

                 QLineEdit { background-color: #fff; color: black; border: 1px solid #ccc; border-radius: 5px; padding: 6px; }
                 QComboBox { background-color: #fff; color: black; border: 1px solid #ccc; padding: 5px; }

                 QPushButton { background-color: #e0e0e0; color: black; border-radius: 5px; padding: 8px; }
                 QPushButton:hover { background-color: #d0d0d0; }
                 QPushButton#btn_add_song { background-color: #ff70db; color: white; }
                 QPushButton#btn_delete { background-color: #ffcdd2; color: #c62828; }

                 QDialog { background-color: #ffffff; color: black; }
                 QSpinBox, QDoubleSpinBox { background-color: #fff; color: black; border: 1px solid #ccc; padding: 5px; }
             """)


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()