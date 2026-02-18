import sys
import os
import ctypes
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLineEdit, QVBoxLayout, 
    QHBoxLayout, QWidget, QPushButton, QTabWidget, 
    QMessageBox, QFileDialog, QListWidget, QListWidgetItem,
    QLabel, QProgressBar
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings, QWebEngineDownloadRequest

# --- КОНФИГУРАЦИЯ ---
HISTORY_FILE = "history.txt"
BOOKMARKS_FILE = "bookmarks.txt"
ICON_PATH = "icon.ico" # Убедись, что файл лежит рядом со скриптом

# --- СТИЛИ (CSS) ---
STYLESHEET = """
QMainWindow { background-color: #2b2b2b; }
QWidget#nav_bar { background-color: #3c3f41; border-bottom: 1px solid #222; }
QPushButton {
    background-color: transparent; color: #cccccc;
    border-radius: 5px; font-size: 18px; padding: 5px;
    min-width: 35px; min-height: 35px;
}
QPushButton:hover { background-color: #4e5254; color: white; }
QLineEdit {
    background-color: #1e1e1e; color: #e0e0e0;
    border: 1px solid #555; border-radius: 12px;
    padding: 5px 15px; font-size: 14px;
}
QLineEdit:focus { border: 1px solid #4b6eaf; }
QTabBar::tab {
    background: #3c3f41; color: #aaa; padding: 8px 15px;
    border-top-left-radius: 8px; border-top-right-radius: 8px;
    margin-right: 2px; min-width: 120px;
}
QTabBar::tab:selected { background: #2b2b2b; color: white; border-bottom: 2px solid #4b6eaf; }
QProgressBar { border: 1px solid #555; border-radius: 5px; text-align: center; color: white; }
QProgressBar::chunk { background-color: #4b6eaf; }
"""

# --- ОБРАБОТКА НОВЫХ ВКЛАДОК ---
class CustomWebPage(QWebEnginePage):
    def __init__(self, window):
        super().__init__(window)
        self.window = window

    def createWindow(self, _type):
        new_browser = self.window.add_new_tab(QUrl(""), "Загрузка...", switch_to=True)
        return new_browser.page()

# --- ИНСТРУМЕНТЫ РАЗРАБОТЧИКА ---
class DevToolsWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Developer Tools")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.resize(900, 600)
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)

    def inspect_page(self, page):
        self.browser.page().setInspectedPage(page)
        self.show()

# --- ЭЛЕМЕНТ ЗАГРУЗКИ ---
class DownloadItemWidget(QWidget):
    def __init__(self, download_item: QWebEngineDownloadRequest):
        super().__init__()
        self.download = download_item
        layout = QHBoxLayout(self)
        self.info_label = QLabel(download_item.suggestedFileName())
        self.p_bar = QProgressBar()
        self.btn_pause = QPushButton("⏸")
        self.btn_cancel = QPushButton("✖")
        self.btn_open = QPushButton("📂")
        self.btn_open.setEnabled(False)
        
        layout.addWidget(self.info_label, 2); layout.addWidget(self.p_bar, 2)
        layout.addWidget(self.btn_pause); layout.addWidget(self.btn_cancel); layout.addWidget(self.btn_open)

        self.download.receivedBytesChanged.connect(self.update_p)
        self.download.isFinishedChanged.connect(self.finished)
        self.btn_pause.clicked.connect(self.toggle_pause)
        self.btn_cancel.clicked.connect(self.download.cancel)
        self.btn_open.clicked.connect(self.open_f)

    def update_p(self):
        total = self.download.totalBytes()
        if total > 0: self.p_bar.setValue(int(self.download.receivedBytes() * 100 / total))

    def toggle_pause(self):
        if self.download.isPaused(): self.download.resume(); self.btn_pause.setText("⏸")
        else: self.download.pause(); self.btn_pause.setText("▶")

    def finished(self):
        if self.download.isFinished():
            self.p_bar.setValue(100)
            if self.download.state() == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
                self.btn_open.setEnabled(True)

    def open_f(self):
        path = os.path.normpath(os.path.join(self.download.downloadDirectory(), self.download.downloadFileName()))
        try: os.startfile(path)
        except: pass

class DownloadManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Загрузки")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.resize(650, 300)
        layout = QVBoxLayout(self)
        self.list = QListWidget()
        layout.addWidget(self.list)

    def add_download(self, dl):
        item = QListWidgetItem(self.list)
        widget = DownloadItemWidget(dl)
        item.setSizeHint(widget.sizeHint())
        self.list.addItem(item)
        self.list.setItemWidget(item, widget)
        self.show()

# --- ИСТОРИЯ И ЗАКЛАДКИ ---
class ListManagerWindow(QWidget):
    def __init__(self, title, file_path, open_callback):
        super().__init__()
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(ICON_PATH))
        self.resize(400, 500)
        self.file_path = file_path
        self.open_callback = open_callback
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.handle_double_click)
        btn_clear = QPushButton("🗑 Очистить всё")
        btn_clear.clicked.connect(self.clear_data)
        layout.addWidget(self.list_widget); layout.addWidget(btn_clear)

    def refresh(self):
        self.list_widget.clear()
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if line.strip(): self.list_widget.addItem(line.strip())

    def handle_double_click(self, item):
        url = item.text().split(" | ")[-1] if " | " in item.text() else item.text()
        self.open_callback(QUrl(url))
        self.hide()

    def clear_data(self):
        if os.path.exists(self.file_path): os.remove(self.file_path)
        self.list_widget.clear()

# --- ГЛАВНОЕ ОКНО ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Skyfire Browser")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.resize(1280, 720)
        self.setStyleSheet(STYLESHEET)

        self.dl_manager = DownloadManager()
        self.history_window = ListManagerWindow("История", HISTORY_FILE, self.add_new_tab)
        self.bookmarks_window = ListManagerWindow("Закладки", BOOKMARKS_FILE, self.add_new_tab)
        self.dev_tools = DevToolsWindow(self)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.tab_changed)

        # ПАНЕЛЬ УПРАВЛЕНИЯ
        nav_container = QWidget()
        nav_container.setObjectName("nav_bar")
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(5, 5, 5, 5)

        btn_back = QPushButton("◀")
        btn_back.clicked.connect(lambda: self.current_browser().back())
        
        btn_forward = QPushButton("▶")
        btn_forward.clicked.connect(lambda: self.current_browser().forward())
        
        btn_reload = QPushButton("🔄")
        btn_reload.clicked.connect(lambda: self.current_browser().reload())

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Поиск или URL...")
        self.url_bar.returnPressed.connect(self.navigate)

        btn_star = QPushButton("⭐")
        btn_star.clicked.connect(self.save_bookmark)

        btn_book = QPushButton("🔖")
        btn_book.clicked.connect(self.show_bookmarks)

        btn_hist = QPushButton("🕒")
        btn_hist.clicked.connect(self.show_history)

        btn_dl = QPushButton("📥")
        btn_dl.clicked.connect(self.dl_manager.show)

        btn_dev = QPushButton("🛠")
        btn_dev.clicked.connect(self.open_dev_tools)

        btn_add = QPushButton("➕")
        btn_add.clicked.connect(lambda: self.add_new_tab())

        for w in [btn_back, btn_forward, btn_reload, self.url_bar, btn_star, btn_book, btn_hist, btn_dl, btn_dev, btn_add]:
            nav_layout.addWidget(w)

        main_layout = QVBoxLayout()
        container = QWidget(); container.setLayout(main_layout)
        main_layout.addWidget(nav_container); main_layout.addWidget(self.tabs)
        main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)
        self.setCentralWidget(container)

        self.add_new_tab(QUrl("https://b1tneym42.github.io/Sky-Dial/"), "Sky-Dial")

    def add_new_tab(self, qurl=None, label="Sky-Dial", switch_to=True):
        if not qurl or qurl == "": qurl = QUrl("https://b1tneym42.github.io/Sky-Dial/")
        
        browser = QWebEngineView()
        browser.setPage(CustomWebPage(self))
        
        s = browser.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        
        browser.page().featurePermissionRequested.connect(self.handle_permission_request)
        browser.page().profile().downloadRequested.connect(self.on_download_requested)
        browser.urlChanged.connect(lambda q, b=browser: self.on_url_change(q, b))
        browser.loadFinished.connect(lambda _, b=browser: self.update_title(b))
        
        if isinstance(qurl, QUrl) and qurl.isValid(): browser.setUrl(qurl)
        
        i = self.tabs.addTab(browser, label)
        if switch_to: self.tabs.setCurrentIndex(i)
        return browser

    def on_download_requested(self, download):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", download.suggestedFileName())
        if path:
            download.setDownloadDirectory(os.path.dirname(path))
            download.setDownloadFileName(os.path.basename(path))
            download.accept()
            self.dl_manager.add_download(download)
        else: download.cancel()

    def handle_permission_request(self, url, feature):
        reply = QMessageBox.question(self, "Разрешение", f"Разрешить {url.host()} доступ к системе?")
        policy = QWebEnginePage.PermissionPolicy.PermissionGrantedByUser if reply == QMessageBox.StandardButton.Yes \
                 else QWebEnginePage.PermissionPolicy.PermissionDeniedByUser
        self.current_browser().page().setFeaturePermission(url, feature, policy)

    def open_dev_tools(self): self.dev_tools.inspect_page(self.current_browser().page())

    def on_url_change(self, q, browser):
        url_str = q.toString()
        if browser == self.current_browser(): self.url_bar.setText(url_str)
        if url_str.strip() and "devtools" not in url_str:
            with open(HISTORY_FILE, "a", encoding="utf-8") as f: f.write(url_str + "\n")

    def save_bookmark(self):
        url = self.current_browser().url().toString()
        title = self.current_browser().page().title()
        with open(BOOKMARKS_FILE, "a", encoding="utf-8") as f: f.write(f"{title} | {url}\n")
        QMessageBox.information(self, "Закладки", "Сохранено!")

    def show_history(self): self.history_window.refresh(); self.history_window.show()
    def show_bookmarks(self): self.bookmarks_window.refresh(); self.bookmarks_window.show()
    def update_title(self, browser):
        i = self.tabs.indexOf(browser)
        if i != -1: self.tabs.setTabText(i, browser.page().title()[:15])

    def current_browser(self): return self.tabs.currentWidget()

    def navigate(self):
        u = self.url_bar.text()
        if not u.startswith(('http', 'file', 'https')): u = 'https://' + u
        self.current_browser().setUrl(QUrl(u))

    def tab_changed(self, i):
        if self.current_browser(): self.url_bar.setText(self.current_browser().url().toString())

    def close_tab(self, i):
        if self.tabs.count() > 1: self.tabs.removeTab(i)

if __name__ == "__main__":
    # Фикс для иконки в панели задач Windows
    my_app_id = 'sky.dial.browser.v1'
    try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)
    except: pass

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICON_PATH)) # Основная иконка приложения

    window = MainWindow()
    window.show()
    sys.exit(app.exec())