import dearpygui.dearpygui as dpg
import subprocess
import threading
import json
import platform
import time
from datetime import datetime


BACKEND = "./boot.fxd"


# ============================================
# GLOBAL STATE
# ============================================

scan_running = False
current_progress = 0.0
last_scan_time = "Never"
boot_mode = "Unknown"
secure_boot = "Unknown"
tpm_status = "Unknown"


# ============================================
# THEME
# ============================================

def setup_theme():

    with dpg.theme(tag="cyber_theme"):

        with dpg.theme_component(dpg.mvAll):

            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (13,17,23))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (22,27,34))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (22,27,34))
            dpg.add_theme_color(dpg.mvThemeCol_Button, (0,170,140))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0,255,170))
            dpg.add_theme_color(dpg.mvThemeCol_Text, (200,220,255))

    dpg.bind_theme("cyber_theme")


# ============================================
# LOGGING SYSTEM
# ============================================

def log(message, level="INFO"):

    timestamp = datetime.now().strftime("%H:%M:%S")

    color = {
        "INFO": "[INFO]",
        "WARN": "[WARN]",
        "THREAT": "[THREAT]"
    }[level]

    current = dpg.get_value("log_console")

    new = f"[{timestamp}] {color} {message}\n"

    dpg.set_value("log_console", current + new)

    dpg.set_y_scroll("log_console", 999999)


# ============================================
# STATUS INDICATOR
# ============================================

def set_status(status):

    colors = {
        "SAFE": (0,255,140),
        "WARNING": (255,170,0),
        "COMPROMISED": (255,60,60),
        "SCANNING": (255,255,0),
        "UNKNOWN": (150,150,150)
    }

    dpg.configure_item("status_indicator", color=colors[status])
    dpg.set_value("status_text", status)


# ============================================
# BACKEND RUNNER
# ============================================

def run_backend(arg):

    try:

        result = subprocess.run(
            ["sudo", BACKEND, arg],
            capture_output=True,
            text=True
        )

        return json.loads(result.stdout)

    except Exception as e:

        return {"status": "error", "message": str(e)}


# ============================================
# SCAN THREAD
# ============================================

def scan_thread():

    global scan_running, last_scan_time

    scan_running = True

    dpg.configure_item("scan_btn", enabled=False)
    dpg.configure_item("init_btn", enabled=False)

    set_status("SCANNING")

    log("Boot integrity scan started")

    animate_progress()

    result = run_backend("--scan")

    stop_progress()

    last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    dpg.set_value("last_scan", last_scan_time)

    if result["status"] == "clean":

        set_status("SAFE")
        log("System integrity verified", "INFO")

    else:

        set_status("COMPROMISED")
        log("Boot integrity violation detected", "THREAT")

        log(json.dumps(result, indent=2), "THREAT")

    scan_running = False

    dpg.configure_item("scan_btn", enabled=True)
    dpg.configure_item("init_btn", enabled=True)


# ============================================
# BASELINE THREAD
# ============================================

def init_thread():

    log("Creating baseline")

    animate_progress()

    result = run_backend("--init")

    stop_progress()

    if result["status"] == "baseline_created":

        log("Baseline created successfully")

    else:

        log("Baseline creation failed", "WARN")


# ============================================
# PROGRESS SYSTEM
# ============================================

def animate_progress():

    global current_progress

    current_progress = 0

    while current_progress < 0.9 and scan_running:

        current_progress += 0.01

        dpg.set_value("progress_bar", current_progress)

        dpg.set_value("progress_text",
            f"{int(current_progress*100)}%")

        time.sleep(0.02)


def stop_progress():

    dpg.set_value("progress_bar", 1.0)
    dpg.set_value("progress_text", "100%")


# ============================================
# BUTTON CALLBACKS
# ============================================

def scan_callback():

    threading.Thread(target=scan_thread).start()


def init_callback():

    threading.Thread(target=init_thread).start()


# ============================================
# SYSTEM INFO
# ============================================

def detect_system_info():

    global boot_mode

    if platform.system() == "Linux":

        try:
            if subprocess.run(
                ["test","-d","/sys/firmware/efi"]
            ).returncode == 0:

                boot_mode = "UEFI"

            else:
                boot_mode = "BIOS"

        except:
            boot_mode = "Unknown"


# ============================================
# UI BUILDERS
# ============================================

def build_header():

    with dpg.child_window(height=60):

        with dpg.group(horizontal=True):

            dpg.add_text(
                "BOOT.FXD Security Dashboard",
                color=(0,255,170)
            )

            dpg.add_spacer(width=30)

            dpg.add_text("●", tag="status_indicator")

            dpg.add_text("UNKNOWN", tag="status_text")

            dpg.add_spacer(width=50)

            dpg.add_text(
                f"{platform.system()} {platform.release()}"
            )


def build_sidebar():

    with dpg.child_window(width=250):

        dpg.add_text("SYSTEM")

        dpg.add_separator()

        dpg.add_text(f"Boot Mode: {boot_mode}")

        dpg.add_text("Secure Boot: Unknown")

        dpg.add_text("TPM: Unknown")

        dpg.add_spacer(height=10)

        dpg.add_text("Last Scan:")

        dpg.add_text(last_scan_time, tag="last_scan")

        dpg.add_spacer(height=20)

        dpg.add_button(
            label="Initialize Baseline",
            tag="init_btn",
            callback=init_callback,
            width=-1
        )

        dpg.add_button(
            label="Scan System",
            tag="scan_btn",
            callback=scan_callback,
            width=-1
        )


def build_main():

    with dpg.child_window():

        dpg.add_text("System Integrity")

        dpg.add_progress_bar(
            tag="progress_bar",
            width=-1
        )

        dpg.add_text("0%", tag="progress_text")

        dpg.add_spacer(height=10)

        dpg.add_text("Log Console")

        dpg.add_input_text(
            tag="log_console",
            multiline=True,
            readonly=True,
            width=-1,
            height=300
        )


# ============================================
# MAIN UI
# ============================================

def build_ui():

    detect_system_info()

    dpg.create_context()

    setup_theme()

    with dpg.window():

        build_header()

        with dpg.group(horizontal=True):

            build_sidebar()

            build_main()

    dpg.create_viewport(
        title="BOOT.FXD Security Dashboard",
        width=1100,
        height=700
    )

    dpg.setup_dearpygui()

    dpg.show_viewport()

    set_status("SAFE")

    dpg.start_dearpygui()

    dpg.destroy_context()


# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":

    build_ui()