import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from pynvml import *
import sv_ttk
import multiprocessing

class NvidiaGpuTool(tb.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("NVIDIA GPU Information Tool")
        self.geometry("750x650")
        self.resizable(False, False)

        sv_ttk.set_theme("dark")

        try:
            nvmlInit()
            self.handle = nvmlDeviceGetHandleByIndex(0)
        except NVMLError as error:
            self.show_error_and_exit(f"NVIDIA NVML Initialisierung fehlgeschlagen:\n{error}\n\nStellen Sie sicher, dass aktuelle NVIDIA-Treiber installiert sind.")
            return

        container = tb.Frame(self, padding=15)
        container.pack(fill=BOTH, expand=YES)
        
        title_label = tb.Label(
            container, text="NVIDIA GPU System Information",
            font=("Helvetica", 20, "bold"), bootstyle="success"
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
        """Handles the clean shutdown of the NVML library."""
        try:
            nvmlShutdown()
        except NVMLError as error:
            print(f"Fehler beim Beenden von NVML: {error}")
        self.destroy()

    def create_specs_tab(self):
        """Creates the tab with detailed GPU specifications."""
        specs_frame = tb.Frame(self.notebook, padding=10)
        self.notebook.add(specs_frame, text=" GPU Spezifikationen ")

        info_text = ScrolledText(specs_frame, wrap=tk.WORD, font=("Consolas", 11), relief="flat")
        info_text.pack(fill=BOTH, expand=YES)
        
        gpu_name = nvmlDeviceGetName(self.handle)
        driver_version = nvmlSystemGetDriverVersion()
        memory_info = nvmlDeviceGetMemoryInfo(self.handle)
        power_limit_watts = nvmlDeviceGetEnforcedPowerLimit(self.handle) / 1000.0

        info_text.insert(END, f"{'GPU Name:'.ljust(25)} {gpu_name}\n")
        info_text.insert(END, f"{'Treiberversion:'.ljust(25)} {driver_version}\n")
        info_text.insert(END, "-"*60 + "\n\n")
        info_text.insert(END, f"{'Gesamter VRAM:'.ljust(25)} {memory_info.total / 1024**2:.0f} MB\n")
        info_text.insert(END, f"{'Leistungslimit (TDP):'.ljust(25)} {power_limit_watts:.0f} W\n")

        info_text.config(state="disabled")

    def create_usage_tab(self):
        """Creates the tab for real-time GPU usage monitoring."""
        usage_frame = tb.Frame(self.notebook, padding=15)
        self.notebook.add(usage_frame, text=" Live-Auslastung ")
        
        self.ui_elements = {}

        metrics = [
            ("GPU-Kern Auslastung", "gpu_util", "danger"),
            ("Speichercontroller", "mem_util", "danger"),
            ("VRAM-Nutzung", "vram", "warning"),
            ("Leistungsaufnahme", "power", "info"),
            ("Temperatur", "temp", "success"),
            ("Lüftergeschwindigkeit", "fan", "primary"),
            ("Grafiktakt", "gfx_clock", None),
            ("Speichertakt", "mem_clock", None)
        ]
        
        for name, key, style in metrics:
            frame = tb.Frame(usage_frame)
            frame.pack(fill=X, pady=6)
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
            util = nvmlDeviceGetUtilizationRates(self.handle)
            mem_info = nvmlDeviceGetMemoryInfo(self.handle)
            power_watts = nvmlDeviceGetPowerUsage(self.handle) / 1000.0
            temp = nvmlDeviceGetTemperature(self.handle, NVML_TEMPERATURE_GPU)
            fan_speed = nvmlDeviceGetFanSpeed(self.handle)
            gfx_clock = nvmlDeviceGetClockInfo(self.handle, NVML_CLOCK_GRAPHICS)
            mem_clock = nvmlDeviceGetClockInfo(self.handle, NVML_CLOCK_MEM)
            
            self.ui_elements['gpu_util']['bar']['value'] = util.gpu
            self.ui_elements['gpu_util']['label'].config(text=f"{util.gpu}%")
            
            self.ui_elements['mem_util']['bar']['value'] = util.memory
            self.ui_elements['mem_util']['label'].config(text=f"{util.memory}%")
            
            vram_percent = (mem_info.used / mem_info.total) * 100
            self.ui_elements['vram']['bar']['value'] = vram_percent
            self.ui_elements['vram']['label'].config(text=f"{mem_info.used / 1024**2:.0f} / {mem_info.total / 1024**2:.0f} MB")
            
            power_limit_watts = nvmlDeviceGetEnforcedPowerLimit(self.handle) / 1000.0
            self.ui_elements['power']['bar']['value'] = (power_watts / power_limit_watts) * 100
            self.ui_elements['power']['label'].config(text=f"{power_watts:.1f} W")
            
            self.ui_elements['temp']['bar']['value'] = temp
            self.ui_elements['temp']['label'].config(text=f"{temp}°C")
            
            self.ui_elements['fan']['bar']['value'] = fan_speed
            self.ui_elements['fan']['label'].config(text=f"{fan_speed}%")

            self.ui_elements['gfx_clock']['label'].config(text=f"{gfx_clock} MHz")
            self.ui_elements['mem_clock']['label'].config(text=f"{mem_clock} MHz")

        except NVMLError as error:
            print(f"Fehler beim Aktualisieren der GPU-Statistiken: {error}")
            for key in self.ui_elements:
                self.ui_elements[key]['label'].config(text="Fehler")

        self.after(1500, self.update_usage)

if __name__ == "__main__":
    multiprocessing.freeze_support()

    app = NvidiaGpuTool()
    app.mainloop()