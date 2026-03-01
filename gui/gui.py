import sys
import json
import subprocess
import platform
import os

from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QLabel, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QFrame,
    QProgressBar, QCheckBox, QGridLayout,
    QDialog
)

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont


BACKEND = "./boot.fxd"

BASELINE_FILE = "output/baseline.json"
HISTORY_FILE = "output/history.json"


# ============================================
# SYSTEM DETECTION
# ============================================

def get_boot_mode():
    return "UEFI" if os.path.exists("/sys/firmware/efi") else "BIOS"


def get_secure_boot():

    try:

        result = subprocess.run(
            ["mokutil", "--sb-state"],
            capture_output=True,
            text=True
        )

        if "enabled" in result.stdout.lower():
            return "Enabled"

        elif "disabled" in result.stdout.lower():
            return "Disabled"

        else:
            return "Unknown"

    except:
        return "Not Available"


def get_tpm():

    if os.path.exists("/dev/tpm0") or os.path.exists("/dev/tpmrm0"):
        return "Present"

    if os.path.exists("/sys/class/tpm"):
        return "Present"

    return "Not Present"


def get_os():
    return platform.system()


def get_kernel():
    return platform.release()


# ============================================
# WORKER THREADS
# ============================================

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


# ============================================
# THEMES
# ============================================

DARK_THEME = """
QMainWindow { background-color: #0a0f1c; }
QFrame { background-color: #111827; border-radius: 12px; }
QLabel { color: #e5e7eb; }
QPushButton {
    background-color: #2563eb;
    color: white;
    padding: 10px;
    border-radius: 8px;
}
QPushButton:hover { background-color: #1d4ed8; }
QTextEdit {
    background-color: #020617;
    color: #00ffcc;
}
"""


LIGHT_THEME = """
QMainWindow { background-color: #f3f4f6; }
QFrame { background-color: white; }
QLabel { color: black; }
QTextEdit { background-color: white; color: black; }
"""


# ============================================
# MAIN WINDOW
# ============================================

class BootFXD(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Boot.fxd Security Center")
        self.resize(1100, 700)

        self.setStyleSheet(DARK_THEME)

        self.detect_system()

        self.build_ui()


    # ============================================
    # SYSTEM DETECTION
    # ============================================

    def detect_system(self):

        self.boot_mode = get_boot_mode()
        self.secure_boot = get_secure_boot()
        self.tpm = get_tpm()
        self.os = get_os()
        self.kernel = get_kernel()


    # ============================================
    # SAVE HISTORY
    # ============================================

    def save_scan_history(self, status):

        record = {

            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

            "status": status,

            "secure_boot": self.secure_boot,

            "tpm": self.tpm
        }

        try:

            if os.path.exists(HISTORY_FILE):

                with open(HISTORY_FILE, "r") as f:
                    data = json.load(f)

            else:

                data = []

            data.append(record)

            with open(HISTORY_FILE, "w") as f:
                json.dump(data, f, indent=4)

        except:
            pass


    # ============================================
    # UI BUILD
    # ============================================

    def build_ui(self):

        root = QHBoxLayout()

        root.addWidget(self.sidebar())
        root.addWidget(self.dashboard())

        container = QWidget()
        container.setLayout(root)

        self.setCentralWidget(container)


    # ============================================
    # SIDEBAR
    # ============================================

    def sidebar(self):

        frame = QFrame()
        frame.setFixedWidth(260)

        layout = QVBoxLayout()

        logo = QLabel("BOOT.FXD")
        logo.setFont(QFont("Arial", 24))

        layout.addWidget(logo)

        layout.addWidget(QLabel(f"OS: {self.os}"))
        layout.addWidget(QLabel(f"Kernel: {self.kernel}"))
        layout.addWidget(QLabel(f"Boot Mode: {self.boot_mode}"))
        layout.addWidget(QLabel(f"Secure Boot: {self.secure_boot}"))
        layout.addWidget(QLabel(f"TPM: {self.tpm}"))

        layout.addSpacing(20)

        init_btn = QPushButton("Initialize Baseline")
        init_btn.clicked.connect(self.init_baseline)

        scan_btn = QPushButton("Scan System")
        scan_btn.clicked.connect(self.scan)

        history_btn = QPushButton("View Scan History")
        history_btn.clicked.connect(self.show_history)

        theme = QCheckBox("Light Mode")
        theme.stateChanged.connect(self.toggle_theme)

        layout.addWidget(init_btn)
        layout.addWidget(scan_btn)
        layout.addWidget(history_btn)
        layout.addWidget(theme)

        layout.addStretch()

        frame.setLayout(layout)

        return frame


    # ============================================
    # DASHBOARD
    # ============================================

    def dashboard(self):

        frame = QFrame()

        layout = QVBoxLayout()

        header = QLabel("System Integrity Dashboard")
        header.setFont(QFont("Arial", 22))

        layout.addWidget(header)

        layout.addWidget(self.cards())

        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        self.log = QTextEdit()
        layout.addWidget(self.log)

        frame.setLayout(layout)

        return frame


    # ============================================
    # CARDS
    # ============================================

    def cards(self):

        grid = QGridLayout()

        self.integrity_card = self.make_card(
            "Boot Integrity",
            "Not Verified"
        )

        self.secureboot_card = self.make_card(
            "Secure Boot",
            self.secure_boot
        )

        self.tpm_card = self.make_card(
            "TPM Status",
            self.tpm
        )

        self.system_card = self.make_card(
            "System",
            f"{self.os} {self.kernel}"
        )

        grid.addWidget(self.integrity_card, 0, 0)
        grid.addWidget(self.secureboot_card, 0, 1)
        grid.addWidget(self.tpm_card, 1, 0)
        grid.addWidget(self.system_card, 1, 1)

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


    # ============================================
    # BASELINE
    # ============================================

    def init_baseline(self):

        self.log.setText("Initializing baseline...")

        self.init_thread = InitThread()
        self.init_thread.finished.connect(self.init_complete)
        self.init_thread.start()

        self.animate_progress()


    def init_complete(self, data):

        self.progress.setValue(100)

        if data["status"] == "baseline_created":

            self.integrity_card.value_label.setText(
                "Baseline Established"
            )

            self.log.setText("Baseline created successfully")


    # ============================================
    # SCAN
    # ============================================

    def scan(self):

        self.log.setText("Scanning boot integrity...")

        self.scan_thread = ScanThread()
        self.scan_thread.finished.connect(self.scan_complete)
        self.scan_thread.start()

        self.animate_progress()


    def scan_complete(self, data):

        self.progress.setValue(100)

        self.save_scan_history(data["status"])

        if data["status"] == "clean":

            self.integrity_card.value_label.setText(
                "Boot Integrity Verified"
            )

            self.integrity_card.value_label.setStyleSheet(
                "color: #22c55e"
            )

            self.log.setText(
                "Boot integrity safe.\n"
                f"Secure Boot: {self.secure_boot}\n"
                f"TPM: {self.tpm}"
            )

        else:

            self.integrity_card.value_label.setText(
                "Boot Integrity Compromised"
            )

            self.integrity_card.value_label.setStyleSheet(
                "color: red"
            )

            self.log.setText(json.dumps(data, indent=4))


    # ============================================
    # SHOW HISTORY
    # ============================================

    def show_history(self):

        dialog = QDialog(self)

        dialog.setWindowTitle("Scan & Baseline History")

        dialog.resize(600, 400)

        layout = QVBoxLayout()

        text = QTextEdit()
        text.setReadOnly(True)

        history_text = ""

        if os.path.exists(BASELINE_FILE):

            baseline_time = datetime.fromtimestamp(
                os.path.getmtime(BASELINE_FILE)
            )

            history_text += (
                f"Baseline Created:\n{baseline_time}\n\n"
            )

        if os.path.exists(HISTORY_FILE):

            with open(HISTORY_FILE, "r") as f:

                data = json.load(f)

                history_text += "Scan History:\n\n"

                for entry in reversed(data):

                    history_text += (
                        f"Time: {entry['timestamp']}\n"
                        f"Status: {entry['status']}\n"
                        f"Secure Boot: {entry['secure_boot']}\n"
                        f"TPM: {entry['tpm']}\n\n"
                    )

        text.setText(history_text)

        layout.addWidget(text)

        dialog.setLayout(layout)

        dialog.exec()


    # ============================================
    # PROGRESS
    # ============================================

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


    # ============================================
    # THEME
    # ============================================

    def toggle_theme(self, state):

        if state:
            self.setStyleSheet(LIGHT_THEME)
        else:
            self.setStyleSheet(DARK_THEME)


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = BootFXD()

    window.show()

    sys.exit(app.exec())