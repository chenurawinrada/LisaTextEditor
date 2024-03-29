VERSION = "5.0"

import sys
import time
import urllib.request
import threading
import webbrowser
import json
import requests
from packaging import version
from PyQt5.QtCore import QRegExp
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QHBoxLayout, QGridLayout, QAction, QSplashScreen
from PyQt5.QtWidgets import QTextEdit, QProgressBar, QLabel, QShortcut, QFileDialog, QMessageBox, QToolBar, QPushButton
from PyQt5.QtGui import QKeySequence, QIcon, QColor, QTextCursor, QTextCharFormat, QSyntaxHighlighter, QFont, QPixmap
from PyQt5 import QtGui
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt

#################################Colors####################################

with open('settings\styles_json.txt', 'r') as style_types:
    style_s = style_types.read()
    style_types.close()
with open(f"settings\{style_s}", 'r') as styles_json:
    json_data = json.loads(styles_json.read())
    styles_json.close()

with open('settings\styles_text_json.txt', 'r') as style_text_types:
    style_text_s = style_text_types.read()
    style_text_types.close()
with open(f"settings\{style_text_s}", 'r') as styles_text_json:
    json_data2 = json.loads(styles_text_json.read())
    styles_text_json.close()

color1 = json_data["color1"]
color2 = json_data["color2"]
color3 = json_data["color3"]
color4 = json_data["color4"]
color5 = json_data["color5"]
color6 = json_data["color6"]
color7 = json_data2["color7"]
color8 = json_data2["color8"]
color9 = json_data2["color9"]
color10 = json_data2["color10"]
color11 = json_data2["color11"]
color12 = json_data2["color12"]
color13 = json_data2["color13"]
color14 = json_data2["color14"]

# Png files will be changed automatically when the themes are activated
png1 = json_data["png1"]
png2 = json_data["png2"]
png3 = json_data["png3"]
png4 = json_data["png4"]
png5 = json_data["png5"]
png6 = json_data["png6"]
png7 = json_data["png7"]
png8 = json_data["png8"]
png9 = json_data["png9"]

###########################################################################

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
    'keyword': format(color7, 'bold'),
    'operator': format(color8),
    'brace': format('darkGray'),
    'defclass': format(color9, 'bold'),
    'string': format(color10),
    'string2': format(color11),
    'comment': format(color12),
    'self': format(color13, 'italic'),
    'numbers': format(color14),
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
        self.s_w = None
        self.file_path = None
        self.setWindowTitle("Lisa Editor Version 5.0")
        self.setWindowIcon(QtGui.QIcon('pics/iconlisa.png'))
        self.setStyleSheet(f"""
                            background: {color1};
                            color: {color2};
                            font-family: Georgia;
                            """)

        self.open_new_file_shortcut = QShortcut(QKeySequence('Ctrl+o'), self)
        self.open_new_file_shortcut.activated.connect(self.open_new_files)
        
        self.save_current_file_shortcut = QShortcut(QKeySequence('Ctrl+s'), self)
        self.save_current_file_shortcut.activated.connect(self.save_current_file)

        vbox = QVBoxLayout()
        text = "Untitled File"
        self.title = QLabel(text)
        self.title.setStyleSheet(f"""
                                border: 5px solid {color3};
                                background: {color4};
                                color: {color5};
                                font-size: 20px
                                """)
        self.title.setWordWrap(True)
        self.title.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self.title)
        self.setLayout(vbox)
        # Text Field
        self.scrollable_text_area = QTextEdit()
        self.scrollable_text_area.setStyleSheet(f"color: {color6}; font-size: 20px; font-family: Lucida Bright;")
        

        # Toolbar
        toolbar = QToolBar()
        
        openBtn = QAction(QIcon(png1), 'open', self)
        openBtn.triggered.connect(self.open_new_files)
        toolbar.addAction(openBtn)
        
        saveBtn = QAction(QIcon(png2), 'save', self)
        saveBtn.triggered.connect(self.save_current_file)
        toolbar.addAction(saveBtn)
        
        undoBtn = QAction(QIcon(png3), 'undo', self)
        undoBtn.triggered.connect(self.scrollable_text_area.undo)
        toolbar.addAction(undoBtn)

        redoBtn = QAction(QIcon(png4), 'redo', self)
        redoBtn.triggered.connect(self.scrollable_text_area.redo)
        toolbar.addAction(redoBtn)

        copyBtn = QAction(QIcon(png5), 'copy', self)
        copyBtn.triggered.connect(self.scrollable_text_area.copy)
        toolbar.addAction(copyBtn)

        cutBtn = QAction(QIcon(png6), 'cut', self)
        cutBtn.triggered.connect(self.scrollable_text_area.cut)
        toolbar.addAction(cutBtn)

        pasteBtn = QAction(QIcon(png7), 'paste', self)
        pasteBtn.triggered.connect(self.scrollable_text_area.paste)
        toolbar.addAction(pasteBtn)

        updateBtn = QAction(QIcon(png8), 'update', self)
        updateBtn.triggered.connect(self.update)
        toolbar.addAction(updateBtn)

        settings_button = QAction(QIcon(png9), 'settings', self)
        settings_button.triggered.connect(self.settings_window_opened)
        toolbar.addAction(settings_button)

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

    def settings_window_opened(self, checked):
        if self.s_w == None:
            self.s_w = SettingsWindow()
        self.s_w.show()
        

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Settings')
        self.setStyleSheet("""
            QWidget{
                background: black;
                font-weight: bold;
                font-family: Georgia;
                border-radius: 20px;
                color: white;
            }
            QPushButton{
                color: white;
                border-radius: 20px;
                font-size: 20px;
                background-color: black;
            }
            QPushButton::hover{
                color: black;
                background-color: white;
            }
            QLabel{
                color: lightblue;
                background-color: black;
                font-size: 20px;
            }
            """)
        self.setFixedSize(500, 400)
        grid = QGridLayout()

        # Theme buttons
        s_button1 = QPushButton('Dark')
        s_button1.clicked.connect(self.setThemeDark)
        s_button2 = QPushButton('Light')
        s_button2.clicked.connect(self.setThemeLight)

        # Style buttons
        s_button_style1 = QPushButton('Green')
        s_button_style1.clicked.connect(self.setStyleGreen)
        s_button_style2 = QPushButton('Perple')
        s_button_style2.clicked.connect(self.setStylePerple)
        s_button_style3 = QPushButton('Red')
        s_button_style3.clicked.connect(self.setStyleRed)
        theme = QLabel('Set Theme To:')
        style = QLabel('Set Style To:')
        grid.addWidget(theme, 1, 0)
        grid.addWidget(style, 1, 1)

        self.textmsg = "You may have to restart the application to see\nthe changes!"
        self.msgLabel = QLabel(self.textmsg)

        grid.addWidget(s_button1, 2, 0)
        grid.addWidget(s_button2, 3, 0)

        grid.addWidget(s_button_style1, 2, 1)
        grid.addWidget(s_button_style2, 3, 1)
        grid.addWidget(s_button_style3, 4, 1)

        grid.addWidget(self.msgLabel, 5, 0, 5, 2)

        self.setLayout(grid)

    def setThemeDark(self):
        with open('settings\styles_json.txt', 'w') as Themes:
            Themes.write("dark.json")
            Themes.close()
            self.msgLabel.setText("Dark theme activated!\n\n" + self.textmsg)

    def setThemeLight(self):
        with open('settings\styles_json.txt', 'w') as Themes:
            Themes.write("light.json")
            Themes.close()
            self.msgLabel.setText("Light theme activated!\n\n" + self.textmsg)

    def setStyleGreen(self):
        with open('settings\styles_text_json.txt', 'w') as Style_Text:
            Style_Text.write("green.json")
            Style_Text.close()
            self.msgLabel.setText("Green style activated!\n\n" + self.textmsg)

    def setStylePerple(self):
        with open('settings\styles_text_json.txt', 'w') as Style_Text:
            Style_Text.write("perple.json")
            Style_Text.close()
            self.msgLabel.setText("Perple style activated!\n\n" + self.textmsg)

    def setStyleRed(self):
        with open('settings\styles_text_json.txt', 'w') as Style_Text:
            Style_Text.write("red.json")
            Style_Text.close()
            self.msgLabel.setText("Red style activated!\n\n" + self.textmsg)

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