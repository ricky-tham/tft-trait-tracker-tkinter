import tkinter as tk
from tkinter import filedialog, messagebox
import threading, time, json

from core.solver import load_units, load_traits_thresholds, find_valid_groups

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Unit Combination Solver")
        self.geometry("800x600")

        # Data storage
        self.units = []
        self.thresholds = {}
        self.solutions_file = None

        self._build_widgets()

    def _build_widgets(self):
        import_frame = tk.Frame(self)
        import_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(import_frame, text="Load Units JSON", command=self.load_units_file).pack(side=tk.LEFT, padx=5)
        tk.Button(import_frame, text="Load Thresholds JSON", command=self.load_thresholds_file).pack(side=tk.LEFT, padx=5)

        display_frame = tk.Frame(self)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        units_frame = tk.LabelFrame(display_frame, text="Units")
        units_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.unit_listbox = tk.Listbox(units_frame)
        self.unit_listbox.pack(fill=tk.BOTH, expand=True)
        unit_scroll = tk.Scrollbar(units_frame, command=self.unit_listbox.yview)
        unit_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.unit_listbox.config(yscrollcommand=unit_scroll.set)

        thresh_frame = tk.LabelFrame(display_frame, text="Trait Thresholds")
        thresh_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.threshold_listbox = tk.Listbox(thresh_frame)
        self.threshold_listbox.pack(fill=tk.BOTH, expand=True)
        thresh_scroll = tk.Scrollbar(thresh_frame, command=self.threshold_listbox.yview)
        thresh_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.threshold_listbox.config(yscrollcommand=thresh_scroll.set)

        control_frame = tk.Frame(self)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(control_frame, text="Group Size:").pack(side=tk.LEFT)
        self.group_size_var = tk.StringVar(value="7")
        tk.Entry(control_frame, textvariable=self.group_size_var, width=5).pack(side=tk.LEFT, padx=5)
        self.run_button = tk.Button(control_frame, text="Run Algorithm", state=tk.DISABLED, command=self.run_algorithm)
        self.run_button.pack(side=tk.LEFT, padx=20)

        status_frame = tk.LabelFrame(self, text="Status")
        status_frame.pack(fill=tk.BOTH, padx=10, pady=5)
        self.status_text = tk.Text(status_frame, height=6, state=tk.DISABLED)
        self.status_text.pack(fill=tk.BOTH, expand=True)

    def load_units_file(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not path:
            return
        try:
            data = load_units(path)
            if not isinstance(data, list):
                raise ValueError("Expected a list of units")
            for item in data:
                if "Name" not in item or "Trait" not in item or not isinstance(item["Trait"], list):
                    raise ValueError("Each unit must have 'Name' and 'Trait' (list)")
            self.units = data
            self.refresh_unit_list()
            self.check_enable_run()
        except Exception as e:
            messagebox.showerror("Invalid Units File", str(e))

    def load_thresholds_file(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not path:
            return
        try:
            data = load_traits_thresholds(path)
            if not isinstance(data, dict):
                raise ValueError("Expected a dict of trait thresholds")
            for k, v in data.items():
                if not isinstance(v, int):
                    raise ValueError("Thresholds must be integers")
            self.thresholds = data
            self.refresh_threshold_list()
            self.check_enable_run()
        except Exception as e:
            messagebox.showerror("Invalid Thresholds File", str(e))

    def refresh_unit_list(self):
        self.unit_listbox.delete(0, tk.END)
        for u in self.units:
            self.unit_listbox.insert(tk.END, f"{u['Name']}: {', '.join(u['Trait'])}")

    def refresh_threshold_list(self):
        self.threshold_listbox.delete(0, tk.END)
        for trait, thresh in self.thresholds.items():
            self.threshold_listbox.insert(tk.END, f"{trait}: {thresh}")

    def check_enable_run(self):
        if self.units and self.thresholds:
            self.run_button.config(state=tk.NORMAL)
        else:
            self.run_button.config(state=tk.DISABLED)

    def run_algorithm(self):
        try:
            size = int(self.group_size_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid group size")
            return
        self.run_button.config(state=tk.DISABLED)
        self._append_status("Starting algorithm...")

        def worker():
            start = time.time()
            solutions = find_valid_groups(
                self.units,
                self.thresholds,
                group_size=size,
                min_active_traits=8
            )
            elapsed = time.time() - start
            filename = f"valid_groups_size_{size}.json"
            with open(filename, 'w') as jf:
                json.dump(solutions, jf, indent=4)
            self.solutions_file = filename
            self._append_status(f"Finished in {elapsed:.2f}s, found {len(solutions)} groups.")
            self._append_status(f"Results saved to {filename}")
            self.run_button.config(state=tk.NORMAL)

        threading.Thread(target=worker, daemon=True).start()

    def _append_status(self, text):
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, text)
        self.status_text.config(state=tk.DISABLED)