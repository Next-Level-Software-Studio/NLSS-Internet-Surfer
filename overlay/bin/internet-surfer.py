import sys, os, json
from PyQt6.QtCore import QUrl, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLineEdit, QStatusBar, QFileDialog, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabBar, QStackedWidget, QMenu, QCheckBox, QSplitter, QLabel, QToolBar)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEngineProfile, QWebEnginePage
from PyQt6.QtGui import QAction
from PyQt6.QtNetwork import QNetworkProxy, QNetworkAccessManager, QNetworkRequest, QNetworkReply
BOOKMARKS_FILE = os.path.expanduser("~/.internet_surfer_bookmarks.json")
class TorCheckWorker(QThread):
    result_signal = pyqtSignal(bool)
    def run(self):
        manager = QNetworkAccessManager()
        proxy = QNetworkProxy(QNetworkProxy.ProxyType.Socks5Proxy, "127.0.0.1", 9050)
        manager.setProxy(proxy)
        request = QNetworkRequest(QUrl("https://check.torproject.org/api/ip"))
        request.setAttribute(QNetworkRequest.Attribute.HttpPipeliningAllowedAttribute, True)
        reply = manager.get(request)
        from PyQt6.QtCore import QEventLoop
        loop = QEventLoop()
        reply.finished.connect(loop.quit)
        loop.exec()
        if reply.error() == QNetworkReply.NetworkError.NoError:
            self.result_signal.emit(True)
        else:
            self.result_signal.emit(False)
        reply.deleteLater()
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
        self.history_list = []
        self.bookmarks = self.load_bookmarks()
        self.private_profile = QWebEngineProfile("PrivateProfile", self)
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
        self.tab_bar.setExpanding(False)
        self.tab_bar.setElideMode(Qt.TextElideMode.ElideRight)
        self.tab_bar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_bar.customContextMenuRequested.connect(self.show_tab_context_menu)
        self.tab_bar.tabCloseRequested.connect(self.close_current_tab)
        self.tab_bar.currentChanged.connect(self.tab_changed)
        tab_layout.addWidget(self.tab_bar)
        self.new_tab_btn = QPushButton("＋")
        self.new_tab_btn.setObjectName("new_tab_btn")
        self.new_tab_btn.clicked.connect(lambda: self.add_new_tab())
        tab_layout.addWidget(self.new_tab_btn)
        tab_layout.addStretch(1)
        main_layout.addWidget(tab_container)
        nav_bar_widget = QWidget()
        nav_bar_widget.setObjectName("nav_bar_widget")
        nav_layout = QHBoxLayout(nav_bar_widget)
        nav_layout.setContentsMargins(8, 4, 8, 4)
        nav_layout.setSpacing(6)
        self.back_btn = QPushButton("←")
        self.back_btn.clicked.connect(lambda: self.get_current_browser().back() if self.get_current_browser() else None)
        nav_layout.addWidget(self.back_btn)
        self.forward_btn = QPushButton("→")
        self.forward_btn.clicked.connect(lambda: self.get_current_browser().forward() if self.get_current_browser() else None)
        nav_layout.addWidget(self.forward_btn)
        self.reload_btn = QPushButton("↻")
        self.reload_btn.clicked.connect(lambda: self.get_current_browser().reload() if self.get_current_browser() else None)
        nav_layout.addWidget(self.reload_btn)
        self.url_container = QWidget()
        self.url_container.setObjectName("url_container")
        url_layout = QHBoxLayout(self.url_container)
        url_layout.setContentsMargins(10, 0, 10, 0)
        url_layout.setSpacing(4)
        self.url_bar = QLineEdit()
        self.url_bar.setStyleSheet("background: transparent; border: none; padding: 0;")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        url_layout.addWidget(self.url_bar)
        self.bookmark_btn = QPushButton("⭐")
        self.bookmark_btn.setObjectName("bookmark_btn")
        self.bookmark_btn.setToolTip("Adicionar aos Favoritos")
        self.bookmark_btn.clicked.connect(self.add_current_to_bookmarks)
        url_layout.addWidget(self.bookmark_btn)
        nav_layout.addWidget(self.url_container, 1)
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
        self.browser_menu.addAction("Histórico").triggered.connect(self.show_history)
        self.browser_menu.addAction("Limpar Dados de Navegação (Cookies/Cache)").triggered.connect(self.clear_browser_data)
        self.browser_menu.addAction("Downloads").triggered.connect(lambda: QMessageBox.information(self, "Downloads", "Em breve!"))
        self.browser_menu.addSeparator()
        self.browser_menu.addAction("Sobre o Internet Surfer").triggered.connect(lambda: QMessageBox.about(self, "Sobre", "Internet Surfer com suporte avançado a Split View."))
        main_layout.addWidget(nav_bar_widget)
        self.bookmarks_bar = QToolBar("Favoritos")
        self.bookmarks_bar.setMovable(False)
        main_layout.addWidget(self.bookmarks_bar)
        self.update_bookmarks_bar()
        self.container = QStackedWidget()
        main_layout.addWidget(self.container)
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.add_new_tab(QUrl("https://www.gentoo.org/"), "Gentoo Linux")
    def apply_embedded_stylesheet(self):
        qss = """
        QMainWindow { background-color: #f1f3f4; }
        QWidget#tab_container { background-color: #dee1e6; padding-top: 8px; padding-left: 8px; }
        QStatusBar { background-color: #f1f3f4; color: #5f6368; font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px; }
        QTabBar { qproperty-drawBase: 0; border: none; }
        QTabBar::tab { background-color: transparent; color: #3c4043; padding: 8px 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: -4px; font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; min-width: 140px; max-width: 200px; }
        QTabBar::tab:selected { background-color: #ffffff; color: #1a73e8; }
        QTabBar::tab:hover:not(:selected) { background-color: rgba(255, 255, 255, 0.4); color: #202124; }
        QTabBar::close-button { subcontrol-position: right; border-radius: 50%; width: 14px; height: 14px; margin-left: 4px; }
        QTabBar::close-button:hover { background-color: #e8eaed; color: #3c4043; }
        QWidget#nav_bar_widget { background-color: #ffffff; border-bottom: 1px solid #dee1e6; }
        QWidget#url_container { background-color: #f1f3f4; border-radius: 16px; min-height: 28px; max-height: 28px; }
        QWidget#url_container:focus-within { background-color: #ffffff; border: 2px solid #1a73e8; }
        QPushButton { background-color: transparent; color: #5f6368; border: none; border-radius: 50%; min-width: 28px; min-height: 28px; max-width: 28px; max-height: 28px; font-size: 14px; }
        QPushButton:hover { background-color: rgba(0, 0, 0, 0.06); color: #202124; }
        QPushButton:pressed { background-color: rgba(0, 0, 0, 0.1); }
        QPushButton#new_tab_btn { font-size: 14px; border-radius: 50%; min-width: 24px; min-height: 24px; max-width: 24px; max-height: 24px; margin-bottom: 4px; margin-left: 4px; }
        QPushButton#menu_btn { font-size: 16px; }
        QPushButton#bookmark_btn { font-size: 13px; min-width: 20px; min-height: 20px; max-width: 20px; max-height: 20px; }
        QCheckBox#safe_search_switch { color: #5f6368; font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; spacing: 6px; }
        QCheckBox#safe_search_switch:hover { color: #202124; }
        QToolBar { background-color: #ffffff; border-bottom: 1px solid #dee1e6; border-top: none; spacing: 4px; padding: 2px 8px; min-height: 28px; }
        QToolButton { background-color: transparent; border: none; border-radius: 4px; padding: 2px 6px; color: #3c4043; font-size: 12px; font-family: 'Segoe UI', Arial, sans-serif; }
        QToolButton:hover { background-color: #f1f3f4; }
        QSplitter::handle { background-color: #dee1e6; }
        QMenu { background-color: #ffffff; border: 1px solid #dee1e6; border-radius: 8px; padding: 4px 0px; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; color: #202124; }
        QMenu::item { padding: 6px 32px 6px 16px; }
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
    def load_bookmarks(self):
        if os.path.exists(BOOKMARKS_FILE):
            try:
                with open(BOOKMARKS_FILE, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}
    def save_bookmarks(self):
        try:
            with open(BOOKMARKS_FILE, "w") as f:
                json.dump(self.bookmarks, f)
        except:
            pass
    def add_current_to_bookmarks(self):
        browser = self.get_current_browser()
        if browser:
            url = browser.url().toString()
            title = browser.title() or url
            if url and url != "about:blank":
                self.bookmarks[title[:15] + "..."] = url
                self.save_bookmarks()
                self.update_bookmarks_bar()
                self.status.showMessage("Adicionado aos favoritos!", 3000)
    def update_bookmarks_bar(self):
        self.bookmarks_bar.clear()
        for title, url in self.bookmarks.items():
            action = QAction(title, self)
            action.triggered.connect(lambda checked, u=url: self.open_url_in_current_tab(u))
            self.bookmarks_bar.addAction(action)
    def open_url_in_current_tab(self, url_str):
        browser = self.get_current_browser()
        if browser:
            browser.setUrl(QUrl(url_str))
    def clear_browser_data(self):
        profile = QWebEngineProfile.defaultProfile()
        profile.clearHttpCache()
        profile.cookieStore().deleteAllCookies()
        self.history_list.clear()
        QMessageBox.information(self, "Limpeza Completa", "Cookies, cache e histórico local foram removidos com sucesso!")
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
        current_data["moved_browser_original_title"] = self.tab_bar.tabText(target_tab_index)
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
        self.tab_changed(self.tab_bar.currentIndex())
    def safe_search_toggled(self, state):
        is_checked = (state == 2 or state == Qt.CheckState.Checked)
        if is_checked:
            self.status.showMessage("Verificando conexão com a rede Tor...", 4000)
            self.worker = TorCheckWorker()
            self.worker.result_signal.connect(self.handle_tor_check_result)
            self.worker.start()
        else:
            QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
            self.private_profile.setProxyConfigurator(lambda url: [])
            QWebEngineProfile.defaultProfile().setProxyConfigurator(lambda url: [])
            self.update_browsers_profile(QWebEngineProfile.defaultProfile())
            self.status.showMessage("Modo Tor Desativado - Perfil Padrão Ativo", 4000)
    def handle_tor_check_result(self, is_available):
        if is_available:
            proxy = QNetworkProxy(QNetworkProxy.ProxyType.Socks5Proxy, "127.0.0.1", 9050)
            QNetworkProxy.setApplicationProxy(proxy)
            self.private_profile.setProxyConfigurator(lambda url: [proxy])
            self.update_browsers_profile(self.private_profile)
            self.status.showMessage("⚠️ Modo Tor & Perfil Incógnito Ativados (Dados não serão salvos)", 5000)
        else:
            self.safe_search_switch.blockSignals(True)
            self.safe_search_switch.setChecked(False)
            self.safe_search_switch.blockSignals(False)
            QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
            QMessageBox.critical(self, "Falha no Modo Tor", "Não foi possível conectar à rede Tor.\n\nVerifique se o serviço 'tor' está rodando no seu Gentoo:\n# rc-service tor start")
            self.status.showMessage("Erro: Serviço Tor indisponível.", 5000)
    def update_browsers_profile(self, profile):
        for index in range(self.tab_bar.count()):
            tab_data = self.tab_bar.tabData(index)
            if tab_data:
                splitter = self.container.widget(tab_data.get("splitter_index"))
                if splitter:
                    for i in range(splitter.count()):
                        browser = splitter.widget(i)
                        if isinstance(browser, QWebEngineView):
                            current_url = browser.url()
                            new_page = QWebEnginePage(profile, browser)
                            browser.setPage(new_page)
                            browser.setUrl(current_url)
                            left_browser = browser
                            left_browser.urlChanged.connect(lambda qurl, b=left_browser: self.update_url_bar(qurl, b))
                            left_browser.titleChanged.connect(lambda title, b=left_browser: self.update_title(title, b))
                            left_browser.loadProgress.connect(self.update_progress)
                            left_browser.loadFinished.connect(self.load_finished)
                            left_browser.page().profile().downloadRequested.connect(self.handle_download)
    def show_menu(self):
        pos = self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomRight())
        pos.setX(pos.x() - self.browser_menu.sizeHint().width())
        self.browser_menu.exec(pos)
    def add_new_tab(self, qurl=None, label="Nova guia"):
        if qurl is None:
            qurl = QUrl("https://www.gentoo.org/")
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #dee1e6; width: 4px; }")
        profile = self.private_profile if self.safe_search_switch.isChecked() else QWebEngineProfile.defaultProfile()
        left_browser = QWebEngineView()
        new_page = QWebEnginePage(profile, left_browser)
        left_browser.setPage(new_page)
        left_browser.setUrl(qurl)
        splitter.addWidget(left_browser)
        splitter_index = self.container.addWidget(splitter)
        tab_index = self.tab_bar.addTab(label)
        self.tab_bar.setTabData(tab_index, {"splitter_index": splitter_index})
        self.tab_bar.setCurrentIndex(tab_index)
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
    def tab_changed(self, index):
        if index >= 0:
            tab_data = self.tab_bar.tabData(index)
            if tab_data and "splitter_index" in tab_data:
                splitter_index = tab_data["splitter_index"]
                self.container.setCurrentIndex(splitter_index)
                browser = self.get_current_browser()
                if browser:
                    self.url_bar.setText(browser.url().toString())
    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        if "." in text and " " not in text:
            if not text.startswith("http://") and not text.startswith("https://"):
                url = QUrl("https://" + text)
            else:
                url = QUrl(text)
        else:
            safe_param = "&safe=active" if self.safe_search_switch.isChecked() else ""
            url = QUrl(f"https://www.google.com/search?q={text}{safe_param}")
        active_browser = self.get_current_browser()
        if active_browser:
            active_browser.setUrl(url)
    def update_url_bar(self, url, browser):
        url_str = url.toString()
        if browser == self.get_current_browser():
            self.url_bar.setText(url_str)
        if not self.safe_search_switch.isChecked():
            if not self.history_list or self.history_list[-1] != url_str:
                self.history_list.append(url_str)
    def show_history(self):
        if not self.history_list:
            QMessageBox.information(self, "Histórico", "Nenhum histórico disponível (ou está no Modo Seguro).")
            return
        history_text = "\n".join(self.history_list[-20:])
        QMessageBox.information(self, "Histórico Recente", f"Últimas páginas visitadas:\n\n{history_text}")
    def update_title(self, title, browser):
        for index in range(self.tab_bar.count()):
            tab_data = self.tab_bar.tabData(index)
            if tab_data:
                splitter = self.container.widget(tab_data.get("splitter_index"))
                if splitter and (splitter.widget(0) == browser or (splitter.count() > 1 and splitter.widget(1) == browser)):
                    short_title = title[:15] + "..." if len(title) > 15 else title
                    if splitter.count() > 1:
                        short_title = f"[Split] {short_title}"
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
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Internet Surfer")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())