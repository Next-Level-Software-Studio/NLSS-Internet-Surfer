import sys, os, json
from PyQt6.QtCore import QUrl, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLineEdit, QStatusBar, QFileDialog, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabBar, QStackedWidget, QMenu, QCheckBox, QSplitter, QLabel, QToolBar, QComboBox, QFormLayout)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEngineProfile, QWebEnginePage, QWebEngineSettings
from PyQt6.QtGui import QAction
from PyQt6.QtNetwork import QNetworkProxy, QNetworkAccessManager, QNetworkRequest, QNetworkReply

BOOKMARKS_FILE = os.path.expanduser("~/.internet_surfer_bookmarks.json")

class SilentWebEnginePage(QWebEnginePage):
    """Classe personalizada para silenciar logs e filtrar links de navegação."""
    
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # Silencia os logs de JavaScript no terminal
        pass

    def acceptNavigationRequest(self, url: QUrl, navigationType, isMainFrame: bool) -> bool:
        """
        Função executada sempre que o navegador tenta aceder a qualquer link.
        """
        url_str = url.toString()
        
        # Ignora páginas em branco internas
        if url_str == "about:blank":
            return True
            
        # =========================================================================
        # PONTO DE INSERÇÃO: SEU CÓDIGO DE VALIDAÇÃO
        # =========================================================================
        # Substitua a lógica abaixo pelo seu sistema de verificação de confiança.
        # url_str contém o link completo que o utilizador está a tentar abrir.
        
        link_confiavel = self.verificar_se_link_e_confiavel(url_str)
        
        if not link_confiavel:
            print(f"[BLOQUEADO] O acesso ao link foi impedido por segurança: {url_str}")
            # Retornar False cancela a navegação e o link não abre
            return False
            
        # =========================================================================
        
        # Retornar True permite que o site carregue normalmente
        return super().acceptNavigationRequest(url, navigationType, isMainFrame)

    def verificar_se_link_e_confiavel(self, url_da_pagina: str) -> bool:
        """
        PLACEHOLDER: Insira aqui a lógica do seu código desenvolvido.
        Deve retornar True se for seguro, ou False se for para bloquear.
        """
        # Exemplo simples (exclui sites que contenham 'malware' no nome):
        if "malware" in url_da_pagina.lower():
            return False
            
        return True


class TorCheckWorker(QThread):
    result_signal = pyqtSignal(bool)
    
    def run(self):
        manager = QNetworkAccessManager()
        proxy = QNetworkProxy(QNetworkProxy.ProxyType.Socks5Proxy, "127.0.0.1", 9050)
        manager.setProxy(proxy)
        request = QNetworkRequest(QUrl("https://check.torproject.org/api/ip"))
        
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
        save_btn.setStyleSheet("""
            QPushButton { background-color: #1a73e8; color: white; border: none; border-radius: 4px; padding: 8px; font-weight: bold; min-width: 100px; max-width: 150px; }
            QPushButton:hover { background-color: #1557b0; }
        """)
        save_btn.clicked.connect(self.apply_settings)
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def apply_settings(self):
        for profile in [self.default_profile, self.private_profile]:
            settings = profile.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, self.js_checkbox.isChecked())
            settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, self.plugins_checkbox.isChecked())
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, self.popups_checkbox.isChecked())
            settings.setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, self.screen_capture_checkbox.isChecked())
            
            cookie_policy = self.cookies_combo.currentIndex()
            if cookie_policy == 0:
                profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
            else:
                profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
                
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
        
        self.default_profile = QWebEngineProfile.defaultProfile()
        self.private_profile = QWebEngineProfile("PrivateProfile", self)
        self.private_profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
        
        self.default_profile.permissionRequested.connect(self.handle_permission_requested)
        self.private_profile.permissionRequested.connect(self.handle_permission_requested)
        
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
        self.browser_menu.addAction("🛡️ Definições e Permissões").triggered.connect(self.open_settings_window)
        self.browser_menu.addSeparator()
        self.browser_menu.addAction("Histórico").triggered.connect(self.show_history)
        self.browser_menu.addAction("Limpar Dados de Navegação (Cookies/Cache)").triggered.connect(self.clear_browser_data)
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

    def handle_permission_requested(self, request):
        feature = request.feature()
        feature_name = "Localização"
        if feature == QWebEngineProfile.PermissionFeature.MediaAudioCapture: feature_name = "Microfone"
        elif feature == QWebEngineProfile.PermissionFeature.MediaVideoCapture: feature_name = "Câmara de Vídeo"
        elif feature == QWebEngineProfile.PermissionFeature.MediaAudioVideoCapture: feature_name = "Câmara e Microfone"
            
        ret = QMessageBox.question(self, "Pedido de Permissão", f"O site {request.origin().toString()} quer aceder a: {feature_name}. Permitir?")
        request.accept() if ret == QMessageBox.StandardButton.Yes else request.reject()

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
        QPushButton#new_tab_btn { font-size: 14px; border-radius: 50%; min-width: 24px; min-height: 24px; max-width: 24px; max-height: 24px; margin-bottom: 4px; margin-left: 4px; }
        QCheckBox#safe_search_switch { color: #5f6368; font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; spacing: 6px; }
        QToolBar { background-color: #ffffff; border-bottom: 1px solid #dee1e6; border-top: none; spacing: 4px; padding: 2px 8px; min-height: 28px; }
        QMenu { background-color: #ffffff; border: 1px solid #dee1e6; border-radius: 8px; padding: 4px 0px; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; color: #202124; }
        QMenu::item { padding: 6px 32px 6px 16px; }
        QMenu::item:selected { background-color: #f1f3f4; }
        """
        self.setStyleSheet(qss)

    def open_settings_window(self):
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.default_profile, self.private_profile)
        self.settings_window.show()
        self.settings_window.raise_()

    def load_bookmarks(self):
        if os.path.exists(BOOKMARKS_FILE):
            try:
                with open(BOOKMARKS_FILE, "r") as f: return json.load(f)
            except: return {}
        return {}

    def save_bookmarks(self):
        try:
            with open(BOOKMARKS_FILE, "w") as f: json.dump(self.bookmarks, f)
        except: pass

    def add_current_to_bookmarks(self):
        browser = self.get_current_browser()
        if browser:
            url = browser.url().toString()
            title = browser.title() or url
            if url and url != "about:blank":
                self.bookmarks[title[:15] + "..."] = url
                self.save_bookmarks()
                self.update_bookmarks_bar()

    def update_bookmarks_bar(self):
        self.bookmarks_bar.clear()
        for title, url in self.bookmarks.items():
            action = QAction(title, self)
            action.triggered.connect(lambda checked, u=url: self.open_url_in_current_tab(u))
            self.bookmarks_bar.addAction(action)

    def open_url_in_current_tab(self, url_str):
        browser = self.get_current_browser()
        if browser: browser.setUrl(QUrl(url_str))

    def clear_browser_data(self):
        self.default_profile.clearHttpCache()
        self.default_profile.cookieStore().deleteAllCookies()
        QMessageBox.information(self, "Limpeza", "Dados limpos!")

    def show_tab_context_menu(self, point):
        tab_index = self.tab_bar.tabAt(point)
        if tab_index == -1: return
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
        if not current_data or not target_data: return
        
        current_splitter = self.container.widget(current_data["splitter_index"])
        target_splitter = self.container.widget(target_data["splitter_index"])
        target_browser = target_splitter.widget(0)
        
        if target_browser:
            target_splitter.removeWidget(target_browser)
            current_splitter.addWidget(target_browser)
            current_data["moved_browser"] = target_browser
            current_data["moved_browser_original_title"] = self.tab_bar.tabText(target_tab_index)
            self.tab_bar.setTabData(current_tab_index, current_data)
            self.tab_bar.removeTab(target_tab_index)
            self.tab_changed(self.tab_bar.currentIndex())

    def unsplit_tab(self, tab_index):
        tab_data = self.tab_bar.tabData(tab_index)
        if not tab_data or "moved_browser" not in tab_data: return
        current_splitter = self.container.widget(tab_data["splitter_index"])
        moved_browser = tab_data["moved_browser"]
        
        if current_splitter.count() > 1 and moved_browser:
            current_splitter.removeWidget(moved_browser)
            new_splitter = QSplitter(Qt.Orientation.Horizontal)
            new_splitter.addWidget(moved_browser)
            new_splitter_index = self.container.addWidget(new_splitter)
            new_tab_index = self.tab_bar.addTab(tab_data.get("moved_browser_original_title", "Aba"))
            self.tab_bar.setTabData(new_tab_index, {"splitter_index": new_splitter_index})
            del tab_data["moved_browser"]
            self.tab_bar.setTabData(tab_index, tab_data)
        self.tab_changed(self.tab_bar.currentIndex())

    def safe_search_toggled(self, state):
        if state == 2 or state == Qt.CheckState.Checked:
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
                            new_page = SilentWebEnginePage(profile, browser)
                            browser.setPage(new_page)
                            browser.setUrl(current_url)
                            browser.urlChanged.connect(lambda qurl, b=browser: self.update_url_bar(qurl, b))
                            browser.titleChanged.connect(lambda title, b=browser: self.update_title(title, b))

    def show_menu(self):
        pos = self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomRight())
        pos.setX(pos.x() - self.browser_menu.sizeHint().width())
        self.browser_menu.exec(pos)

    def add_new_tab(self, qurl=None, label="Nova guia"):
        if qurl is None: qurl = QUrl("https://www.gentoo.org/")
        splitter = QSplitter(Qt.Orientation.Horizontal)
        profile = self.private_profile if self.safe_search_switch.isChecked() else self.default_profile
        
        left_browser = QWebEngineView()
        new_page = SilentWebEnginePage(profile, left_browser)
        left_browser.setPage(new_page)
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
            return splitter.widget(1) if splitter.count() > 1 and splitter.widget(1).hasFocus() else splitter.widget(0)
        return None

    def close_current_tab(self, index):
        if self.tab_bar.count() < 2: return
        tab_data = self.tab_bar.tabData(index)
        if tab_data and "splitter_index" in tab_data:
            splitter_widget = self.container.widget(tab_data["splitter_index"])
            if splitter_widget: splitter_widget.deleteLater()
        self.tab_bar.removeTab(index)

    def tab_changed(self, index):
        if index >= 0:
            tab_data = self.tab_bar.tabData(index)
            if tab_data and "splitter_index" in tab_data:
                self.container.setCurrentIndex(tab_data["splitter_index"])
                browser = self.get_current_browser()
                if browser: self.url_bar.setText(browser.url().toString())

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text: return
        url = QUrl(text) if text.startswith("http") else QUrl("https://" + text) if "." in text else QUrl(f"https://www.google.com/search?q={text}")
        active_browser = self.get_current_browser()
        if active_browser: active_browser.setUrl(url)

    def update_url_bar(self, url, browser):
        if browser == self.get_current_browser(): self.url_bar.setText(url.toString())

    def show_history(self): pass

    def update_title(self, title, browser):
        for index in range(self.tab_bar.count()):
            tab_data = self.tab_bar.tabData(index)
            if tab_data:
                splitter = self.container.widget(tab_data.get("splitter_index"))
                if splitter and (splitter.widget(0) == browser or (splitter.count() > 1 and splitter.widget(1) == browser)):
                    self.tab_bar.setTabText(index, title[:12] + "...")
                    break

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())