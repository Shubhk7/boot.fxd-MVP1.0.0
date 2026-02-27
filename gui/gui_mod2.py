import subprocess
import json
import threading
import platform
import time

import dearpygui.dearpygui as dpg


BACKEND = "./boot.fxd"


# -------------------------
# Backend execution
# -------------------------

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


# -------------------------
# UI helpers
# -------------------------

def set_status(text, color):

    dpg.set_value("status_text", text)
    dpg.configure_item("status_text", color=color)


def set_threat(text, color):

    dpg.set_value("threat_text", text)
    dpg.configure_item("threat_text", color=color)


def set_log(text):

    dpg.set_value("log_console", text)


def set_progress(val):

    dpg.set_value("progress_bar", val)


# -------------------------
# Progress animation
# -------------------------

progress_running = False


def animate_progress():

    global progress_running

    progress_running = True

    progress = 0.0

    while progress < 0.9 and progress_running:

        progress += 0.01

        dpg.set_value("progress_bar", progress)

        time.sleep(0.02)


def stop_progress():

    global progress_running

    progress_running = False

    dpg.set_value("progress_bar", 1.0)


# -------------------------
# Initialize baseline
# -------------------------

def init_baseline():

    def worker():

        set_status("INITIALIZING...", (255, 255, 0))
        set_log("Creating baseline...")

        animate_thread = threading.Thread(target=animate_progress)
        animate_thread.start()

        data = run_backend("--init")

        stop_progress()

        if data["status"] == "baseline_created":

            set_status("BASELINE CREATED", (0, 255, 0))

            set_log("Baseline created successfully.")

        else:

            set_status("ERROR", (255, 0, 0))

            set_log(json.dumps(data, indent=4))

    threading.Thread(target=worker).start()


# -------------------------
# Scan system
# -------------------------

def scan_system():

    def worker():

        set_status("SCANNING...", (255, 255, 0))
        set_log("Scanning system integrity...")

        animate_thread = threading.Thread(target=animate_progress)
        animate_thread.start()

        data = run_backend("--scan")

        stop_progress()

        if data["status"] == "clean":

            set_status("SYSTEM SAFE", (0, 255, 0))

            set_threat("NONE", (0, 255, 0))

            set_log("No threats detected.")

        else:

            set_status("SYSTEM COMPROMISED", (255, 0, 0))

            set_threat("HIGH", (255, 0, 0))

            set_log(json.dumps(data, indent=4))

    threading.Thread(target=worker).start()


# -------------------------
# DearPyGui setup
# -------------------------

dpg.create_context()


# Theme
with dpg.theme() as theme:

    with dpg.theme_component(dpg.mvAll):

        dpg.add_theme_color(
            dpg.mvThemeCol_WindowBg,
            (10, 15, 30),
            category=dpg.mvThemeCat_Core
        )


dpg.bind_theme(theme)


# Main window
with dpg.window(
    label="Boot.fxd Security Dashboard",
    width=900,
    height=600
):

    with dpg.group(horizontal=True):

        # Sidebar
        with dpg.child_window(width=220):

            dpg.add_text(
                "Boot.fxd",
                color=(0, 200, 255)
            )

            dpg.add_spacer(height=10)

            dpg.add_button(
                label="Initialize Baseline",
                callback=lambda: init_baseline(),
                width=-1
            )

            dpg.add_button(
                label="Scan System",
                callback=lambda: scan_system(),
                width=-1
            )

            dpg.add_spacer(height=20)

            dpg.add_text("System:")

            dpg.add_text(
                f"{platform.system()} {platform.release()}"
            )

        # Main dashboard
        with dpg.child_window(width=-1):

            dpg.add_text("Status:")

            dpg.add_text(
                "UNKNOWN",
                tag="status_text",
                color=(255, 255, 0)
            )

            dpg.add_spacer(height=10)

            dpg.add_text("Threat Level:")

            dpg.add_text(
                "NONE",
                tag="threat_text",
                color=(0, 255, 0)
            )

            dpg.add_spacer(height=10)

            dpg.add_progress_bar(
                default_value=0,
                tag="progress_bar",
                width=-1
            )

            dpg.add_spacer(height=10)

            dpg.add_text("Log Console:")

            dpg.add_input_text(
                multiline=True,
                readonly=True,
                tag="log_console",
                width=-1,
                height=300
            )


dpg.create_viewport(
    title="Boot.fxd Security Dashboard",
    width=900,
    height=600
)

dpg.setup_dearpygui()

dpg.show_viewport()

dpg.start_dearpygui()

dpg.destroy_context()
