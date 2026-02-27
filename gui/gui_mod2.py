import dearpygui.dearpygui as dpg
import subprocess
import threading
import json
import platform
import time
from datetime import datetime
import queue

BACKEND = "./boot.fxd"

# ============================================
# GLOBAL STATE
# ============================================

scan_running = False
current_progress = 0.0
last_scan_time = "Never"
boot_mode = "Unknown"

log_queue = queue.Queue()
progress_queue = queue.Queue()
status_queue = queue.Queue()


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
# THREAD SAFE LOGGING
# ============================================

def log(message, level="INFO"):

    timestamp = datetime.now().strftime("%H:%M:%S")

    tag = {
        "INFO": "[INFO]",
        "WARN": "[WARN]",
        "THREAT": "[THREAT]"
    }[level]

    log_queue.put(f"[{timestamp}] {tag} {message}")


# ============================================
# STATUS SYSTEM
# ============================================

def set_status(status):
    status_queue.put(status)


# ============================================
# SAFE UI UPDATE LOOP (MAIN THREAD ONLY)
# ============================================

def ui_update_loop():

    # log update
    while not log_queue.empty():
        msg = log_queue.get()

        current = dpg.get_value("log_console")
        dpg.set_value("log_console", current + msg + "\n")
        dpg.set_y_scroll("log_console", -1)

    # progress update
    while not progress_queue.empty():
        progress = progress_queue.get()

        dpg.set_value("progress_bar", progress)
        dpg.set_value("progress_text", f"{int(progress*100)}%")

    # status update
    while not status_queue.empty():

        status = status_queue.get()

        colors = {
            "SAFE": (0,255,140),
            "WARNING": (255,170,0),
            "COMPROMISED": (255,60,60),
            "SCANNING": (255,255,0),
            "UNKNOWN": (150,150,150)
        }

        dpg.configure_item("status_indicator", color=colors[status])
        dpg.set_value("status_text", status)

    dpg.set_frame_callback(1, ui_update_loop)


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
# PROGRESS THREAD
# ============================================

def animate_progress():

    progress = 0

    while scan_running and progress < 0.9:

        progress += 0.01
        progress_queue.put(progress)

        time.sleep(0.02)


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

    threading.Thread(target=animate_progress, daemon=True).start()

    result = run_backend("--scan")

    progress_queue.put(1.0)

    last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    dpg.set_value("last_scan", last_scan_time)

    if result.get("status") == "clean":

        set_status("SAFE")
        log("System integrity verified")

    else:

        set_status("COMPROMISED")
        log("Boot integrity violation detected", "THREAT")

    scan_running = False

    dpg.configure_item("scan_btn", enabled=True)
    dpg.configure_item("init_btn", enabled=True)


# ============================================
# CALLBACKS
# ============================================

def scan_callback():
    threading.Thread(target=scan_thread, daemon=True).start()


def init_callback():
    threading.Thread(target=run_backend, args=("--init",), daemon=True).start()
    log("Baseline initialized")


# ============================================
# SYSTEM INFO
# ============================================

def detect_system_info():

    global boot_mode

    if platform.system() == "Linux":

        if subprocess.run(
            ["test","-d","/sys/firmware/efi"]
        ).returncode == 0:

            boot_mode = "UEFI"
        else:
            boot_mode = "BIOS"


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

        dpg.add_progress_bar(tag="progress_bar", width=-1)

        dpg.add_text("0%", tag="progress_text")

        dpg.add_spacer(height=10)

        dpg.add_text("Log Console")

        dpg.add_input_text(
            tag="log_console",
            multiline=True,
            readonly=True,
            width=-1,
            height=400
        )


# ============================================
# MAIN UI
# ============================================

def build_ui():

    detect_system_info()

    dpg.create_context()

    setup_theme()

    with dpg.window(
        tag="main_window",
        no_title_bar=True,
        no_move=True,
        no_resize=True
    ):

        build_header()

        with dpg.group(horizontal=True):

            build_sidebar()
            build_main()

    dpg.create_viewport(
        title="BOOT.FXD Security Dashboard",
        width=1200,
        height=800
    )

    dpg.setup_dearpygui()

    dpg.set_primary_window("main_window", True)

    dpg.show_viewport()

    ui_update_loop()

    set_status("SAFE")

    dpg.start_dearpygui()

    dpg.destroy_context()


# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":

    build_ui()