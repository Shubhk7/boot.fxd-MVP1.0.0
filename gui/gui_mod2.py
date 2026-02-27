import dearpygui.dearpygui as dpg
import subprocess
import threading
import json
import platform
import time
import os

from datetime import datetime


BACKEND = "./boot.fxd"


# ============================================
# GLOBAL STATE
# ============================================

scan_result = None
init_result = None

scan_running = False
init_running = False

last_scan_time = "Never"


# ============================================
# SYSTEM DETECTION
# ============================================

def get_boot_mode():

    try:
        if os.path.exists("/sys/firmware/efi"):
            return "UEFI"
        else:
            return "BIOS"
    except:
        return "Unknown"


def get_secure_boot_status():

    try:

        result = subprocess.run(
            ["mokutil", "--sb-state"],
            capture_output=True,
            text=True
        )

        output = result.stdout.lower()

        if "enabled" in output:
            return "Enabled"

        elif "disabled" in output:
            return "Disabled"

        else:
            return "Unknown"

    except:
        return "Not Available"


def get_tpm_status():

    try:

        if os.path.exists("/dev/tpm0") or os.path.exists("/dev/tpmrm0"):
            return "Present"

        if os.path.exists("/sys/class/tpm"):
            return "Present"

        return "Not Present"

    except:
        return "Unknown"


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
# LOG SYSTEM
# ============================================

def log(message, level="INFO"):

    timestamp = datetime.now().strftime("%H:%M:%S")

    prefix = {
        "INFO": "[INFO]",
        "WARN": "[WARN]",
        "THREAT": "[THREAT]"
    }.get(level, "[INFO]")

    current = dpg.get_value("log_console")

    new = f"[{timestamp}] {prefix} {message}\n"

    dpg.set_value("log_console", current + new)

    dpg.set_y_scroll("log_container", -1)


# ============================================
# STATUS INDICATOR
# ============================================

def set_status(status):

    colors = {
        "SAFE": (0,255,140),
        "SCANNING": (255,255,0),
        "COMPROMISED": (255,60,60),
        "INITIALIZING": (255,170,0),
        "UNKNOWN": (150,150,150)
    }

    dpg.configure_item("status_indicator", color=colors.get(status, (150,150,150)))

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

        return {
            "status": "error",
            "message": str(e)
        }


# ============================================
# THREAD WORKERS
# ============================================

def scan_worker():

    global scan_result

    scan_result = run_backend("--scan")


def init_worker():

    global init_result

    init_result = run_backend("--init")


# ============================================
# BUTTON CALLBACKS
# ============================================

def scan_callback():

    global scan_running, scan_result

    if scan_running:
        return

    scan_result = None

    scan_running = True

    dpg.configure_item("scan_btn", enabled=False)

    set_status("SCANNING")

    log("Boot integrity scan started")

    dpg.set_value("progress_bar", 0)

    threading.Thread(target=scan_worker, daemon=True).start()


def init_callback():

    global init_running, init_result

    if init_running:
        return

    init_result = None

    init_running = True

    dpg.configure_item("init_btn", enabled=False)

    set_status("INITIALIZING")

    log("Baseline initialization started")

    dpg.set_value("progress_bar", 0)

    threading.Thread(target=init_worker, daemon=True).start()


# ============================================
# UPDATE LOOP
# ============================================

def update_loop():

    global scan_running, scan_result
    global init_running, init_result
    global last_scan_time

    progress = dpg.get_value("progress_bar")

    if scan_running or init_running:

        if progress < 0.95:
            dpg.set_value("progress_bar", progress + 0.002)


    if scan_running and scan_result is not None:

        dpg.set_value("progress_bar", 1.0)

        last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        dpg.set_value("last_scan", last_scan_time)

        if scan_result.get("status") == "clean":

            set_status("SAFE")

            log("System integrity verified")

        else:

            set_status("COMPROMISED")

            log("Boot integrity violation detected", "THREAT")

            log(json.dumps(scan_result, indent=2), "THREAT")

        scan_running = False

        dpg.configure_item("scan_btn", enabled=True)


    if init_running and init_result is not None:

        dpg.set_value("progress_bar", 1.0)

        if init_result.get("status") == "baseline_created":

            set_status("SAFE")

            log("Baseline created successfully")

        else:

            set_status("UNKNOWN")

            log("Baseline creation failed", "WARN")

        init_running = False

        dpg.configure_item("init_btn", enabled=True)


    dpg.set_frame_callback(
        dpg.get_frame_count() + 1,
        lambda: update_loop()
    )


# ============================================
# UI BUILD
# ============================================

def build_ui():

    dpg.create_context()

    setup_theme()

    boot_mode = get_boot_mode()

    secure_boot = get_secure_boot_status()

    tpm_status = get_tpm_status()

    with dpg.window(
        tag="main_window",
        no_move=True,
        no_resize=True,
        no_close=True
    ):

        with dpg.child_window(height=60):

            with dpg.group(horizontal=True):

                dpg.add_text(
                    "BOOT.FXD Security Dashboard",
                    color=(0,255,170)
                )

                dpg.add_spacer(width=20)

                dpg.add_text("●", tag="status_indicator")

                dpg.add_text("SAFE", tag="status_text")

                dpg.add_spacer(width=40)

                dpg.add_text(
                    f"{platform.system()} {platform.release()}"
                )


        with dpg.group(horizontal=True):

            with dpg.child_window(width=250):

                dpg.add_text("SYSTEM")

                dpg.add_separator()

                dpg.add_text(f"Boot Mode: {boot_mode}")

                dpg.add_text(f"Secure Boot: {secure_boot}")

                dpg.add_text(f"TPM: {tpm_status}")

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


            with dpg.child_window(width=-1):

                dpg.add_text("System Integrity")

                dpg.add_progress_bar(
                    tag="progress_bar",
                    width=-1
                )

                dpg.add_spacer(height=10)

                dpg.add_text("Log Console")

                with dpg.child_window(
                    tag="log_container",
                    height=-1
                ):

                    dpg.add_input_text(
                        tag="log_console",
                        multiline=True,
                        readonly=True,
                        width=-1,
                        height=-1
                    )


    dpg.create_viewport(
        title="BOOT.FXD Security Dashboard",
        width=1200,
        height=800
    )

    dpg.setup_dearpygui()

    dpg.show_viewport()

    dpg.set_primary_window("main_window", True)

    set_status("SAFE")

    update_loop()

    dpg.start_dearpygui()

    dpg.destroy_context()


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":

    build_ui()