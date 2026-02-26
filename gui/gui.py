import sys
import json
import subprocess
import platform

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QLabel, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QFrame,
    QProgressBar, QCheckBox, QGridLayout
)

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont


BACKEND = "./boot.fxd"


# Worker thread for scan
class ScanThread(QThread):
    finished = pyqtSignal(dict)

    def run(self):
        result = subprocess.run(
            ["sudo", BACKEND, "--scan"],
            capture_output=True,
            text=True
        )

        try:
            data = json.loads(result.stdout)
        except:
            data = {"status": "error"}

        self.finished.emit(data)


# Worker thread for init
class InitThread(QThread):
    finished = pyqtSignal(dict)

    def run(self):
        result = subprocess.run(
            ["sudo", BACKEND, "--init"],
            capture_output=True,
            text=True
        )

        try:
            data = json.loads(result.stdout)
        except:
            data = {"status": "error"}

        self.finished.emit(data)


DARK_THEME = """
QMainWindow {
    background-color: #0a0f1c;
}
QFrame {
    background-color: #111827;
    border-radius: 12px;
}
QLabel {
    color: #e5e7eb;
}
QPushButton {
    background-color: #2563eb;
    color: white;
    padding: 10px;
    border-radius: 8px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QTextEdit {
    background-color: #020617;
    color: #00ffcc;
    border-radius: 8px;
}
QProgressBar {
    border-radius: 8px;
    height: 18px;
}
"""


LIGHT_THEME = """
QMainWindow {
    background-color: #f3f4f6;
}
QFrame {
    background-color: white;
}
QLabel {
    color: black;
}
QTextEdit {
    background-color: white;
    color: black;
}
"""


class BootFXD(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Boot.fxd Security Center")
        self.resize(1000, 650)

        self.setStyleSheet(DARK_THEME)

        self.build_ui()


    def build_ui(self):

        root = QHBoxLayout()

        root.addWidget(self.sidebar())
        root.addWidget(self.dashboard())

        container = QWidget()
        container.setLayout(root)

        self.setCentralWidget(container)


    def sidebar(self):

        frame = QFrame()
        frame.setFixedWidth(220)

        layout = QVBoxLayout()

        logo = QLabel("Boot.fxd")
        logo.setFont(QFont("Arial", 22))
        layout.addWidget(logo)

        init_btn = QPushButton("Initialize Baseline")
        init_btn.clicked.connect(self.init_baseline)

        scan_btn = QPushButton("Scan System")
        scan_btn.clicked.connect(self.scan)

        theme = QCheckBox("Light Mode")
        theme.stateChanged.connect(self.toggle_theme)

        layout.addWidget(init_btn)
        layout.addWidget(scan_btn)
        layout.addWidget(theme)
        layout.addStretch()

        frame.setLayout(layout)

        return frame


    def dashboard(self):

        frame = QFrame()
        layout = QVBoxLayout()

        header = QLabel("Security Dashboard")
        header.setFont(QFont("Arial", 20))

        layout.addWidget(header)
        layout.addWidget(self.cards())

        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        self.log = QTextEdit()
        layout.addWidget(self.log)

        frame.setLayout(layout)

        return frame


    def cards(self):

        grid = QGridLayout()

        self.status_card = self.make_card("Status", "UNKNOWN")
        self.threat_card = self.make_card("Threat Level", "NONE")

        self.system_card = self.make_card(
            "System",
            f"{platform.system()} {platform.release()}"
        )

        grid.addWidget(self.status_card, 0, 0)
        grid.addWidget(self.threat_card, 0, 1)
        grid.addWidget(self.system_card, 0, 2)

        container = QFrame()
        container.setLayout(grid)

        return container


    def make_card(self, title, value):

        frame = QFrame()
        layout = QVBoxLayout()

        t = QLabel(title)
        t.setFont(QFont("Arial", 12))

        v = QLabel(value)
        v.setFont(QFont("Arial", 18))

        layout.addWidget(t)
        layout.addWidget(v)

        frame.setLayout(layout)
        frame.value_label = v

        return frame


    # Initialize baseline
    def init_baseline(self):

        self.log.setText("Initializing baseline...")
        self.progress.setValue(0)

        self.init_thread = InitThread()
        self.init_thread.finished.connect(self.init_complete)
        self.init_thread.start()

        self.animate_progress()


    def init_complete(self, data):

        self.progress.setValue(100)

        if data["status"] == "baseline_created":
            self.status_card.value_label.setText("BASELINE CREATED")
            self.log.setText("Baseline created successfully.")
        else:
            self.log.setText("Error creating baseline.")


    # Scan system
    def scan(self):

        self.log.setText("Scanning system...")
        self.progress.setValue(0)

        self.scan_thread = ScanThread()
        self.scan_thread.finished.connect(self.scan_complete)
        self.scan_thread.start()

        self.animate_progress()


    def scan_complete(self, data):

        self.progress.setValue(100)

        if data["status"] == "clean":

            self.status_card.value_label.setText("SAFE")
            self.status_card.value_label.setStyleSheet("color: #22c55e")

            self.threat_card.value_label.setText("NONE")

            self.log.setText("No threats detected.")

        else:

            self.status_card.value_label.setText("COMPROMISED")
            self.status_card.value_label.setStyleSheet("color: red")

            self.threat_card.value_label.setText("HIGH")

            self.log.setText(json.dumps(data, indent=4))


    # Progress animation
    def animate_progress(self):

        self.progress_timer = QTimer()

        def update():
            val = self.progress.value()
            if val < 90:
                self.progress.setValue(val + 2)
            else:
                self.progress_timer.stop()

        self.progress_timer.timeout.connect(update)
        self.progress_timer.start(50)


    def toggle_theme(self, state):

        if state:
            self.setStyleSheet(LIGHT_THEME)
        else:
            self.setStyleSheet(DARK_THEME)


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = BootFXD()

    window.show()

    sys.exit(app.exec())