import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from pyadl import ADLManager, ADLException
import sv_ttk
import multiprocessing

class AmdGpuTool(tb.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("AMD GPU Information Tool")
        self.geometry("750x600")
        self.resizable(False, False)

        sv_ttk.set_theme("dark")

        try:
            self.device = ADLManager.getInstance().getDevices()[0]
        except (ADLException, IndexError) as e:
            self.show_error_and_exit(f"AMD ADL Initialisierung fehlgeschlagen:\n{e}\n\nStellen Sie sicher, dass die AMD Adrenalin Software korrekt installiert ist und eine AMD GPU erkannt wird.")
            return

        container = tb.Frame(self, padding=15)
        container.pack(fill=BOTH, expand=YES)
        
        title_label = tb.Label(
            container, text="AMD GPU System Information",
            font=("Helvetica", 20, "bold"), bootstyle="danger"
        )
        title_label.pack(pady=(0, 20))

        self.notebook = tb.Notebook(container)
        self.notebook.pack(fill=BOTH, expand=YES)

        self.create_specs_tab()
        self.create_usage_tab()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.update_usage()

    def show_error_and_exit(self, message):
        """Displays an error message in a separate dialog box."""
        self.withdraw()
        messagebox.showerror("Fehler", message)
        self.destroy()

    def on_closing(self):
        """Handles the window closing event."""
        self.destroy()

    def create_specs_tab(self):
        """Creates the tab with detailed GPU specifications."""
        specs_frame = tb.Frame(self.notebook, padding=10)
        self.notebook.add(specs_frame, text=" GPU Spezifikationen ")

        info_text = ScrolledText(specs_frame, wrap=tk.WORD, font=("Consolas", 11), relief="flat")
        info_text.pack(fill=BOTH, expand=YES)
        
        gpu_name = self.device.adapter_name
        driver_version = self.device.driver_version
        vram_size_mb = self.device.vram_size / (1024 * 1024)

        info_text.insert(END, f"{'GPU Name:'.ljust(25)} {gpu_name}\n")
        info_text.insert(END, f"{'Treiberversion:'.ljust(25)} {driver_version}\n")
        info_text.insert(END, "-"*60 + "\n\n")
        info_text.insert(END, f"{'Gesamter VRAM:'.ljust(25)} {vram_size_mb:.0f} MB\n")
        
        info_text.config(state="disabled")

    def create_usage_tab(self):
        """Creates the tab for real-time GPU usage monitoring."""
        usage_frame = tb.Frame(self.notebook, padding=15)
        self.notebook.add(usage_frame, text=" Live-Auslastung ")
        
        self.ui_elements = {}

        metrics = [
            ("GPU-Kern Auslastung", "gpu_util", "danger"),
            ("Leistungsaufnahme", "power", "info"),
            ("Temperatur", "temp", "success"),
            ("Lüftergeschwindigkeit", "fan", "primary"),
            ("Grafiktakt", "gfx_clock", None),
            ("Speichertakt", "mem_clock", None)
        ]
        
        for name, key, style in metrics:
            frame = tb.Frame(usage_frame)
            frame.pack(fill=X, pady=8)
            tb.Label(frame, text=f"{name}:", font=("Helvetica", 12), width=22, anchor="w").pack(side=LEFT)
            
            elements = {}
            if style:
                bar = tb.Progressbar(frame, bootstyle=f"{style}-striped", length=300)
                bar.pack(side=LEFT, fill=X, expand=YES, padx=5)
                elements['bar'] = bar
            
            label = tb.Label(frame, text="N/A", font=("Helvetica", 12, "bold"), width=15, anchor="w")
            label.pack(side=LEFT)
            elements['label'] = label
            
            self.ui_elements[key] = elements

    def update_usage(self):
        """Periodically updates the GPU usage bars and labels."""
        try:
            activity = self.device.get_activity()
            gpu_util = activity.get('engine_usage', 0)
            
            temp = self.device.get_temperature()
            fan_speed = self.device.get_fan_speed()
            gfx_clock = self.device.get_engine_clock()
            mem_clock = self.device.get_memory_clock()
            power_watts = self.device.get_power_usage()

            self.ui_elements['gpu_util']['bar']['value'] = gpu_util
            self.ui_elements['gpu_util']['label'].config(text=f"{gpu_util}%")
            
            if power_watts is not None:
                self.ui_elements['power']['label'].config(text=f"{power_watts:.1f} W")
                if 'bar' in self.ui_elements['power']: self.ui_elements['power']['bar'].pack_forget()
            else:
                self.ui_elements['power']['label'].config(text="N/A")

            self.ui_elements['temp']['bar']['value'] = temp
            self.ui_elements['temp']['label'].config(text=f"{temp}°C")
            
            self.ui_elements['fan']['bar']['value'] = fan_speed
            self.ui_elements['fan']['label'].config(text=f"{fan_speed}%")

            self.ui_elements['gfx_clock']['label'].config(text=f"{gfx_clock} MHz")
            self.ui_elements['mem_clock']['label'].config(text=f"{mem_clock} MHz")

        except ADLException as error:
            print(f"Fehler beim Aktualisieren der GPU-Statistiken: {error}")
            for key in self.ui_elements:
                self.ui_elements[key]['label'].config(text="Fehler")

        self.after(2000, self.update_usage)

if __name__ == "__main__":
    multiprocessing.freeze_support()

    app = AmdGpuTool()
    app.mainloop()