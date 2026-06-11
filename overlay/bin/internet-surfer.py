import sys, os
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLineEdit, QStatusBar, 
                             QFileDialog, QMessageBox, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTabBar, QStackedWidget, 
                             QMenu, QCheckBox, QSplitter, QLabel)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest
from PyQt6.QtGui import QAction, QColor
class SafeSearchWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configurações do Safe Search")
        self.setGeometry(200, 200, 500, 400)
        self.setStyleSheet("background-color: #f8f9fa;")
        layout = QVBoxLayout(self)
        self.label = QLabel("Funcionalidades do Safe Search\n\nAdicionado em breve...", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-family: 'Segoe UI', Arial, sans-serif; font-size: 16px; color: #5f6368;")
        layout.addWidget(self.label)
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Internet Surfer")
        self.setGeometry(100, 100, 1200, 800)
        self.safe_search_window = None
        self.apply_embedded_stylesheet()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        tab_container = QWidget()
        tab_container.setObjectName("tab_container")
        tab_layout = QHBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        self.tab_bar = QTabBar()
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setMovable(True)
        self.tab_bar.setExpanding(True)
        self.tab_bar.setElideMode(Qt.TextElideMode.ElideRight)
        self.tab_bar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_bar.customContextMenuRequested.connect(self.show_tab_context_menu)
        self.tab_bar.tabCloseRequested.connect(self.close_current_tab)
        self.tab_bar.currentChanged.connect(self.tab_changed)
        self.tab_bar.tabBarClicked.connect(self.adjust_tab_widths)
        tab_layout.addWidget(self.tab_bar)
        self.new_tab_btn = QPushButton("＋")
        self.new_tab_btn.setObjectName("new_tab_btn")
        self.new_tab_btn.clicked.connect(lambda: self.add_new_tab())
        tab_layout.addWidget(self.new_tab_btn)
        tab_layout.addStretch(1)
        main_layout.addWidget(tab_container)
        nav_bar_widget = QWidget()
        nav_bar_widget.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #dee1e6;")
        nav_layout = QHBoxLayout(nav_bar_widget)
        nav_layout.setContentsMargins(8, 4, 8, 6)
        nav_layout.setSpacing(8)
        self.back_btn = QPushButton("←")
        self.back_btn.clicked.connect(lambda: self.get_current_browser().back() if self.get_current_browser() else None)
        nav_layout.addWidget(self.back_btn)
        self.forward_btn = QPushButton("→")
        self.forward_btn.clicked.connect(lambda: self.get_current_browser().forward() if self.get_current_browser() else None)
        nav_layout.addWidget(self.forward_btn)
        self.reload_btn = QPushButton("↻")
        self.reload_btn.clicked.connect(lambda: self.get_current_browser().reload() if self.get_current_browser() else None)
        nav_layout.addWidget(self.reload_btn)
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_layout.addWidget(self.url_bar)
        self.safe_search_switch = QCheckBox("Pesquisa Segura")
        self.safe_search_switch.setObjectName("safe_search_switch")
        self.safe_search_switch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.safe_search_switch.stateChanged.connect(self.safe_search_toggled)
        nav_layout.addWidget(self.safe_search_switch)
        self.menu_btn = QPushButton("⋮")
        self.menu_btn.setObjectName("menu_btn")
        self.menu_btn.clicked.connect(self.show_menu)
        nav_layout.addWidget(self.menu_btn)
        self.browser_menu = QMenu(self)
        self.browser_menu.addAction("Nova aba").triggered.connect(lambda: self.add_new_tab())
        self.browser_menu.addSeparator()
        self.browser_menu.addAction("Safe Search").triggered.connect(self.open_safe_search_window)
        self.browser_menu.addSeparator()
        self.browser_menu.addAction("Histórico").triggered.connect(lambda: QMessageBox.information(self, "Histórico", "Em breve!"))
        self.browser_menu.addAction("Downloads").triggered.connect(lambda: QMessageBox.information(self, "Downloads", "Em breve!"))
        self.browser_menu.addSeparator()
        self.browser_menu.addAction("Sobre o Internet Surfer").triggered.connect(lambda: QMessageBox.about(self, "Sobre", "Internet Surfer com suporte avançado a Split View."))
        main_layout.addWidget(nav_bar_widget)
        self.container = QStackedWidget()
        main_layout.addWidget(self.container)
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.add_new_tab(QUrl("https://www.gentoo.org/"), "Gentoo Linux")
    def apply_embedded_stylesheet(self):
        qss = """
        QMainWindow { background-color: #ffffff; }
        QWidget#tab_container { background-color: #dee1e6; border: none; }
        QStatusBar { background-color: #f1f3f4; color: #5f6368; font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px; }
        QTabBar { background-color: #dee1e6; qproperty-drawBase: 0; border: none; }
        QTabBar::tab { background-color: #dee1e6; color: #3c4043; padding: 8px 12px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-top: 4px; margin-right: 2px; font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; }
        QTabBar::tab:selected { background-color: #ffffff; }
        QTabBar::tab:hover:not(:selected) { background-color: #e8eaed; color: #202124; }
        QTabBar::close-button { subcontrol-position: right; border-radius: 2px; }
        QTabBar::close-button:hover { background-color: #e81123; color: white; }
        QSplitter::handle { background-color: #dee1e6; }
        QLineEdit { background-color: #f1f3f4; color: #202124; border: none; border-radius: 14px; padding: 5px 15px; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
        QLineEdit:focus { border: 2px solid #1a73e8; background-color: #ffffff; padding: 3px 13px; }
        QPushButton { background-color: transparent; color: #5f6368; border: none; border-radius: 14px; min-width: 28px; min-height: 28px; max-width: 28px; max-height: 28px; font-size: 16px; }
        QPushButton:hover { background-color: rgba(0, 0, 0, 0.06); color: #202124; }
        QPushButton:pressed { background-color: rgba(0, 0, 0, 0.12); }
        QPushButton#new_tab_btn { color: #5f6368; font-size: 14px; margin-top: 6px; margin-left: 4px; }
        QPushButton#new_tab_btn:hover { background-color: rgba(0, 0, 0, 0.06); color: #202124; }
        QPushButton#menu_btn { font-size: 18px; font-weight: bold; }
        QCheckBox#safe_search_switch { color: #5f6368; font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; font-weight: bold; spacing: 8px; }
        QCheckBox#safe_search_switch:hover { color: #202124; }
        QCheckBox#safe_search_switch::indicator { width: 34px; height: 20px; border-radius: 10px; }
        QCheckBox#safe_search_switch::indicator:unchecked { background-color: #dee1e6; }
        QCheckBox#safe_search_switch::indicator:checked { background-color: #1a73e8; }
        QCheckBox#safe_search_switch::indicator::text-button { background-color: #ffffff; border-radius: 7px; width: 14px; height: 14px; }
        QMenu { background-color: #ffffff; border: 1px solid #dee1e6; border-radius: 8px; padding: 4px 0px; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; color: #202124; }
        QMenu::item { padding: 8px 32px 8px 16px; }
        QMenu::item:selected { background-color: #f1f3f4; }
        QMenu::separator { height: 1px; background-color: #dee1e6; margin: 4px 0px; }
        """
        self.setStyleSheet(qss)
    def open_safe_search_window(self):
        if self.safe_search_window is None:
            self.safe_search_window = SafeSearchWindow()
        self.safe_search_window.show()
        self.safe_search_window.raise_()
        self.safe_search_window.activateWindow()
    def show_tab_context_menu(self, point):
        tab_index = self.tab_bar.tabAt(point)
        if tab_index == -1:
            return
        context_menu = QMenu(self)
        tab_data = self.tab_bar.tabData(tab_index)
        splitter = self.container.widget(tab_data["splitter_index"]) if tab_data else None
        if splitter and splitter.count() == 1:
            split_submenu = context_menu.addMenu("🖥️ Escolher aba para dividir")
            has_other_tabs = False
            for i in range(self.tab_bar.count()):
                if i != tab_index:
                    has_other_tabs = True
                    tab_title = self.tab_bar.tabText(i)
                    action = QAction(tab_title, self)
                    action.triggered.connect(lambda checked, current_idx=tab_index, target_idx=i: self.split_with_existing_tab(current_idx, target_idx))
                    split_submenu.addAction(action)
            if not has_other_tabs:
                placeholder_action = QAction("Nenhuma outra aba aberta", self)
                placeholder_action.setEnabled(False)
                split_submenu.addAction(placeholder_action)
        elif splitter and splitter.count() > 1:
            unsplit_action = QAction("📺 Desfazer Vista Dividida (Separar Abas)", self)
            unsplit_action.triggered.connect(lambda: self.unsplit_tab(tab_index))
            context_menu.addAction(unsplit_action)
        context_menu.addSeparator()
        groups = [
            ("Grupo Trabalho (Azul)", "#1a73e8"),
            ("Grupo Lazer (Verde)", "#1e8e3e"),
            ("Grupo Estudos (Laranja)", "#f2994a")
        ]
        for name, color in groups:
            action = QAction(name, self)
            action.triggered.connect(lambda checked, idx=tab_index, col=color: self.assign_tab_to_group(idx, col))
            context_menu.addAction(action)
        context_menu.addSeparator()
        clear_action = QAction("Remover do Grupo", self)
        clear_action.triggered.connect(lambda: self.assign_tab_to_group(tab_index, None))
        context_menu.addAction(clear_action)
        context_menu.exec(self.tab_bar.mapToGlobal(point))
    def split_with_existing_tab(self, current_tab_index, target_tab_index):
        current_data = self.tab_bar.tabData(current_tab_index)
        target_data = self.tab_bar.tabData(target_tab_index)
        if not current_data or not target_data:
            return
        current_splitter = self.container.widget(current_data["splitter_index"])
        target_splitter = self.container.widget(target_data["splitter_index"])
        target_browser = target_splitter.widget(0)
        if not target_browser:
            return
        target_splitter.removeWidget(target_browser)
        current_splitter.addWidget(target_browser)
        current_data["moved_browser"] = target_browser
        current_data["moved_browser_original_title"] = self.tab_bar.tabText(target_tab_index).replace("● ", "")
        self.tab_bar.setTabData(current_tab_index, current_data)
        self.tab_bar.removeTab(target_tab_index)
        target_browser.urlChanged.connect(lambda qurl, b=target_browser: self.update_url_bar(qurl, b))
        target_browser.titleChanged.connect(lambda title, b=target_browser: self.update_title(title, b))
        self.tab_changed(self.tab_bar.currentIndex())
    def unsplit_tab(self, tab_index):
        tab_data = self.tab_bar.tabData(tab_index)
        if not tab_data or "moved_browser" not in tab_data:
            return
        current_splitter = self.container.widget(tab_data["splitter_index"])
        moved_browser = tab_data["moved_browser"]
        original_title = tab_data.get("moved_browser_original_title", "Aba Restaurada")
        if current_splitter.count() > 1 and moved_browser:
            current_splitter.removeWidget(moved_browser)
            new_splitter = QSplitter(Qt.Orientation.Horizontal)
            new_splitter.setStyleSheet("QSplitter::handle { background-color: #dee1e6; width: 4px; }")
            new_splitter.addWidget(moved_browser)
            new_splitter_index = self.container.addWidget(new_splitter)
            new_tab_index = self.tab_bar.addTab(original_title)
            self.tab_bar.setTabData(new_tab_index, {"splitter_index": new_splitter_index})
            del tab_data["moved_browser"]
            self.tab_bar.setTabData(tab_index, tab_data)
            moved_browser.urlChanged.connect(lambda qurl, b=moved_browser: self.update_url_bar(qurl, b))
            moved_browser.titleChanged.connect(lambda title, b=moved_browser: self.update_title(title, b))
            self.adjust_tab_widths()
        self.tab_changed(self.tab_bar.currentIndex())
    def assign_tab_to_group(self, tab_index, color_hex):
        if color_hex:
            self.tab_bar.setTabTextColor(tab_index, QColor(color_hex))
            current_text = self.tab_bar.tabText(tab_index)
            if not current_text.startswith("● "):
                self.tab_bar.setTabText(tab_index, f"● {current_text}")
        else:
            self.tab_bar.setTabTextColor(tab_index, QColor("#3c4043"))
            current_text = self.tab_bar.tabText(tab_index)
            if current_text.startswith("● "):
                self.tab_bar.setTabText(tab_index, current_text[2:])
    def safe_search_toggled(self, state):
        is_checked = (state == 2 or state == Qt.CheckState.Checked)
        self.status.showMessage("Pesquisa Segura Ativada" if is_checked else "Pesquisa Segura Desativada", 2000)
    def show_menu(self):
        pos = self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomRight())
        pos.setX(pos.x() - self.browser_menu.sizeHint().width())
        self.browser_menu.exec(pos)
    def adjust_tab_widths(self):
        num_tabs = self.tab_bar.count()
        if num_tabs == 0:
            return
        parent_widget = self.tab_bar.parent()
        available_width = parent_widget.width() - self.new_tab_btn.width() - 30 if parent_widget else 800
        min_tab_width = 75
        max_tab_width = 240
        tab_width = max(min_tab_width, min(max_tab_width, available_width // num_tabs))
        self.tab_bar.setStyleSheet(f"QTabBar::tab {{ min-width: {min_tab_width}px; max-width: {tab_width}px; }}")
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_tab_widths()
    def add_new_tab(self, qurl=None, label="Nova guia"):
        if qurl is None:
            qurl = QUrl("https://www.gentoo.org/")
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #dee1e6; width: 4px; }")
        left_browser = QWebEngineView()
        left_browser.setUrl(qurl)
        splitter.addWidget(left_browser)
        splitter_index = self.container.addWidget(splitter)
        tab_index = self.tab_bar.addTab(label)
        self.tab_bar.setTabData(tab_index, {"splitter_index": splitter_index})
        self.tab_bar.setCurrentIndex(tab_index)
        self.adjust_tab_widths()
        left_browser.urlChanged.connect(lambda qurl, b=left_browser: self.update_url_bar(qurl, b))
        left_browser.titleChanged.connect(lambda title, b=left_browser: self.update_title(title, b))
        left_browser.loadProgress.connect(self.update_progress)
        left_browser.loadFinished.connect(self.load_finished)
        left_browser.page().profile().downloadRequested.connect(self.handle_download)
    def get_current_browser(self):
        splitter = self.container.currentWidget()
        if splitter and isinstance(splitter, QSplitter):
            if splitter.count() > 1 and splitter.widget(1).hasFocus():
                return splitter.widget(1)
            return splitter.widget(0)
        return None
    def close_current_tab(self, index):
        if self.tab_bar.count() < 2:
            return
        tab_data = self.tab_bar.tabData(index)
        if tab_data and "splitter_index" in tab_data:
            if "moved_browser" in tab_data and tab_data["moved_browser"]:
                tab_data["moved_browser"].deleteLater()
            splitter_index = tab_data["splitter_index"]
            splitter_widget = self.container.widget(splitter_index)
            if splitter_widget:
                self.container.removeWidget(splitter_widget)
                splitter_widget.deleteLater()
        self.tab_bar.removeTab(index)
        self.adjust_tab_widths()
    def tab_changed(self, index):
        if index >= 0:
            tab_data = self.tab_bar.tabData(index)
            if tab_data and "splitter_index" in tab_data:
                splitter_index = tab_data["splitter_index"]
                self.container.setCurrentIndex(splitter_index)
                browser = self.get_current_browser()
                if browser:
                    self.url_bar.setText(browser.url().toString())
        self.adjust_tab_widths()
    def navigate_to_url(self):
        text = self.url_bar.text()
        if not text.startswith("http://") and not text.startswith("https://"):
            url = QUrl("https://" + text)
        else:
            url = QUrl(text)
        active_browser = self.get_current_browser()
        if active_browser:
            active_browser.setUrl(url)
    def update_url_bar(self, url, browser):
        if browser == self.get_current_browser():
            self.url_bar.setText(url.toString())
    def update_title(self, title, browser):
        for index in range(self.tab_bar.count()):
            tab_data = self.tab_bar.tabData(index)
            if tab_data:
                splitter = self.container.widget(tab_data.get("splitter_index"))
                if splitter and (splitter.widget(0) == browser or (splitter.count() > 1 and splitter.widget(1) == browser)):
                    has_bullet = self.tab_bar.tabText(index).startswith("● ")
                    short_title = title[:15] + "..." if len(title) > 15 else title
                    if splitter.count() > 1:
                        short_title = f"[Split] {short_title}"
                    if has_bullet:
                        self.tab_bar.setTabText(index, f"● {short_title}")
                    else:
                        self.tab_bar.setTabText(index, short_title)
                    break
    def update_progress(self, progress):
        if progress < 100:
            self.status.showMessage(f"Carregando... {progress}%")
    def load_finished(self):
        self.status.showMessage("Pronto", 3000)
    def handle_download(self, download_item: QWebEngineDownloadRequest):
        default_path = os.path.expanduser(f"~/Downloads/{download_item.suggestedFileName()}")
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo", default_path)
        if path:
            download_item.setDownloadDirectory(os.path.dirname(path))
            download_item.setDownloadFileName(os.path.basename(path))
            download_item.accept()
            self.status.showMessage(f"Baixando: {download_item.suggestedFileName()}", 5000)
            download_item.stateChanged.connect(lambda state: self.download_status_changed(state, download_item))
        else:
            download_item.interrupt()
    def download_status_changed(self, state, download_item):
        if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            QMessageBox.information(self, "Download Concluído", f"O arquivo '{download_item.suggestedFileName()}' foi baixado com sucesso!")
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
            QMessageBox.warning(self, "Download Interrompido", f"O download de '{download_item.suggestedFileName()}' falhou ou foi cancelado.")
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Internet Surfer")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())