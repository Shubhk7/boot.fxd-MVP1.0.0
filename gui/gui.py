import sys
import json
import subprocess

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QCheckBox, QFrame
)

from PyQt6.QtCore import Qt, QPropertyAnimation
from PyQt6.QtGui import QFont


BOOTFXD_PATH = "./boot.fxd"


DARK_THEME = """
QWidget {
    background-color: #121212;
    color: #e0e0e0;
    font-family: Segoe UI;
}

QPushButton {
    background-color: #1f1f1f;
    border: 1px solid #333;
    padding: 10px;
    border-radius: 6px;
}

QPushButton:hover {
    background-color: #2a2a2a;
}

QTextEdit {
    background-color: #1a1a1a;
    border: 1px solid #333;
    border-radius: 6px;
}

QCheckBox {
    padding: 5px;
}
"""


LIGHT_THEME = """
QWidget {
    background-color: #f5f5f5;
    color: #111;
    font-family: Segoe UI;
}

QPushButton {
    background-color: #ffffff;
    border: 1px solid #ccc;
    padding: 10px;
    border-radius: 6px;
}

QPushButton:hover {
    background-color: #eaeaea;
}

QTextEdit {
    background-color: #ffffff;
    border: 1px solid #ccc;
    border-radius: 6px;
}
"""


class BootIntegrityGUI(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Boot Integrity Monitor")
        self.resize(750, 520)

        self.setStyleSheet(DARK_THEME)

        layout = QVBoxLayout()

        # Header
        header = QLabel("BOOT INTEGRITY MONITOR")
        header.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(header)

        # Status box
        self.status_box = QLabel("STATUS: UNKNOWN")
        self.status_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_box.setFont(QFont("Segoe UI", 16))

        self.status_box.setFrameShape(QFrame.Shape.Box)
        self.status_box.setStyleSheet("""
            border: 2px solid #444;
            padding: 10px;
        """)

        layout.addWidget(self.status_box)

        # Buttons
        button_layout = QHBoxLayout()

        self.init_btn = QPushButton("Initialize Baseline")
        self.scan_btn = QPushButton("Scan System")

        self.init_btn.clicked.connect(self.init_baseline)
        self.scan_btn.clicked.connect(self.scan_system)

        button_layout.addWidget(self.init_btn)
        button_layout.addWidget(self.scan_btn)

        layout.addLayout(button_layout)

        # Theme toggle
        self.theme_toggle = QCheckBox("Light Theme")
        self.theme_toggle.stateChanged.connect(self.toggle_theme)

        layout.addWidget(self.theme_toggle)

        # Output
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        layout.addWidget(self.output)

        self.setLayout(layout)


    def toggle_theme(self):

        if self.theme_toggle.isChecked():
            self.setStyleSheet(LIGHT_THEME)
        else:
            self.setStyleSheet(DARK_THEME)


    def run_backend(self, arg):

        try:

            result = subprocess.run(
                ["sudo", BOOTFXD_PATH, arg],
                capture_output=True,
                text=True
            )

            return json.loads(result.stdout)

        except Exception as e:

            return {"status": "error", "message": str(e)}


    def animate_status(self, color):

        self.anim = QPropertyAnimation(self.status_box, b"windowOpacity")
        self.anim.setDuration(300)
        self.anim.setStartValue(0.5)
        self.anim.setEndValue(1)
        self.anim.start()

        self.status_box.setStyleSheet(f"""
            border: 2px solid {color};
            padding: 10px;
        """)


    def init_baseline(self):

        self.output.setText("Initializing baseline...")

        data = self.run_backend("--init")

        if data["status"] == "baseline_created":

            self.status_box.setText("BASELINE CREATED")
            self.animate_status("#4caf50")

            self.output.setText("Baseline initialized successfully.")

        else:

            self.status_box.setText("ERROR")
            self.animate_status("#f44336")

            self.output.setText(str(data))


    def scan_system(self):

        self.output.setText("Scanning system...")

        data = self.run_backend("--scan")

        if data["status"] == "clean":

            self.status_box.setText("SYSTEM SAFE")
            self.animate_status("#4caf50")

            self.output.setText("No tampering detected.")

        elif data["status"] == "tampered":

            self.status_box.setText("SYSTEM COMPROMISED")
            self.animate_status("#f44336")

            text = ""

            if data["modified"]:
                text += "Modified:\n" + "\n".join(data["modified"]) + "\n\n"

            if data["added"]:
                text += "Added:\n" + "\n".join(data["added"]) + "\n\n"

            if data["removed"]:
                text += "Removed:\n" + "\n".join(data["removed"]) + "\n\n"

            self.output.setText(text)

        else:

            self.status_box.setText("ERROR")
            self.animate_status("#f44336")

            self.output.setText(str(data))


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = BootIntegrityGUI()

    window.show()

    sys.exit(app.exec())