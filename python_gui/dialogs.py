from PyQt5.QtWidgets import (QDialog, QFormLayout, QLineEdit, QSpinBox,
                             QPushButton, QHBoxLayout, QTextEdit, QDoubleSpinBox,
                             QComboBox, QLabel)
from PyQt5.QtCore import Qt


class SongDialog(QDialog):
    def __init__(self, parent=None, song=None, albums_list=None, artists_list=None):
        super().__init__(parent)
        self.setWindowTitle("Add / Edit Song")
        self.resize(400, 550)

        layout = QFormLayout(self)

        # 1. Title
        self.title_edit = QLineEdit()
        layout.addRow("Title:", self.title_edit)

        # 2. Artist (ВИПАДАЮЧИЙ СПИСОК)
        self.artist_combo = QComboBox()
        self.artist_combo.setEditable(True)  # Можна і вибрати, і ввести нового
        self.artist_combo.setInsertPolicy(QComboBox.NoInsert)

        # Налаштування автодоповнення для артистів
        self.artist_combo.completer().setCompletionMode(self.artist_combo.completer().PopupCompletion)
        self.artist_combo.completer().setFilterMode(Qt.MatchContains)

        if artists_list:
            # Сортуємо, щоб легше було шукати очима, і додаємо в список
            sorted_artists = sorted([a.name for a in artists_list])
            self.artist_combo.addItems(sorted_artists)

        layout.addRow("Artist:", self.artist_combo)

        # 3. Album
        self.album_combo = QComboBox()
        self.album_combo.setEditable(True)
        self.album_combo.setInsertPolicy(QComboBox.NoInsert)
        self.album_combo.completer().setCompletionMode(self.album_combo.completer().PopupCompletion)
        self.album_combo.completer().setFilterMode(Qt.MatchContains)

        self.album_combo.addItem("Single", 0)

        if albums_list:
            for album in albums_list:
                display_text = f"{album.title}"
                if album.year > 0: display_text += f" ({album.year})"
                self.album_combo.addItem(display_text, album.id)

        layout.addRow("Album:", self.album_combo)

        # 4. Duration
        dur_layout = QHBoxLayout()
        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 59)
        self.min_spin.setSuffix(" m")
        self.sec_spin = QSpinBox()
        self.sec_spin.setRange(0, 59)
        self.sec_spin.setSuffix(" s")
        dur_layout.addWidget(self.min_spin)
        dur_layout.addWidget(self.sec_spin)
        layout.addRow("Duration:", dur_layout)

        # 5. Genre
        self.genre_edit = QLineEdit()
        layout.addRow("Genre:", self.genre_edit)

        # 6. Popularity
        self.popularity_spin = QDoubleSpinBox()
        self.popularity_spin.setRange(0.0, 10.0)
        self.popularity_spin.setDecimals(1)
        layout.addRow("Popularity (0-10):", self.popularity_spin)

        # 7. Lyrics
        self.lyrics_edit = QTextEdit()
        layout.addRow("Lyrics:", self.lyrics_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_ok.setStyleSheet("background-color: #198754; color: white; padding: 5px;")
        self.btn_cancel.setStyleSheet("background-color: #dc3545; color: white; padding: 5px;")
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addRow(btn_layout)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        if song:
            self.title_edit.setText(song.title)
            self.artist_combo.setCurrentText(song.artist)
            self.genre_edit.setText(song.genre)
            self.popularity_spin.setValue(song.popularity_score)
            self.lyrics_edit.setPlainText(song.lyrics)

            mins = song.duration_sec // 60
            secs = song.duration_sec % 60
            self.min_spin.setValue(mins)
            self.sec_spin.setValue(secs)

            index = self.album_combo.findData(song.album_id)
            if index >= 0:
                self.album_combo.setCurrentIndex(index)
            else:
                self.album_combo.setCurrentIndex(0)

    def get_song_data(self):
        total_sec = (self.min_spin.value() * 60) + self.sec_spin.value()
        return {
            "title": self.title_edit.text().strip(),
            "artist": self.artist_combo.currentText().strip(),
            "duration_sec": total_sec,
            "genre": self.genre_edit.text().strip(),
            "popularity_score": self.popularity_spin.value(),
            "lyrics": self.lyrics_edit.toPlainText().strip(),
            "album_id": self.album_combo.currentData(),
            "album_text": self.album_combo.currentText().strip()
        }

class AlbumDialog(QDialog):
    def __init__(self, parent=None, album=None):
        super().__init__(parent)
        self.setWindowTitle("Add / Edit Album")
        self.resize(350, 250)

        layout = QFormLayout(self)

        self.title_edit = QLineEdit()
        layout.addRow("Title:", self.title_edit)

        self.artist_edit = QLineEdit()
        layout.addRow("Artist:", self.artist_edit)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(1500, 2026)
        self.year_spin.setValue(2025)
        layout.addRow("Year:", self.year_spin)

        # ПОЛЕ РЕЙТИНГУ
        self.rating_spin = QDoubleSpinBox()
        self.rating_spin.setRange(0.0, 10.0)
        self.rating_spin.setDecimals(1)
        self.rating_spin.setSingleStep(0.5)
        layout.addRow("User Rating:", self.rating_spin)

        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_ok.setStyleSheet("background-color: #198754; color: white;")
        self.btn_cancel.setStyleSheet("background-color: #dc3545; color: white;")

        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addRow(btn_layout)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        if album:
            self.title_edit.setText(album.title)
            self.artist_edit.setText(album.artist)
            self.year_spin.setValue(album.year)
            # Встановлюємо поточний рейтинг, якщо він є
            current_rating = getattr(album, 'user_rating', 0.0)
            self.rating_spin.setValue(current_rating)

    def get_data(self):
        return {
            "title": self.title_edit.text().strip(),
            "artist": self.artist_edit.text().strip(),
            "year": self.year_spin.value(),
            "user_rating": self.rating_spin.value()
        }