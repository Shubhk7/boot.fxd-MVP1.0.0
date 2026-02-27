import subprocess
import json
import threading
import platform
import dearpygui.dearpygui as dpg

BACKEND = "./boot.fxd"


# ------------------------
# Backend runner
# ------------------------

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


# ------------------------
# UI update helpers
# ------------------------

def set_status(text, color=(0,255,0)):

    dpg.set_value("status_text", text)
    dpg.configure_item("status_text", color=color)


def set_threat(text, color=(0,255,0)):

    dpg.set_value("threat_text", text)
    dpg.configure_item("threat_text", color=color)


def set_log(text):

    dpg.set_value("log_console", text)


def set_progress(val):

    dpg.set_value("progress_bar", val)


# ------------------------
# Progress animation
# ------------------------

def animate_progress():

    for i in range(0, 90, 2):

        dpg.set_value("progress_bar", i/100)
        dpg.sleep(0.02)


# ------------------------
# Initialize baseline
# ------------------------

def init_baseline():

    def worker():

        set_status("INITIALIZING...", (255,255,0))
        set_progress(0)

        animate_progress()

        data = run_backend("--init")

        set_progress(1.0)

        if data["status"] == "baseline_created":

            set_status("BASELINE CREATED", (0,255,0))
            set_log("Baseline successfully created.")

        else:

            set_status("ERROR", (255,0,0))
            set_log(str(data))

    threading.Thread(target=worker).start()


# ------------------------
# Scan system
# ------------------------

def scan_system():

    def worker():

        set_status("SCANNING...", (255,255,0))
        set_progress(0)

        animate_progress()

        data = run_backend("--scan")

        set_progress(1.0)

        if data["status"] == "clean":

            set_status("SYSTEM SAFE", (0,255,0))
            set_threat("NONE", (0,255,0))
            set_log("No threats detected.")

        else:

            set_status("COMPROMISED", (255,0,0))
            set_threat("HIGH", (255,0,0))

            set_log(json.dumps(data, indent=4))

    threading.Thread(target=worker).start()


# ------------------------
# DearPyGui UI
# ------------------------

dpg.create_context()

with dpg.window(label="Boot.fxd Security Dashboard", width=900, height=600):

    with dpg.group(horizontal=True):

        # Sidebar
        with dpg.child_window(width=200):

            dpg.add_text("Boot.fxd", color=(0,200,255))
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
                color=(255,255,0)
            )

            dpg.add_spacer(height=10)

            dpg.add_text("Threat Level:")
            dpg.add_text(
                "NONE",
                tag="threat_text",
                color=(0,255,0)
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


# Theme
with dpg.theme() as theme:

    with dpg.theme_component(dpg.mvAll):

        dpg.add_theme_color(
            dpg.mvThemeCol_WindowBg,
            (10,15,30),
            category=dpg.mvThemeCat_Core
        )

dpg.bind_theme(theme)


dpg.create_viewport(
    title="Boot.fxd Security Dashboard",
    width=900,
    height=600
)

dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()