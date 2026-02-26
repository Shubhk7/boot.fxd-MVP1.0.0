import sys
import json
import subprocess

from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow,
    QPushButton, QLabel, QTextEdit,
    QVBoxLayout, QHBoxLayout, QFrame,
    QProgressBar, QCheckBox
)

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


BACKEND = "./boot.fxd"


DARK_THEME = """
QMainWindow {
    background-color: #0b0f17;
}

QFrame {
    background-color: #111827;
    border-radius: 10px;
}

QLabel {
    color: white;
}

QPushButton {
    background-color: #2563eb;
    color: white;
    border-radius: 6px;
    padding: 8px;
}

QPushButton:hover {
    background-color: #1d4ed8;
}

QTextEdit {
    background-color: #020617;
    color: #00ffcc;
    border-radius: 6px;
}

QProgressBar {
    border-radius: 6px;
    text-align: center;
}
"""


LIGHT_THEME = """
QMainWindow {
    background-color: #f3f4f6;
}

QFrame {
    background-color: white;
    border-radius: 10px;
}

QLabel {
    color: black;
}

QPushButton {
    background-color: #2563eb;
    color: white;
}

QTextEdit {
    background-color: white;
    color: black;
}
"""


class BootFXD(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Boot.fxd Security Dashboard")
        self.setGeometry(100, 100, 900, 600)

        self.setStyleSheet(DARK_THEME)

        self.build_ui()


    def build_ui(self):

        main = QHBoxLayout()

        sidebar = self.sidebar()
        dashboard = self.dashboard()

        main.addWidget(sidebar)
        main.addWidget(dashboard)

        container = QWidget()
        container.setLayout(main)

        self.setCentralWidget(container)


    def sidebar(self):

        frame = QFrame()
        frame.setFixedWidth(200)

        layout = QVBoxLayout()

        title = QLabel("Boot.fxd")
        title.setFont(QFont("Arial", 18))
        layout.addWidget(title)

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

        self.status = QLabel("System Status: UNKNOWN")
        self.status.setFont(QFont("Arial", 22))

        self.progress = QProgressBar()
        self.progress.setValue(0)

        self.output = QTextEdit()

        layout.addWidget(self.status)
        layout.addWidget(self.progress)
        layout.addWidget(self.output)

        frame.setLayout(layout)

        return frame


    def run_backend(self, arg):

        try:

            result = subprocess.run(
                ["sudo", BACKEND, arg],
                capture_output=True,
                text=True
            )

            return json.loads(result.stdout)

        except Exception as e:
            return {"status": "error", "message": str(e)}


    def init_baseline(self):

        self.output.setText("Initializing baseline...")
        self.progress.setValue(30)

        data = self.run_backend("--init")

        self.progress.setValue(100)

        if data["status"] == "baseline_created":
            self.status.setText("Status: BASELINE CREATED")
        else:
            self.status.setText("Status: ERROR")

        self.output.setText(str(data))


    def scan(self):

        self.progress.setValue(10)

        self.output.setText("Scanning system...")

        QTimer.singleShot(500, lambda: self.progress.setValue(40))
        QTimer.singleShot(1000, lambda: self.progress.setValue(70))

        data = self.run_backend("--scan")

        self.progress.setValue(100)

        if data["status"] == "clean":

            self.status.setText("Status: SYSTEM SAFE")
            self.status.setStyleSheet("color: #00ff00")

            self.output.setText("No threats detected.")

        elif data["status"] == "tampered":

            self.status.setText("Status: SYSTEM COMPROMISED")
            self.status.setStyleSheet("color: red")

            text = json.dumps(data, indent=4)

            self.output.setText(text)

        else:

            self.status.setText("Status: ERROR")

            self.output.setText(str(data))


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