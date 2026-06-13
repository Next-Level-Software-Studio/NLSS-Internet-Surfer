import os
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem

class BookmarksWindow(QDialog):
    def __init__(self, parent, bookmarks):
        super().__init__(parent)
        self.parent = parent
        self.bookmarks = bookmarks
        self.setWindowTitle("Gestão de Marcadores")
        self.setMinimumSize(420, 320)
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.refresh_list()
        layout.addWidget(self.list_widget)
        button_layout = QHBoxLayout()
        open_btn = QPushButton("Abrir")
        open_btn.clicked.connect(self.open_selected)
        remove_btn = QPushButton("Remover")
        remove_btn.clicked.connect(self.remove_selected)
        button_layout.addWidget(open_btn)
        button_layout.addWidget(remove_btn)
        layout.addLayout(button_layout)

    def refresh_list(self):
        self.list_widget.clear()
        for title, url in self.bookmarks.items():
            item = QListWidgetItem(f"{title} — {url}")
            item.setData(Qt.ItemDataRole.UserRole, url)
            self.list_widget.addItem(item)

    def open_selected(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        self.parent.open_url_in_current_tab(item.data(Qt.ItemDataRole.UserRole))
        self.close()

    def remove_selected(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        url = item.data(Qt.ItemDataRole.UserRole)
        title = item.text().split(" — ", 1)[0]
        if title in self.bookmarks and self.bookmarks[title] == url:
            del self.bookmarks[title]
            self.parent.save_bookmarks()
            self.parent.update_bookmarks_bar()
            self.refresh_list()

class DownloadsWindow(QDialog):
    def __init__(self, parent, downloads):
        super().__init__(parent)
        self.setWindowTitle("Transferências")
        self.setMinimumSize(520, 340)
        self.downloads = downloads
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.refresh_list()
        layout.addWidget(self.list_widget)
        button_layout = QHBoxLayout()
        open_folder_btn = QPushButton("Abrir pasta")
        open_folder_btn.clicked.connect(self.open_folder)
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(open_folder_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

    def refresh_list(self):
        self.list_widget.clear()
        for entry in self.downloads:
            status = entry.get("status", "Desconhecido")
            item = QListWidgetItem(f"{os.path.basename(entry.get('path', ''))} — {status}")
            item.setData(Qt.ItemDataRole.UserRole, entry.get("path", ""))
            self.list_widget.addItem(item)

    def open_folder(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        folder = os.path.dirname(item.data(Qt.ItemDataRole.UserRole))
        if folder and os.path.isdir(folder):
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
