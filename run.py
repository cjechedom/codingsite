"""
KeySnap - AMOLED-dark, curved, developer-styled editor
Features:
- Multi-tab code editor (Python, JS, C, C++, HTML, CSS)
- Syntax highlighting
- Popup autocomplete (Ctrl+Space) with buffer + keyword packs
- TXT / CONFIG / DOCX keyword extraction
- Folder keyword scanning
- Run Python/Tkinter (F5) via subprocess
- Help tab + About dialog
- AMOLED-black UI with medium curves and slightly curved popup
"""

import sys
import os
import re
import subprocess
from zipfile import ZipFile

from PyQt5.QtCore import Qt, QStringListModel, QRegExp
from PyQt5.QtGui import (
    QFont,
    QColor,
    QTextCharFormat,
    QSyntaxHighlighter,
    QPalette,
)
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPlainTextEdit,
    QFileDialog,
    QMessageBox,
    QAction,
    QTabWidget,
    QCompleter,
    QVBoxLayout,
    QWidget,
    QStatusBar,
)


# ============================================================
# Keyword system (TXT / CONFIG / DOCX)
# ============================================================

WORD_RE = re.compile(r"[A-Za-z_]{3,}")
KEY_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_\-]{2,}")

PY_KEYWORDS = [
    "False", "None", "True", "and", "as", "assert", "async", "await", "break",
    "class", "continue", "def", "del", "elif", "else", "except", "finally",
    "for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal",
    "not", "or", "pass", "raise", "return", "try", "while", "with", "yield"
]

JS_KEYWORDS = [
    "await", "break", "case", "catch", "class", "const", "continue", "debugger",
    "default", "delete", "do", "else", "enum", "export", "extends", "false",
    "finally", "for", "function", "if", "implements", "import", "in",
    "instanceof", "interface", "let", "new", "null", "package", "private",
    "protected", "public", "return", "super", "switch", "static", "this",
    "throw", "true", "try", "typeof", "var", "void", "while", "with", "yield"
]

C_KEYWORDS = [
    "auto", "break", "case", "char", "const", "continue", "default", "do",
    "double", "else", "enum", "extern", "float", "for", "goto", "if", "inline",
    "int", "long", "register", "restrict", "return", "short", "signed",
    "sizeof", "static", "struct", "switch", "typedef", "union", "unsigned",
    "void", "volatile", "while"
]

CPP_KEYWORDS = [
    "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor",
    "bool", "break", "case", "catch", "char", "char16_t", "char32_t", "class",
    "compl", "const", "constexpr", "const_cast", "continue", "decltype",
    "default", "delete", "do", "double", "dynamic_cast", "else", "enum",
    "explicit", "export", "extern", "false", "float", "for", "friend", "goto",
    "if", "inline", "int", "long", "mutable", "namespace", "new", "noexcept",
    "not", "not_eq", "nullptr", "operator", "or", "or_eq", "private",
    "protected", "public", "register", "reinterpret_cast", "return", "short",
    "signed", "sizeof", "static", "static_assert", "static_cast", "struct",
    "switch", "template", "this", "thread_local", "throw", "true", "try",
    "typedef", "typeid", "typename", "union", "unsigned", "using", "virtual",
    "void", "volatile", "wchar_t", "while", "xor", "xor_eq"
]

HTML_KEYWORDS = [
    "html", "head", "body", "title", "meta", "link", "script", "style", "div",
    "span", "p", "a", "img", "ul", "ol", "li", "table", "thead", "tbody", "tr",
    "td", "th", "form", "input", "button", "select", "option", "textarea",
    "label", "header", "footer", "nav", "section", "article", "aside", "main",
    "h1", "h2", "h3", "h4", "h5", "h6"
]

CSS_KEYWORDS = [
    "color", "background", "background-color", "border", "margin", "padding",
    "display", "position", "top", "bottom", "left", "right", "float", "clear",
    "z-index", "width", "height", "min-width", "max-width", "font",
    "font-size", "font-weight", "font-family", "line-height", "text-align",
    "text-decoration"
]

JSON_KEYS = [
    "id", "name", "title", "type", "value", "items", "data", "attributes",
    "properties", "metadata", "created", "updated", "status", "user", "role",
    "email", "token", "session", "count", "total", "limit", "offset", "page",
    "results", "error", "message", "success", "code", "version", "config",
    "options", "settings", "theme", "host", "port", "method", "headers",
    "body", "params", "query", "response", "timeout"
]

BASE_KEYWORDS = sorted(set(
    PY_KEYWORDS
    + JS_KEYWORDS
    + C_KEYWORDS
    + CPP_KEYWORDS
    + HTML_KEYWORDS
    + CSS_KEYWORDS
    + JSON_KEYS
))


def extract_keywords_from_txt(text: str):
    """Extract simple word-based keywords from plain text."""
    words = WORD_RE.findall(text)
    return sorted(set(w.lower() for w in words))


def extract_keywords_from_docx(path: str):
    """
    Extract keywords from a DOCX file by reading word/document.xml.
    No external libraries required.
    """
    try:
        with ZipFile(path, "r") as z:
            if "word/document.xml" not in z.namelist():
                return []
            xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
    except Exception:
        return []
    words = WORD_RE.findall(xml)
    return sorted(set(w.lower() for w in words))


def extract_keywords_from_config(text: str):
    """Extract key-like tokens from config-style text."""
    keys = KEY_RE.findall(text)
    return sorted(set(k.lower() for k in keys))


def extract_keywords_from_any_file(path: str):
    """
    Dispatch keyword extraction based on file extension.
    - .docx → DOCX XML parsing
    - config-like → KEY_RE
    - everything else → plain text words
    """
    ext = os.path.splitext(path)[1].lower()

    if ext == ".docx":
        return extract_keywords_from_docx(path)[:500]

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception:
        return []

    if ext in [".json", ".xml", ".ini", ".cfg", ".conf", ".env", ".yaml", ".yml", ".toml"]:
        return extract_keywords_from_config(text)[:500]

    return extract_keywords_from_txt(text)[:500]


class KeywordPacks:
    """Container for multiple keyword packs merged into autocomplete."""

    def __init__(self):
        self.packs = []

    def add_pack(self, keywords):
        if not keywords:
            return
        self.packs.append(sorted(set(keywords)))

    def all_keywords(self):
        merged = set(BASE_KEYWORDS)
        for p in self.packs:
            merged.update(p)
        return sorted(merged)


# ============================================================
# Syntax highlighter
# ============================================================

class CodeHighlighter(QSyntaxHighlighter):
    """Simple multi-language syntax highlighter."""

    def __init__(self, parent, language="python"):
        super().__init__(parent)
        self.language = language
        self.rules = []
        self._build_rules()

    @staticmethod
    def _fmt(color, bold=False):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Bold)
        return fmt

    def _build_rules(self):
        self.rules = []

        if self.language == "python":
            kws = PY_KEYWORDS
        elif self.language == "javascript":
            kws = JS_KEYWORDS
        elif self.language in ("c", "cpp"):
            kws = C_KEYWORDS + CPP_KEYWORDS
        elif self.language in ("html", "css"):
            kws = HTML_KEYWORDS + CSS_KEYWORDS
        else:
            kws = []

        # Keywords
        kw_fmt = self._fmt("#c792ea", True)
        for kw in kws:
            pattern = QRegExp(r"\b" + kw + r"\b")
            self.rules.append((pattern, kw_fmt))

        # Strings
        string_fmt = self._fmt("#c3e88d")
        self.rules.append((QRegExp(r"\".*\""), string_fmt))
        self.rules.append((QRegExp(r"\'.*\'"), string_fmt))

        # Comments
        comment_fmt = self._fmt("#546e7a")
        if self.language in ("python", "javascript", "c", "cpp"):
            self.rules.append((QRegExp(r"//[^\n]*"), comment_fmt))
            self.rules.append((QRegExp(r"#[^\n]*"), comment_fmt))

        # Numbers
        number_fmt = self._fmt("#f78c6c")
        self.rules.append((QRegExp(r"\b[0-9]+\b"), number_fmt))

    def set_language(self, language):
        self.language = language
        self._build_rules()
        self.rehighlight()

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            index = pattern.indexIn(text, 0)
            while index >= 0:
                length = pattern.matchedLength()
                self.setFormat(index, length, fmt)
                index = pattern.indexIn(text, index + length)


# ============================================================
# Code editor with popup autocomplete
# ============================================================

class CodeEditor(QPlainTextEdit):
    """
    Core editor widget:
    - syntax highlighting
    - popup autocomplete (Ctrl+Space)
    - dynamic buffer + keyword packs
    """

    def __init__(self, keyword_packs: KeywordPacks, language="python", parent=None):
        super().__init__(parent)

        self.keyword_packs = keyword_packs
        self.language = language
        self.file_path = None

        # Developer font
        font = QFont("Consolas", 11)
        self.setFont(font)
        self.setTabStopDistance(4 * self.fontMetrics().width(" "))

        # Highlighter
        self.highlighter = CodeHighlighter(self.document(), language=self.language)

        # Completer
        self.completer = QCompleter(self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setWrapAround(False)
        self.completer.activated.connect(self.insert_completion)

        self.model = QStringListModel()
        self.completer.setModel(self.model)
        self.setCompleter(self.completer)

        # Update completions when text changes
        self.textChanged.connect(self.update_completions)

    # ---------- Language ----------

    def set_language(self, language):
        self.language = language
        self.highlighter.set_language(language)

    # ---------- Completer plumbing ----------

    def setCompleter(self, completer):
        if hasattr(self, "completer") and self.completer:
            try:
                self.completer.disconnect()
            except Exception:
                pass

        self.completer = completer
        if not self.completer:
            return

        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)

    def insert_completion(self, completion):
        tc = self.textCursor()
        extra = completion[len(self.completer.completionPrefix()):]
        tc.insertText(extra)
        self.setTextCursor(tc)

    def text_under_cursor(self):
        tc = self.textCursor()
        tc.select(tc.WordUnderCursor)
        return tc.selectedText()

    def keyPressEvent(self, event):
        # Let completer handle navigation keys when visible
        if self.completer and self.completer.popup().isVisible():
            if event.key() in (
                Qt.Key_Enter,
                Qt.Key_Return,
                Qt.Key_Escape,
                Qt.Key_Tab,
                Qt.Key_Backtab,
            ):
                event.ignore()
                return

        super().keyPressEvent(event)

        # Trigger popup with Ctrl+Space
        ctrl_space = (event.modifiers() & Qt.ControlModifier) and event.key() == Qt.Key_Space
        if ctrl_space:
            self.show_completions(force=True)
        else:
            self.show_completions(force=False)

    def show_completions(self, force=False):
        prefix = self.text_under_cursor()
        if not prefix and not force:
            return
        if len(prefix) < 2 and not force:
            return

        self.completer.setCompletionPrefix(prefix)
        cr = self.cursorRect()
        cr.setWidth(
            self.completer.popup().sizeHintForColumn(0)
            + self.completer.popup().verticalScrollBar().sizeHint().width()
        )
        self.completer.complete(cr)

    def update_completions(self):
        """Merge buffer words + keyword packs into the completer model."""
        text = self.toPlainText()
        buffer_words = set(w for w in WORD_RE.findall(text) if len(w) > 2)
        pack_words = set(self.keyword_packs.all_keywords())
        all_words = sorted(buffer_words.union(pack_words))
        self.model.setStringList(all_words)

    # ---------- File I/O ----------

    def load_from_file(self, path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                self.setPlainText(f.read())
            self.file_path = path
        except Exception as e:
            QMessageBox.critical(self, "Open File", f"Could not open file:\n{e}")

    def save_to_file(self, path=None):
        if path is None:
            path = self.file_path
        if not path:
            return False
        try:
            with open(path, "w", encoding="utf-8", errors="ignore") as f:
                f.write(self.toPlainText())
            self.file_path = path
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save File", f"Could not save file:\n{e}")
            return False


# ============================================================
# Tab container
# ============================================================

class EditorTabs(QTabWidget):
    """Tabbed container for multiple CodeEditor instances."""

    def __init__(self, keyword_packs: KeywordPacks, parent=None):
        super().__init__(parent)
        self.keyword_packs = keyword_packs

        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)

    def new_tab(self, language="python", title="untitled"):
        editor = CodeEditor(self.keyword_packs, language=language)
        idx = self.addTab(editor, title)
        self.setCurrentIndex(idx)
        return editor

    def open_file(self, path, language="python"):
        editor = self.new_tab(language=language, title=os.path.basename(path))
        editor.load_from_file(path)
        return editor

    def current_editor(self):
        widget = self.currentWidget()
        if isinstance(widget, CodeEditor):
            return widget
        return None

    def close_tab(self, index):
        widget = self.widget(index)
        self.removeTab(index)
        widget.deleteLater()


# ============================================================
# Help content
# ============================================================

def help_text():
    return (
        "KeySnap Help\n"
        "============\n\n"
        "Core:\n"
        "- AMOLED-dark, curved UI\n"
        "- Multi-tab editor\n"
        "- Syntax highlighting (Python, JS, C, C++, HTML, CSS)\n"
        "- Popup autocomplete (Ctrl+Space)\n"
        "- Keyword packs from TXT / DOCX / CONFIG\n"
        "- Folder keyword scanning\n"
        "- Run Python/Tkinter (F5)\n\n"
        "Shortcuts:\n"
        "- Ctrl+N : New file\n"
        "- Ctrl+O : Open file\n"
        "- Ctrl+S : Save file\n"
        "- F5     : Run current Python file\n"
        "- Ctrl+Space : Show autocomplete popup\n\n"
        "Keywords Menu:\n"
        "- Load Keywords from File: extract keywords from txt/docx/config\n"
        "- Scan Folder: build keyword packs from many files\n\n"
        "DOCX Reading:\n"
        "- Use Keywords → Load Keywords from File\n"
        "- Select a .docx file\n"
        "- Extracted keywords are merged into autocomplete.\n"
    )


# ============================================================
# Main window
# ============================================================

class MainWindow(QMainWindow):
    """KeySnap main window."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("KeySnap")
        self.resize(1100, 700)

        self.keyword_packs = KeywordPacks()

        # Central layout
        self.tabs = EditorTabs(self.keyword_packs, self)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.tabs)
        self.setCentralWidget(container)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # Menus
        self.build_menus()

        # Start with one Python tab
        self.tabs.new_tab(language="python", title="untitled.py")

    # ---------- Menus ----------

    def build_menus(self):
        menubar = self.menuBar()

        # File
        file_menu = menubar.addMenu("File")

        new_act = QAction("New", self)
        new_act.setShortcut("Ctrl+N")
        new_act.triggered.connect(self.new_file)
        file_menu.addAction(new_act)

        open_act = QAction("Open...", self)
        open_act.setShortcut("Ctrl+O")
        open_act.triggered.connect(self.open_file)
        file_menu.addAction(open_act)

        save_act = QAction("Save", self)
        save_act.setShortcut("Ctrl+S")
        save_act.triggered.connect(self.save_file)
        file_menu.addAction(save_act)

        save_as_act = QAction("Save As...", self)
        save_as_act.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_act)

        file_menu.addSeparator()

        exit_act = QAction("Exit", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        # Run
        run_menu = menubar.addMenu("Run")

        run_py_act = QAction("Run Current Python File", self)
        run_py_act.setShortcut("F5")
        run_py_act.triggered.connect(self.run_current_python_file)
        run_menu.addAction(run_py_act)

        # Keywords
        kw_menu = menubar.addMenu("Keywords")

        load_kw_file_act = QAction("Load Keywords from File (txt/docx/config)", self)
        load_kw_file_act.triggered.connect(self.load_keywords_from_file)
        kw_menu.addAction(load_kw_file_act)

        scan_folder_act = QAction("Scan Folder for Keyword Packs", self)
        scan_folder_act.triggered.connect(self.scan_folder_for_keywords)
        kw_menu.addAction(scan_folder_act)

        # Language
        lang_menu = menubar.addMenu("Language")

        py_lang = QAction("Python", self)
        py_lang.triggered.connect(lambda: self.set_language("python"))
        js_lang = QAction("JavaScript", self)
        js_lang.triggered.connect(lambda: self.set_language("javascript"))
        c_lang = QAction("C", self)
        c_lang.triggered.connect(lambda: self.set_language("c"))
        cpp_lang = QAction("C++", self)
        cpp_lang.triggered.connect(lambda: self.set_language("cpp"))
        html_lang = QAction("HTML", self)
        html_lang.triggered.connect(lambda: self.set_language("html"))
        css_lang = QAction("CSS", self)
        css_lang.triggered.connect(lambda: self.set_language("css"))

        for act in (py_lang, js_lang, c_lang, cpp_lang, html_lang, css_lang):
            lang_menu.addAction(act)

        # Help
        help_menu = menubar.addMenu("Help")

        help_tab_act = QAction("Open Help Tab", self)
        help_tab_act.triggered.connect(self.open_help_tab)
        help_menu.addAction(help_tab_act)

        about_act = QAction("About KeySnap", self)
        about_act.triggered.connect(self.show_about)
        help_menu.addAction(about_act)

    # ---------- File actions ----------

    def new_file(self):
        self.tabs.new_tab(language="python", title="untitled.py")

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)")
        if not path:
            return
        lang = self.detect_language(path)
        self.tabs.open_file(path, language=lang)
        self.status.showMessage(f"Opened: {path}", 3000)

    def save_file(self):
        editor = self.tabs.current_editor()
        if not editor:
            return
        if not editor.file_path:
            self.save_file_as()
            return
        if editor.save_to_file(editor.file_path):
            self.status.showMessage(f"Saved: {editor.file_path}", 3000)

    def save_file_as(self):
        editor = self.tabs.current_editor()
        if not editor:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save File As", "", "All Files (*)")
        if not path:
            return
        if editor.save_to_file(path):
            idx = self.tabs.currentIndex()
            self.tabs.setTabText(idx, os.path.basename(path))
            self.status.showMessage(f"Saved: {path}", 3000)

    # ---------- Language ----------

    @staticmethod
    def detect_language(path):
        ext = os.path.splitext(path)[1].lower()
        if ext in (".py",):
            return "python"
        if ext in (".js",):
            return "javascript"
        if ext in (".c",):
            return "c"
        if ext in (".cpp", ".hpp", ".cc", ".hh"):
            return "cpp"
        if ext in (".html", ".htm",):
            return "html"
        if ext in (".css",):
            return "css"
        return "python"

    def set_language(self, language):
        editor = self.tabs.current_editor()
        if not editor:
            return
        editor.set_language(language)
        self.status.showMessage(f"Language set to: {language}", 2000)

    # ---------- Run Python/Tkinter ----------

    def run_current_python_file(self):
        editor = self.tabs.current_editor()
        if editor is None:
            return

        if editor.language != "python":
            QMessageBox.information(self, "Run Python", "Current tab is not set to Python.")
            return

        if not editor.file_path:
            QMessageBox.information(self, "Run Python", "Please save the file before running.")
            return

        python_exe = sys.executable
        path = editor.file_path

        try:
            subprocess.Popen([python_exe, path])
            self.status.showMessage(f"Running: {path}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Run Python", f"Could not run file:\n{e}")

    # ---------- Keyword actions ----------

    def load_keywords_from_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Keywords from File",
            "",
            "All Files (*);;Word Documents (*.docx);;Text Files (*.txt *.md *.rtf);;"
            "Config Files (*.json *.xml *.ini *.cfg *.conf *.env *.yaml *.yml *.toml)"
        )
        if not path:
            return

        kws = extract_keywords_from_any_file(path)
        if not kws:
            QMessageBox.information(self, "Keywords", "No keywords found in file.")
            return

        self.keyword_packs.add_pack(kws)
        self.status.showMessage(
            f"Loaded {len(kws)} keywords from {os.path.basename(path)}",
            4000,
        )

        editor = self.tabs.current_editor()
        if editor:
            editor.update_completions()

    def scan_folder_for_keywords(self):
        folder = QFileDialog.getExistingDirectory(self, "Scan Folder for Keyword Packs", "")
        if not folder:
            return

        total_files = 0
        total_keywords = 0

        for root, dirs, files in os.walk(folder):
            for name in files:
                path = os.path.join(root, name)
                kws = extract_keywords_from_any_file(path)
                if kws:
                    self.keyword_packs.add_pack(kws)
                    total_files += 1
                    total_keywords += len(kws)

        QMessageBox.information(
            self,
            "Scan Complete",
            f"Scanned folder:\n{folder}\n\n"
            f"Files with keywords: {total_files}\n"
            f"Total keywords loaded: {total_keywords}"
        )

        editor = self.tabs.current_editor()
        if editor:
            editor.update_completions()

    # ---------- Help ----------

    def open_help_tab(self):
        editor = self.tabs.new_tab(language="python", title="HELP")
        editor.setPlainText(help_text())
        editor.setReadOnly(True)

    def show_about(self):
        QMessageBox.information(
            self,
            "About KeySnap",
            "KeySnap\n\n"
            "AMOLED-dark, curved, developer-styled editor\n"
            "with DOCX/TXT/CONFIG keyword extraction,\n"
            "popup autocomplete, and Python/Tkinter run support."
        )


# ============================================================
# Global AMOLED-dark, curved UI
# ============================================================

def apply_dark_palette(app: QApplication):
    """
    AMOLED-black base, medium curves, slightly curved popup.
    VS Code-inspired vibe, but not a copy.
    """
    palette = QPalette()

    # Base colors
    palette.setColor(QPalette.Window, QColor(0, 0, 0))
    palette.setColor(QPalette.WindowText, QColor(224, 224, 224))
    palette.setColor(QPalette.Base, QColor(0, 0, 0))
    palette.setColor(QPalette.AlternateBase, QColor(18, 18, 18))
    palette.setColor(QPalette.ToolTipBase, QColor(0, 0, 0))
    palette.setColor(QPalette.ToolTipText, QColor(224, 224, 224))
    palette.setColor(QPalette.Text, QColor(224, 224, 224))
    palette.setColor(QPalette.Button, QColor(10, 10, 10))
    palette.setColor(QPalette.ButtonText, QColor(224, 224, 224))
    palette.setColor(QPalette.BrightText, QColor(255, 82, 82))

    # Highlights
    palette.setColor(QPalette.Highlight, QColor(40, 40, 40))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

    app.setPalette(palette)

    # Global stylesheet for curves + popup
    app.setStyleSheet("""
        QMainWindow, QMenuBar, QMenu, QStatusBar {
            background-color: #000000;
            color: #e0e0e0;
        }

        QMenuBar::item {
            padding: 4px 10px;
            background: transparent;
        }
        QMenuBar::item:selected {
            background-color: #262626;
            border-radius: 10px;
        }

        QMenu {
            border: 1px solid #262626;
            border-radius: 10px;
            padding: 4px;
        }
        QMenu::item {
            padding: 4px 18px;
            border-radius: 8px;
        }
        QMenu::item:selected {
            background-color: #333333;
        }

        QTabWidget::pane {
            border: 1px solid #262626;
            border-radius: 12px;
            margin: 6px;
            background: #050505;
        }

        QTabBar::tab {
            background: #101010;
            color: #b0bec5;
            padding: 6px 14px;
            margin: 2px;
            border-radius: 12px;
        }
        QTabBar::tab:selected {
            background: #262626;
            color: #ffffff;
        }
        QTabBar::tab:hover {
            background: #333333;
        }

        QPlainTextEdit {
            background-color: #050505;
            color: #e0e0e0;
            border: none;
            selection-background-color: #262626;
            border-radius: 12px;
        }

        QStatusBar {
            background-color: #000000;
        }

        /* Autocomplete popup (QCompleter uses QAbstractItemView) */
        QAbstractItemView {
            background-color: #050505;
            color: #e0e0e0;
            border: 1px solid #262626;
            border-radius: 6px;  /* slightly curved popup */
            padding: 2px;
        }
        QAbstractItemView::item {
            padding: 2px 8px;
        }
        QAbstractItemView::item:selected {
            background-color: #262626;
            color: #ffffff;
        }
    """)


# ============================================================
# Entry point
# ============================================================

def main():
    app = QApplication(sys.argv)
    apply_dark_palette(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
