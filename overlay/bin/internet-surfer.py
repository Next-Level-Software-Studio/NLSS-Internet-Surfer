import sys, os, json
from PyQt6.QtCore import QUrl, Qt, QThread, pyqtSignal, QEventLoop
from urllib.parse import quote_plus
from PyQt6.QtWidgets import QApplication, QMainWindow, QLineEdit, QStatusBar, QFileDialog, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabBar, QStackedWidget, QMenu, QCheckBox, QSplitter, QLabel, QToolBar, QComboBox, QFormLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEngineProfile, QWebEnginePage, QWebEngineSettings
from PyQt6.QtGui import QAction
from PyQt6.QtNetwork import QNetworkProxy, QNetworkAccessManager, QNetworkRequest, QNetworkReply
support_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "usr", "share", "internet-explorer"))
if support_dir not in sys.path:
    sys.path.insert(0, support_dir)
from browser_support import BookmarksWindow, DownloadsWindow

BOOKMARKS_FILE = os.path.expanduser("~/.internet_surfer_bookmarks.json")

class SilentWebEnginePage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        self.permissionRequested.connect(self.handle_page_permission)

    def javaScriptConsoleMessage(self, *args):
        pass

    def acceptNavigationRequest(self, url: QUrl, navigationType, isMainFrame: bool) -> bool:
        url_str = url.toString()
        if url_str == "about:blank":
            return True
        if not self.verificar_se_link_e_confiavel(url_str):
            print(f"[BLOQUEADO] Link interceptado por segurança: {url_str}")
            return False
        return super().acceptNavigationRequest(url, navigationType, isMainFrame)

    def verificar_se_link_e_confiavel(self, url_da_pagina: str) -> bool:
        return "malware" not in url_da_pagina.lower()

    def handle_page_permission(self, request):
        feature = request.feature()
        feature_name = "Localização"
        if feature == QWebEnginePage.PermissionFeature.MediaAudioCapture:
            feature_name = "Microfone"
        elif feature == QWebEnginePage.PermissionFeature.MediaVideoCapture:
            feature_name = "Câmara de Vídeo"
        elif feature == QWebEnginePage.PermissionFeature.MediaAudioVideoCapture:
            feature_name = "Câmara e Microfone"
        parent_window = self.view().window() if self.view() else None
        allow = QMessageBox.question(parent_window, "Pedido de Permissão", f"O site {request.origin().toString()} quer aceder a: {feature_name}. Permitir?")
        request.accept() if allow == QMessageBox.StandardButton.Yes else request.reject()

class TorCheckWorker(QThread):
    result_signal = pyqtSignal(bool)

    def run(self):
        manager = QNetworkAccessManager()
        manager.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.Socks5Proxy, "127.0.0.1", 9050))
        reply = manager.get(QNetworkRequest(QUrl("https://check.torproject.org/api/ip")))
        loop = QEventLoop()
        reply.finished.connect(loop.quit)
        loop.exec()
        self.result_signal.emit(reply.error() == QNetworkReply.NetworkError.NoError)
        reply.deleteLater()

class SettingsWindow(QWidget):
    def __init__(self, default_profile, private_profile):
        super().__init__()
        self.default_profile = default_profile
        self.private_profile = private_profile
        self.setWindowTitle("Definições e Permissões")
        self.setGeometry(200, 200, 450, 400)
        self.setStyleSheet("background-color: #ffffff; font-family: 'Segoe UI', Arial, sans-serif;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel("Permissões do Navegador")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #202124; margin-bottom: 15px;")
        layout.addWidget(title)
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        self.js_checkbox = QCheckBox("Permitir JavaScript (Recomendado)")
        self.plugins_checkbox = QCheckBox("Permitir Plugins Web")
        self.popups_checkbox = QCheckBox("Permitir Bloqueio de Popups automáticos")
        self.screen_capture_checkbox = QCheckBox("Permitir Captura de Ecrã/Câmara/Microfone")
        self.cookies_combo = QComboBox()
        self.cookies_combo.addItems(["Aceitar todos os Cookies", "Bloquear Cookies de Terceiros", "Bloquear todos os Cookies"])
        settings = self.default_profile.settings()
        self.js_checkbox.setChecked(settings.testAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled))
        self.plugins_checkbox.setChecked(settings.testAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled))
        self.popups_checkbox.setChecked(settings.testAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled))
        form_layout.addRow(self.js_checkbox)
        form_layout.addRow(self.plugins_checkbox)
        form_layout.addRow(self.popups_checkbox)
        form_layout.addRow(self.screen_capture_checkbox)
        form_layout.addRow(QLabel("Gestão de Armazenamento/Cookies:"), self.cookies_combo)
        layout.addLayout(form_layout)
        layout.addStretch()
        save_btn = QPushButton("Aplicar Alterações")
        save_btn.setStyleSheet("QPushButton { background-color: #1a73e8; color: white; border: none; border-radius: 4px; padding: 8px; font-weight: bold; min-width: 100px; max-width: 150px; } QPushButton:hover { background-color: #1557b0; }")
        save_btn.clicked.connect(self.apply_settings)
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def apply_settings(self):
        for profile in (self.default_profile, self.private_profile):
            settings = profile.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, self.js_checkbox.isChecked())
            settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, self.plugins_checkbox.isChecked())
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, self.popups_checkbox.isChecked())
            settings.setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, self.screen_capture_checkbox.isChecked())
            profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies if self.cookies_combo.currentIndex() == 0 else QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
        QMessageBox.information(self, "Sucesso", "As novas permissões foram aplicadas com sucesso!")
        self.close()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Internet Surfer")
        self.setGeometry(100, 100, 1200, 800)
        self.settings_window = None
        self.history_list = []
        self.bookmarks = self.load_bookmarks()
        self.downloads = []
        self.default_profile = QWebEngineProfile.defaultProfile()
        self.private_profile = QWebEngineProfile("PrivateProfile", self)
        self.default_profile.downloadRequested.connect(self.handle_download_request)
        self.private_profile.downloadRequested.connect(self.handle_download_request)
        self.private_profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
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
        self.reload_btn.setObjectName("reload_btn")
        self.reload_btn.setToolTip("Recarregar")
        self.reload_btn.clicked.connect(lambda: self.get_current_browser().reload() if self.get_current_browser() else None)
        nav_layout.addWidget(self.reload_btn)
        self.home_btn = QPushButton("⌂")
        self.home_btn.setObjectName("home_btn")
        self.home_btn.setToolTip("Página inicial")
        self.home_btn.clicked.connect(self.go_home)
        nav_layout.addWidget(self.home_btn)
        self.url_container = QWidget()
        self.url_container.setObjectName("url_container")
        url_layout = QHBoxLayout(self.url_container)
        url_layout.setContentsMargins(10, 0, 10, 0)
        url_layout.setSpacing(4)
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("color: #5f6368; padding-left: 6px; padding-right: 4px;")
        url_layout.addWidget(search_icon)
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Pesquisar ou inserir endereço")
        self.url_bar.setClearButtonEnabled(True)
        self.url_bar.setStyleSheet("background: transparent; border: none; padding: 0;")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        url_layout.addWidget(self.url_bar)
        self.bookmark_btn = QPushButton("⭐")
        self.bookmark_btn.setObjectName("bookmark_btn")
        self.bookmark_btn.setToolTip("Adicionar aos favoritos")
        self.bookmark_btn.clicked.connect(self.add_current_to_bookmarks)
        url_layout.addWidget(self.bookmark_btn)
        nav_layout.addWidget(self.url_container, 1)
        self.safe_search_switch = QCheckBox("Pesquisa Segura")
        self.safe_search_switch.setObjectName("safe_search_switch")
        self.safe_search_switch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.safe_search_switch.stateChanged.connect(self.safe_search_toggled)
        self.safe_search_switch.setChecked(True)
        nav_layout.addWidget(self.safe_search_switch)
        self.menu_btn = QPushButton("☰")
        self.menu_btn.setObjectName("menu_btn")
        self.menu_btn.clicked.connect(self.show_menu)
        nav_layout.addWidget(self.menu_btn)
        self.browser_menu = QMenu(self)
        self.browser_menu.addAction("Novo separador").triggered.connect(lambda: self.add_new_tab())
        self.browser_menu.addAction("Nova aba").triggered.connect(lambda: self.add_new_tab())
        self.browser_menu.addSeparator()
        self.browser_menu.addAction("Histórico").triggered.connect(self.show_history)
        self.browser_menu.addAction("Transferências").triggered.connect(self.show_downloads)
        self.browser_menu.addSeparator()
        self.browser_menu.addAction("Marcadores, listas e grupos").triggered.connect(self.open_bookmarks_manager)
        self.browser_menu.addSeparator()
        self.browser_menu.addAction("Eliminar dados").triggered.connect(self.clear_browser_data)
        zoom_menu = self.browser_menu.addMenu("Zoom")
        zoom_menu.addAction("Aumentar").triggered.connect(self.zoom_in)
        zoom_menu.addAction("Reduzir").triggered.connect(self.zoom_out)
        zoom_menu.addAction("Resetar").triggered.connect(self.zoom_reset)
        self.browser_menu.addAction("Traduzir").triggered.connect(self.translate_current_page)
        self.browser_menu.addSeparator()
        self.browser_menu.addAction("Definições").triggered.connect(self.open_settings_window)
        self.addAction(QAction("Nova aba", self, shortcut="Ctrl+T", triggered=self.add_new_tab))
        self.addAction(QAction("Fechar aba", self, shortcut="Ctrl+W", triggered=lambda: self.close_current_tab(self.tab_bar.currentIndex())))
        self.addAction(QAction("Recarregar", self, shortcut="Ctrl+R", triggered=self.reload_current_page))
        self.addAction(QAction("Página inicial", self, shortcut="Alt+Home", triggered=self.go_home))
        main_layout.addWidget(nav_bar_widget)
        self.bookmarks_bar = QToolBar("Favoritos")
        self.bookmarks_bar.setMovable(False)
        main_layout.addWidget(self.bookmarks_bar)
        self.update_bookmarks_bar()
        self.container = QStackedWidget()
        main_layout.addWidget(self.container)
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.add_new_tab(QUrl("https://check.torproject.org/"), "Teste Tor")

    def apply_embedded_stylesheet(self):
        qss_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "usr", "share", "internet-explorer", "internet-surfer.qss"))
        if os.path.exists(qss_path):
            try:
                with open(qss_path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            except Exception:
                self.setStyleSheet("")
        else:
            self.setStyleSheet("")

    def open_settings_window(self):
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.default_profile, self.private_profile)
        self.settings_window.show()
        self.settings_window.raise_()

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
                display_title = title[:15] + "..." if len(title) > 15 else title
                self.bookmarks[display_title] = url
                self.save_bookmarks()
                self.update_bookmarks_bar()

    def update_bookmarks_bar(self):
        self.bookmarks_bar.clear()
        for title, url in self.bookmarks.items():
            btn = QPushButton(title)
            btn.setStyleSheet("padding: 2px 8px; color: #3c4043; border-radius: 4px;")
            btn.clicked.connect(lambda checked, u=url: self.open_url_in_current_tab(u))
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda point, t=title: self.show_bookmark_context_menu(point, t))
            self.bookmarks_bar.addWidget(btn)

    def show_bookmark_context_menu(self, point, title):
        sender_widget = self.sender()
        if not sender_widget:
            return
        menu = QMenu(self)
        remove_action = menu.addAction("❌ Remover dos Favoritos")
        action = menu.exec(sender_widget.mapToGlobal(point))
        if action == remove_action and title in self.bookmarks:
            del self.bookmarks[title]
            self.save_bookmarks()
            self.update_bookmarks_bar()

    def open_url_in_current_tab(self, url_str):
        browser = self.get_current_browser()
        if browser:
            browser.setUrl(QUrl(url_str))

    def clear_browser_data(self):
        self.default_profile.clearHttpCache()
        self.default_profile.cookieStore().deleteAllCookies()
        QMessageBox.information(self, "Limpeza", "Dados limpos!")

    def show_tab_context_menu(self, point):
        tab_index = self.tab_bar.tabAt(point)
        if tab_index == -1:
            return
        context_menu = QMenu(self)
        tab_data = self.tab_bar.tabData(tab_index)
        splitter = self.container.widget(tab_data["splitter_index"]) if tab_data else None
        if splitter and splitter.count() == 1:
            split_submenu = context_menu.addMenu("🖥️ Escolher aba para dividir")
            for i in range(self.tab_bar.count()):
                if i != tab_index:
                    action = QAction(self.tab_bar.tabText(i), self)
                    action.triggered.connect(lambda checked, c=tab_index, t=i: self.split_with_existing_tab(c, t))
                    split_submenu.addAction(action)
        elif splitter and splitter.count() > 1:
            unsplit_action = QAction("📺 Desfazer Vista Dividida", self)
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
        target_browser = target_splitter.widget(0) if target_splitter else None
        if target_browser:
            target_browser.setParent(None)
            current_splitter.addWidget(target_browser)
            current_data["moved_browser"] = target_browser
            current_data["moved_browser_original_title"] = self.tab_bar.tabText(target_tab_index)
            self.tab_bar.setTabData(current_tab_index, current_data)
            if target_splitter.count() == 0:
                self.container.removeWidget(target_splitter)
                target_splitter.deleteLater()
            self.tab_bar.removeTab(target_tab_index)
            self.tab_changed(self.tab_bar.currentIndex())

    def unsplit_tab(self, tab_index):
        tab_data = self.tab_bar.tabData(tab_index)
        if not tab_data or "moved_browser" not in tab_data:
            return
        current_splitter = self.container.widget(tab_data["splitter_index"])
        moved_browser = tab_data["moved_browser"]
        if current_splitter.count() > 1 and moved_browser:
            moved_browser.setParent(None)
            new_splitter = QSplitter(Qt.Orientation.Horizontal)
            new_splitter.addWidget(moved_browser)
            new_splitter_index = self.container.addWidget(new_splitter)
            new_tab_index = self.tab_bar.addTab(tab_data.get("moved_browser_original_title", "Aba"))
            self.tab_bar.setTabData(new_tab_index, {"splitter_index": new_splitter_index})
            del tab_data["moved_browser"]
            self.tab_bar.setTabData(tab_index, tab_data)
        self.tab_changed(self.tab_bar.currentIndex())

    def split_current_tab_with_new_browser(self):
        splitter = self.container.currentWidget()
        if splitter and isinstance(splitter, QSplitter):
            profile = self.private_profile if self.safe_search_switch.isChecked() else self.default_profile
            new_browser = QWebEngineView()
            new_page = SilentWebEnginePage(profile, new_browser)
            new_browser.setPage(new_page)
            new_browser.setUrl(QUrl("https://www.gentoo.org/"))
            splitter.addWidget(new_browser)
            new_browser.urlChanged.connect(lambda qurl, b=new_browser: self.update_url_bar(qurl, b))
            new_browser.titleChanged.connect(lambda title, b=new_browser: self.update_title(title, b))
            new_browser.setFocus()

    def toggle_splitter_orientation(self):
        splitter = self.container.currentWidget()
        if splitter and isinstance(splitter, QSplitter):
            splitter.setOrientation(Qt.Orientation.Vertical if splitter.orientation() == Qt.Orientation.Horizontal else Qt.Orientation.Horizontal)

    def safe_search_toggled(self, state):
        if state == Qt.CheckState.Checked:
            self.status.showMessage("Verificando rede Tor...")
            self.worker = TorCheckWorker()
            self.worker.result_signal.connect(self.handle_tor_check_result)
            self.worker.start()
        else:
            QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
            self.update_browsers_profile(self.default_profile)

    def handle_tor_check_result(self, is_available):
        if is_available:
            QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.Socks5Proxy, "127.0.0.1", 9050))
            self.private_profile.clearHttpCache()
            self.update_browsers_profile(self.private_profile)
            self.status.showMessage("⚠️ Modo Tor Ativado")
        else:
            self.safe_search_switch.setChecked(False)
            QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))

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
                            old_page = browser.page()
                            try:
                                browser.urlChanged.disconnect()
                                browser.titleChanged.disconnect()
                            except TypeError:
                                pass
                            new_page = SilentWebEnginePage(profile, browser)
                            browser.setPage(new_page)
                            browser.setUrl(current_url)
                            if old_page and old_page != new_page:
                                old_page.setParent(None)
                                old_page.deleteLater()
                            browser.urlChanged.connect(lambda qurl, b=browser: self.update_url_bar(qurl, b))
                            browser.titleChanged.connect(lambda title, b=browser: self.update_title(title, b))

    def cleanup_browser_pages(self):
        for index in range(self.tab_bar.count()):
            tab_data = self.tab_bar.tabData(index)
            if not tab_data:
                continue
            splitter = self.container.widget(tab_data.get("splitter_index"))
            if not splitter:
                continue
            for i in range(splitter.count()):
                browser = splitter.widget(i)
                if isinstance(browser, QWebEngineView):
                    page = browser.page()
                    if page:
                        browser.setPage(QWebEnginePage(self.default_profile, browser))
                        page.setParent(None)
                        page.deleteLater()

    def closeEvent(self, event):
        self.cleanup_browser_pages()
        super().closeEvent(event)

    def show_menu(self):
        pos = self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomRight())
        pos.setX(pos.x() - self.browser_menu.sizeHint().width())
        self.browser_menu.exec(pos)

    def handle_download_request(self, download):
        default_name = os.path.basename(download.url().path()) or "download"
        suggested_path = os.path.join(os.path.expanduser("~"), default_name)
        save_path, _ = QFileDialog.getSaveFileName(self, "Guardar Transferência", suggested_path)
        if not save_path:
            download.cancel()
            return
        download.setPath(save_path)
        download.accept()
        entry = {"url": download.url().toString(), "path": save_path, "status": "Em progresso"}
        self.downloads.append(entry)
        download.downloadProgress.connect(lambda received, total, e=entry: self.update_download_progress(e, received, total))
        download.finished.connect(lambda e=entry, d=download: self.finish_download(e, d))
        self.status.showMessage(f"Transferência iniciada: {os.path.basename(save_path)}", 5000)

    def update_download_progress(self, entry, received, total):
        if total > 0:
            entry["status"] = f"{int(received * 100 / total)}%"
        else:
            entry["status"] = "Em progresso"

    def finish_download(self, entry, download):
        status = "Concluído"
        try:
            state = download.state()
            if hasattr(download, 'DownloadState'):
                if state == download.DownloadState.DownloadCancelled:
                    status = "Cancelado"
                elif state != download.DownloadState.DownloadCompleted:
                    status = "Interrompido"
        except Exception:
            pass
        entry["status"] = status
        self.status.showMessage(f"Transferência {status}: {os.path.basename(entry['path'])}", 5000)

    def show_downloads(self):
        DownloadsWindow(self, self.downloads).exec()

    def open_bookmarks_manager(self):
        BookmarksWindow(self, self.bookmarks).exec()

    def translate_current_page(self):
        browser = self.get_current_browser()
        if not browser:
            return
        url = browser.url().toString()
        if not url or url == "about:blank":
            QMessageBox.information(self, "Traduzir", "Nenhuma página válida para tradução.")
            return
        translate_url = QUrl(f"https://translate.google.com/translate?sl=auto&tl=pt&u={quote_plus(url)}")
        browser.setUrl(translate_url)

    def zoom_in(self):
        b = self.get_current_browser()
        if b:
            try:
                b.setZoomFactor(b.zoomFactor() + 0.1)
            except Exception:
                pass

    def reload_current_page(self):
        browser = self.get_current_browser()
        if browser:
            browser.reload()

    def zoom_out(self):
        b = self.get_current_browser()
        if b:
            try:
                b.setZoomFactor(max(0.25, b.zoomFactor() - 0.1))
            except Exception:
                pass

    def zoom_reset(self):
        b = self.get_current_browser()
        if b:
            try:
                b.setZoomFactor(1.0)
            except Exception:
                pass

    def go_home(self):
        browser = self.get_current_browser()
        if browser:
            browser.setUrl(QUrl("https://www.google.com/"))

    def add_new_tab(self, qurl=None, label="Nova guia"):
        if qurl is None:
            qurl = QUrl("https://www.gentoo.org/")
        splitter = QSplitter(Qt.Orientation.Horizontal)
        profile = self.private_profile if self.safe_search_switch.isChecked() else self.default_profile
        left_browser = QWebEngineView()
        left_browser.setPage(SilentWebEnginePage(profile, left_browser))
        left_browser.setUrl(qurl)
        splitter.addWidget(left_browser)
        splitter_index = self.container.addWidget(splitter)
        tab_index = self.tab_bar.addTab(label)
        self.tab_bar.setTabData(tab_index, {"splitter_index": splitter_index})
        self.tab_bar.setCurrentIndex(tab_index)
        left_browser.urlChanged.connect(lambda qurl, b=left_browser: self.update_url_bar(qurl, b))
        left_browser.titleChanged.connect(lambda title, b=left_browser: self.update_title(title, b))

    def get_current_browser(self):
        splitter = self.container.currentWidget()
        if splitter and isinstance(splitter, QSplitter):
            for i in range(splitter.count()):
                w = splitter.widget(i)
                if w and w.hasFocus():
                    return w
            if splitter.count() > 0:
                return splitter.widget(0)
        return None

    def close_current_tab(self, index):
        if self.tab_bar.count() < 2:
            return
        tab_data = self.tab_bar.tabData(index)
        if tab_data and "splitter_index" in tab_data:
            splitter_widget = self.container.widget(tab_data["splitter_index"])
            if splitter_widget:
                for i in range(splitter_widget.count()):
                    widget = splitter_widget.widget(i)
                    if isinstance(widget, QWebEngineView) and widget.page():
                        old_page = widget.page()
                        widget.setPage(QWebEnginePage(self.default_profile, widget))
                        old_page.setParent(None)
                        old_page.deleteLater()
                splitter_widget.deleteLater()
        self.tab_bar.removeTab(index)

    def tab_changed(self, index):
        if index >= 0:
            tab_data = self.tab_bar.tabData(index)
            if tab_data and "splitter_index" in tab_data:
                self.container.setCurrentIndex(tab_data["splitter_index"])
                browser = self.get_current_browser()
                if browser:
                    self.url_bar.setText(browser.url().toString())

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        url = QUrl(text) if text.startswith("http") else QUrl("https://" + text) if "." in text else QUrl(f"https://www.google.com/search?q={text}")
        active_browser = self.get_current_browser()
        if active_browser:
            active_browser.setUrl(url)

    def record_history(self, url):
        url_str = url.toString()
        if url_str and url_str != "about:blank" and (not self.history_list or self.history_list[-1] != url_str):
            self.history_list.append(url_str)

    def update_url_bar(self, url, browser):
        if browser == self.get_current_browser():
            self.url_bar.setText(url.toString())
            self.record_history(url)

    def show_history(self):
        if not self.history_list:
            QMessageBox.information(self, "Histórico", "Nenhum histórico disponível.")
            return
        history_text = "\n".join(self.history_list[-15:][::-1])
        QMessageBox.information(self, "Histórico recente", history_text)

    def update_title(self, title, browser):
        for index in range(self.tab_bar.count()):
            tab_data = self.tab_bar.tabData(index)
            if tab_data:
                splitter = self.container.widget(tab_data.get("splitter_index"))
                if splitter:
                    for i in range(splitter.count()):
                        if splitter.widget(i) == browser:
                            self.tab_bar.setTabText(index, title[:12] + "...")
                            return

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
