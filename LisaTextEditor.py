VERSION = "4.0"

import sys
import time
import urllib.request
import threading
import webbrowser
import json
import requests
from packaging import version
from PyQt5.QtCore import QRegExp
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QHBoxLayout, QAction, QSplashScreen
from PyQt5.QtWidgets import QTextEdit, QProgressBar, QLabel, QShortcut, QFileDialog, QMessageBox, QToolBar
from PyQt5.QtGui import QKeySequence, QIcon, QColor, QTextCursor, QTextCharFormat, QSyntaxHighlighter, QFont, QPixmap
from PyQt5 import QtGui
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt

def format(color, style=''):
    """
    Return a QTextCharFormat with the given attributes.
    """
    _color = QColor()
    if type(color) is not str:
        _color.setRgb(color[0], color[1], color[2])
    else:
        _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format

# 150, 85, 140
# 147, 112, 219
# 'defclass': format([220, 220, 255], 'bold'),
# Syntax styles that can be shared by all languages

STYLES = {
    'keyword': format([0, 255, 0], 'bold'),
    'operator': format([150, 150, 150]),
    'brace': format('darkGray'),
    'defclass': format([255, 255, 204], 'bold'),
    'string': format([51, 255, 255]),
    'string2': format([30, 120, 110]),
    'comment': format([128, 128, 128]),
    'self': format([255, 0, 255], 'italic'),
    'numbers': format([0, 204, 102]),
}


class PythonHighlighter(QSyntaxHighlighter):

    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'cout', 'cin', 'println', 'printf',
        'None', 'True', 'False', 'range', 'html', 'div',
        'center', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
    ]

    # Python operators
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        '\+', '-', '\*', '/', '//', '\%', '\*\*',
        # In-place
        '\+=', '-=', '\*=', '/=', '\%=',
        # Bitwise
        '\^', '\|', '\&', '\~', '>>', '<<',
    ]

    # Python braces
    braces = [
        '\{', '\}', '\(', '\)', '\[', '\]',
    ]

    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)

        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
        self.tri_single = (QRegExp("'''"), 1, STYLES['string2'])
        self.tri_double = (QRegExp('"""'), 2, STYLES['string2'])

        rules = []

        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, STYLES['keyword'])
                  for w in PythonHighlighter.keywords]
        rules += [(r'%s' % o, 0, STYLES['operator'])
                  for o in PythonHighlighter.operators]
        rules += [(r'%s' % b, 0, STYLES['brace'])
                  for b in PythonHighlighter.braces]

        # All other rules
        rules += [
            # 'self'
            (r'\bself\b', 0, STYLES['self']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

            # 'def' followed by an identifier
            (r'\bdef\b\s*(\w+)', 1, STYLES['defclass']),
            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, STYLES['defclass']),

            # From '#' until a newline
            (r'#[^\n]*', 0, STYLES['comment']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, STYLES['numbers']),
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt)
                      for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        # Do other syntax formatting
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)

    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QRegExp`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False
# Main Window

class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.file_path = None
        self.setWindowTitle("Lisa Editor Version 4.0")
        self.setWindowIcon(QtGui.QIcon('pics/iconlisa.png'))
        self.setStyleSheet("""
                            background: black;
                            color: blue;
                            font-family: Georgia;
                            """)

        self.open_new_file_shortcut = QShortcut(QKeySequence('Ctrl+o'), self)
        self.open_new_file_shortcut.activated.connect(self.open_new_files)
        
        self.save_current_file_shortcut = QShortcut(QKeySequence('Ctrl+s'), self)
        self.save_current_file_shortcut.activated.connect(self.save_current_file)

        vbox = QVBoxLayout()
        text = "Untitled File"
        self.title = QLabel(text)
        self.title.setStyleSheet("""
                                border: 5px solid black;
                                background: gray;
                                color: black;
                                font-size: 20px
                                """)
        self.title.setWordWrap(True)
        self.title.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self.title)
        self.setLayout(vbox)
        # Text Field
        self.scrollable_text_area = QTextEdit()
        self.scrollable_text_area.setStyleSheet("color: white; font-size: 20px; font-family: Lucida Bright;")
        

        # Toolbar
        toolbar = QToolBar()
        
        openBtn = QAction(QIcon('pics/open.png'), 'open', self)
        openBtn.triggered.connect(self.open_new_files)
        toolbar.addAction(openBtn)
        
        saveBtn = QAction(QIcon('pics/save.png'), 'save', self)
        saveBtn.triggered.connect(self.save_current_file)
        toolbar.addAction(saveBtn)
        
        undoBtn = QAction(QIcon('pics/undo.png'), 'undo', self)
        undoBtn.triggered.connect(self.scrollable_text_area.undo)
        toolbar.addAction(undoBtn)

        redoBtn = QAction(QIcon('pics/redo.png'), 'redo', self)
        redoBtn.triggered.connect(self.scrollable_text_area.redo)
        toolbar.addAction(redoBtn)

        copyBtn = QAction(QIcon('pics/copy.png'), 'copy', self)
        copyBtn.triggered.connect(self.scrollable_text_area.copy)
        toolbar.addAction(copyBtn)

        cutBtn = QAction(QIcon('pics/cut.png'), 'cut', self)
        cutBtn.triggered.connect(self.scrollable_text_area.cut)
        toolbar.addAction(cutBtn)

        pasteBtn = QAction(QIcon('pics/paste.png'), 'paste', self)
        pasteBtn.triggered.connect(self.scrollable_text_area.paste)
        toolbar.addAction(pasteBtn)

        updateBtn = QAction(QIcon('pics/update.png'), 'update', self)
        updateBtn.triggered.connect(self.update)
        toolbar.addAction(updateBtn)
        
        vbox.addWidget(toolbar)
        self.highlight = PythonHighlighter(self.scrollable_text_area.document())
        vbox.addWidget(self.scrollable_text_area)

    def open_new_files(self):
        self.file_path, filter_type = QFileDialog.getOpenFileName(self, "Open new file", "", "All files (*)")
        if self.file_path:
            with open(self.file_path, "r") as f:
                file_contents = f.read()
                self.title.setText(self.file_path)
                self.scrollable_text_area.setText(file_contents)

        else:
            self.invalied_path_alert_message()

    def save_current_file(self):
        if not self.file_path:
            new_file_path, filter_type = QFileDialog.getSaveFileName(self, "Save this file as....", "", "All files (*)")
            if new_file_path:
                self.file_path = new_file_path
            else:
                self.invalied_path_alert_message()
                return False
        file_contents = self.scrollable_text_area.toPlainText()
        with open(self.file_path, "w") as f:
            f.write(file_contents)
        self.title.setText(self.file_path)

    def closeEvent(self, event):
        messgeBox = QMessageBox()
        title = "Quit Application?"
        message = "WARNING !!\n\nIf you quit without saving, any changes made to the file will be lost.\n\nSave file before quiting?"

        reply = messgeBox.question(self, title, message, messgeBox.Yes | messgeBox.No | messgeBox.Cancel, messgeBox.Cancel)
        if reply == messgeBox.Yes:
            return_value = self.save_current_file()
            if return_value == False:
                event.ignore()
        elif reply == messgeBox.No:
            event.accept()
        else:
            event.ignore()

    def invalied_path_alert_message(self):
        messageBox = QMessageBox()
        messageBox.setWindowTitle("Invalied file")
        messageBox.setText("Selected filename or path is not valid. Please select a valid file.")
        messageBox.exec()

    def check_connection(self, timeout=1):
        try:
            urllib.request.urlopen('https://www.google.com', timeout=1)
            return True
        except Exception as e:
            print(e)
            return False

    def update_(self):
        url = 'https://github.com/chenurawinrada/LisaTextEditor'
        webbrowser.open(url)

# Cheack for updates
    def update(self):
        if self.check_connection(timeout=1):
            url = 'https://raw.githubusercontent.com/chenurawinrada/LisaTextEditor/master/update_utils/metadata.json'
            rqt = requests.get(url, timeout=5)
            meta_sc = rqt.status_code
            if meta_sc == 200:
                metadata = rqt.text
                json_data = json.loads(metadata)
                gh_version = json_data['version']
                if version.parse(gh_version) > version.parse(VERSION):
                    mgb = QMessageBox()
                    title = "Update available!"
                    message = "Do you want to go to the website now?"
                    reply = mgb.question(self, title, message, mgb.Yes | mgb.No)
                    if reply == mgb.Yes:
                        threading.Thread(target=self.update_).start()
                    elif reply == mgb.No:
                        mgb.close()
                else:
                    messageBox = QMessageBox()
                    messageBox.setWindowTitle("Info.")
                    messageBox.setText("No updates available.")
                    messageBox.exec()
        else:
            messageBox = QMessageBox()
            messageBox.setWindowTitle("No network connection!")
            messageBox.setText("You need an active connection to do that!")
            messageBox.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    splash_pix = QPixmap('pics/iconlisa.png')
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    progressbar = QProgressBar(splash)
    progressbar.setAlignment(Qt.AlignCenter)
    progressbar.setStyleSheet("""
    QProgressBar{
        color: black;
        font-weight: bold;
        font-family: Georgia;
        border-radius: 20px;
        background-color: white;
    }
    QProgressBar::chunk{
        border-radius: 20px;
        background-color: rgb(65, 214, 189);
    }
    """)
    progressbar.setGeometry(0, splash_pix.height() - 20, splash_pix.width(), 20)
    splash.setMask(splash_pix.mask())
    splash.show()
    for i in range(0, 101):
        progressbar.setValue(i)
        t = time.time()
        while time.time() < t + 0.1:
            app.processEvents()
    time.sleep(1)
    splash.close()
    w = Window()
    w.showMaximized()
    sys.exit(app.exec_())
