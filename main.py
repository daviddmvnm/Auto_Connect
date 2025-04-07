import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
import threading
import json
import os
import logging
from PIL import Image, ImageTk

from functions.outreach_eval import load_acceptance_metrics
from functions.ml_train_new import ModelTrainer
from pipeline_entrypoint import collect_and_prepare_data, send_connection_invites, refresh_connection_tracking
from functions.utils import load_config, resource_path
from functions.utils import resource_path
CONFIG_PATH = resource_path("config.json")


import os
import sys
import platform


#potential future development? left in here for now
def create_desktop_shortcut():
    system = platform.system()
    exe_path = sys.executable
    app_name = "AutoConnect"
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

    if system == "Windows":
        try:
            import winshell
            from win32com.client import Dispatch

            shortcut_path = os.path.join(desktop_path, f"{app_name}.lnk")
            icon_path = os.path.join(os.path.dirname(exe_path), "iconb.ico")

            if not os.path.exists(shortcut_path):
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = exe_path
                shortcut.WorkingDirectory = os.path.dirname(exe_path)
                shortcut.IconLocation = icon_path if os.path.exists(icon_path) else exe_path
                shortcut.save()
        except Exception as e:
            print(f"[Shortcut] Failed to create Windows shortcut: {e}")

    elif system == "Linux":
        shortcut_path = os.path.join(desktop_path, f"{app_name}.desktop")
        icon_path = os.path.join(os.path.dirname(exe_path), "iconb.png")  

        desktop_entry = f"""[Desktop Entry]
Type=Application
Name={app_name}
Exec="{exe_path}"
Icon={icon_path if os.path.exists(icon_path) else "utilities-terminal"}
Terminal=false
"""

        try:
            if not os.path.exists(shortcut_path):
                with open(shortcut_path, "w") as f:
                    f.write(desktop_entry)
                os.chmod(shortcut_path, 0o755)
        except Exception as e:
            print(f"[Shortcut] Failed to create Linux .desktop file: {e}")

    elif system == "Darwin":  # macOS      
        pass 

class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.text_widget.tag_configure("log", foreground="#6bb3f2", font=("Courier New", 10))

    def emit(self, record):
        msg = self.format(record)
        def write():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n', "log")
            self.text_widget.configure(state='disabled')
            self.text_widget.see(tk.END)
        self.text_widget.after(0, write)


def show_splash_popup():
    splash = tb.Toplevel()
    splash.title("Welcome to AutoConnect Prototype")
    splash.geometry("500x400")
    splash.resizable(False, False)
    splash.attributes("-topmost", True)

    
    splash.grab_set()
    try:
        icon_path = resource_path("iconb1.png")
        icon_img = ImageTk.PhotoImage(Image.open(icon_path))
        splash.iconphoto(False, icon_img)
    except Exception as e:
        logging.warning(f"Failed to set splash icon: {e}")

    tb.Label(splash, text="Prototype Notice", font=("Ubuntu Medium", 12, "bold")).pack(pady=(15, 5))
    tb.Label(splash, text="This is an early prototype.\nSee the manual.txt file for usage guidance.",
             justify="left", wraplength=350).pack(pady=5)
    tb.Label(splash, text="a window will brielfy fullscreen when collecting data after it finds your desired tab feel free to minimise",
             justify="left", wraplength=350).pack(pady=5)
    tb.Label(splash, text="It's recommended to keep the tab in the background as interacting with it can disrupt the script",
             justify="left", wraplength=350).pack(pady=5)
    tb.Label(splash, text="this a tradeoff for better bot detection avoidance and less chance of being shadowbanned",
             justify="left", wraplength=350).pack(pady=5)

    def close_splash():
        splash.destroy()

    tb.Button(splash, text="Continue", command=close_splash, bootstyle="success").pack(pady=(10, 15))




import subprocess
import platform
import webbrowser

def open_manual():
    manual_path = resource_path("manual.txt")
    if not os.path.exists(manual_path):
        messagebox.showerror("Manual Not Found", "The manual file could not be found.")
        return

    try:
        if platform.system() == "Windows":
            os.startfile(manual_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.call(["open", manual_path], stderr=subprocess.DEVNULL)
        else:  # Linux and others
            subprocess.call(["xdg-open", manual_path], stderr=subprocess.DEVNULL)
    except Exception as e:
        logging.error(f"Failed to open manual: {e}")
        messagebox.showerror("Error", f"Could not open the manual:\n{e}")



def start_gui():
    app = tb.Window(themename="vapor")
    # Icon shown inside the GUI (e.g., splash, logo, etc.)
    gui_icon_path = resource_path("iconb1.png")
    gui_icon_img = ImageTk.PhotoImage(Image.open(gui_icon_path))
    app.iconphoto(False, gui_icon_img)

# Override taskbar / Alt+Tab icon if supported
    try:
        if platform.system() == "Windows":
            taskbar_icon_path = resource_path("iconb1.ico")
            app.iconbitmap(default=taskbar_icon_path)
    except Exception as e:
        logging.warning(f"Failed to set taskbar icon: {e}")
        

    app.title("AutoConnect | LinkedIn Outreach Assistant")
    app.geometry("750x600")
    app.resizable(False, False)

    default_font = ("Lato", 12)
    header_font = ("Ubuntu Medium", 16, "bold")
    app.option_add("*Font", default_font)

    total_sent = tk.StringVar(value="Total Sent: 0")
    total_accepted = tk.StringVar(value="Total Accepted: 0")
    acceptance_rate = tk.StringVar(value="Acceptance Rate: 0.00%")
    status_var = tk.StringVar(value="Idle...")

    progress = tb.Progressbar(app, bootstyle="info-striped", mode="indeterminate", length=600)

    log_display = tk.Text(app, height=10, state='disabled', font=("Courier New", 10), bg="#1e1e1e", fg="#f27b7b", insertbackground="#f27b7b")
    log_scroll = tb.Scrollbar(app, command=log_display.yview)
    log_display.configure(yscrollcommand=log_scroll.set)

    log_handler = TextHandler(log_display)
    log_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logging.getLogger().addHandler(log_handler)
    logging.getLogger().setLevel(logging.INFO)

    def run_with_loading(task_fn, status_message):
        def wrapper():
            status_var.set(status_message)
            progress.start(10)
            try:
                task_fn()
            except Exception as e:
                logging.error(f"Exception occurred: {e}")
                status_var.set(f"Error: {str(e)}")
            else:
                status_var.set("Done.")
            finally:
                progress.stop()
        threading.Thread(target=wrapper).start()

    def collect_data():
        run_with_loading(lambda: (collect_and_prepare_data(), update_stats()), "Collecting data...")

    def send_only_invites():
        run_with_loading(lambda: (send_connection_invites(), update_stats()), "Sending invites...")

    def update_only_tracking():
        run_with_loading(lambda: (refresh_connection_tracking(), update_stats()), "Refreshing tracking...")


    def train_new_model():
        run_with_loading(lambda: (ModelTrainer().run(), update_stats()), "Training model...")

    def update_stats():
        try:
            sent, accepted, rate = load_acceptance_metrics()
            total_sent.set(f"Total Sent: {sent}")
            total_accepted.set(f"Total Accepted: {accepted}")
            acceptance_rate.set(f"Acceptance Rate: {rate:.2f}%")
        except Exception as e:
            logging.error(f"Failed to update stats: {e}")
            total_sent.set("Total Sent: -")
            total_accepted.set("Total Accepted: -")
            acceptance_rate.set("Acceptance Rate: -")

    def open_config_editor():
        config = load_config()
        editor = tb.Toplevel(app)
        editor.title("Edit Config")
        editor.geometry("420x800")
        editor.resizable(False, True)  # allow vertical stretching

        entries = {}

        def create_entry(label, key):
            row = tb.Frame(editor, padding=5)
            row.pack(fill="x")
            tb.Label(row, text=label, width=15).pack(side="left")
            var = tk.StringVar(value=str(config.get(key, "")))
            ent = tb.Entry(row, textvariable=var, width=30)
            ent.pack(side="left", fill="x", expand=True)
            entries[key] = var

        create_entry("Max Profiles", "max_profiles")
        create_entry("Max Invites", "max_invites")
        create_entry("Target Label", "target_label")
        create_entry("Model Path", "model_path")

        keyword_frame = tb.Labelframe(editor, text="Interest Keywords", padding=10)
        keyword_frame.pack(fill="both", expand=True, padx=10, pady=5)
        keyword_list = config.get("interest_keywords", [])

        new_kw_var = tk.StringVar()
        input_row = tb.Frame(keyword_frame)
        input_row.pack(fill="x", pady=(0, 10))
        tb.Label(input_row, text="Type keywords of interest (minimum 4):").pack(side="top", anchor="w", pady=(0, 2))
        entry_and_btn = tb.Frame(input_row)
        entry_and_btn.pack(fill="x")
        entry_box = tb.Entry(entry_and_btn, textvariable=new_kw_var)
        entry_box.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tb.Button(entry_and_btn, text="Add", command=lambda: add_keyword(), bootstyle="success-outline").pack(side="left")

        # Scrollable pill area
        canvas = tk.Canvas(keyword_frame, bg="#2b2b2b", highlightthickness=0)
        scrollbar = tb.Scrollbar(keyword_frame, orient="vertical", command=canvas.yview)
        pill_area = tb.Frame(canvas)

        pill_area.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=pill_area, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def render_keywords():
            for widget in pill_area.winfo_children():
                widget.destroy()
            for keyword in keyword_list:
                frame = tb.Frame(pill_area)
                frame.pack(anchor="w", pady=2)
                lbl = tb.Label(frame, text=keyword, bootstyle="info", padding=(5, 2))
                lbl.pack(side="left")
                tb.Button(frame, text="x", width=2, command=lambda k=keyword: remove_keyword(k), bootstyle="info-link").pack(side="left")

        def remove_keyword(keyword):
            keyword_list.remove(keyword)
            render_keywords()

        def add_keyword():
            new_kw = new_kw_var.get().strip()
            if new_kw and new_kw not in keyword_list:
                keyword_list.append(new_kw)
                new_kw_var.set("")
                render_keywords()

        render_keywords()

        def save_config():
            try:
                new_config = {
                    k: int(v.get()) if v.get().isdigit() else v.get()
                    for k, v in entries.items()
                }
                new_config["interest_keywords"] = keyword_list
                with open(CONFIG_PATH, "w") as f:
                    json.dump(new_config, f, indent=2)
                messagebox.showinfo("Config Saved", "Configuration updated successfully.")
                editor.destroy()
            except Exception as e:
                messagebox.showerror("Save Failed", str(e))

        tb.Button(
            editor,
            text="Save",
            command=save_config,
            bootstyle="danger-outline",
            width=12
        ).pack(padx=10, pady=10, ipady=4)

    def clear_log():
        log_display.configure(state='normal')
        log_display.delete('1.0', tk.END)
        log_display.configure(state='disabled')

    def create_buttons_frame_with_logo(parent):
        frame = tb.Frame(parent, padding=10)

        # --- Logo on the left ---
        try:
            logo_path = resource_path("iconb.png")
            logo_img = Image.open(logo_path)
            resample = getattr(Image, 'Resampling', Image).LANCZOS
            logo_img = logo_img.resize((120, 120), resample=resample)
            logo_tk = ImageTk.PhotoImage(logo_img)
            logo_label = tb.Label(frame, image=logo_tk)
            logo_label.image = logo_tk
            logo_label.grid(row=0, column=0, rowspan=3, padx=(5, 20), sticky="n")
        except Exception as e:
            logging.warning(f"Failed to load logo: {e}")

        # --- Button styles ---
        button_style1 = {"bootstyle": "success-outline", "width": 16}
        button_style2 = {"bootstyle": "info-outline", "width": 16}

        # --- First row of buttons ---
        tb.Button(frame, text="Collect Data", command=collect_data, **button_style1).grid(row=0, column=1, padx=5, pady=3)
        tb.Button(frame, text="Send Invites", command=send_only_invites, **button_style1).grid(row=0, column=2, padx=5, pady=3)
        tb.Button(frame, text="Update Tracking", command=update_only_tracking, **button_style1).grid(row=0, column=3, padx=5, pady=3)

        # --- Second row of buttons ---
        tb.Button(frame, text="Open Manual", command=open_manual, **button_style2).grid(row=1, column=1, padx=5, pady=3)
        tb.Button(frame, text="Train New Model", command=train_new_model, **button_style2).grid(row=1, column=2, padx=5, pady=3)
        tb.Button(frame, text="Clear Log", command=clear_log, **button_style2).grid(row=1, column=3, padx=5, pady=3)

        return frame

    def create_config_button(parent):
        frame = tb.Frame(parent, padding=5)
        tb.Button(frame, text="Edit Config", command=open_config_editor, bootstyle="success-outline", width=30).pack(side=tk.LEFT)
        return frame

    def create_stats_frame(parent):
        stats = tb.Labelframe(parent, text="Outreach Stats", padding=10)
        tb.Label(stats, textvariable=total_sent).pack(anchor="w")
        tb.Label(stats, textvariable=total_accepted).pack(anchor="w")
        tb.Label(stats, textvariable=acceptance_rate).pack(anchor="w")
        return stats

    def create_status_bar(parent):
        frame = tb.Frame(parent, padding=(10, 5))
        tb.Label(frame, textvariable=status_var).pack(anchor="w")
        return frame

    create_buttons_frame_with_logo(app).pack(pady=(20, 5), padx=(5, 10), fill="x")
    create_config_button(app).pack(pady=(0, 5))
    create_stats_frame(app).pack(pady=10, fill="x", padx=10)
    progress.pack(pady=(5, 5))
    create_status_bar(app).pack(fill="x", padx=10)
    log_display.pack(fill="both", expand=True, padx=10, pady=(0, 5))
    log_scroll.pack(fill="y", side="right")

    update_stats()
    show_splash_popup() 
    app.mainloop()

if __name__ == "__main__":
    create_desktop_shortcut()
    start_gui()
