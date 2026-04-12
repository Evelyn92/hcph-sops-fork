#!/usr/bin/env python3
from __future__ import annotations

import shlex
import shutil
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox


SCRIPT_DIR = Path(__file__).resolve().parent
S1_SCRIPT = SCRIPT_DIR / "s1_edf2bids_program.py"
S2_SCRIPT = SCRIPT_DIR / "s2_et_program.py"
DEFAULT_DATASETS_ROOT = Path("/Volumes/FS_PROJETS/MatTechLab/yiwei.jia/datasets")


def parse_criteria(raw: str) -> list[float]:
    items = [x.strip() for x in raw.split(",") if x.strip()]
    if not items:
        raise ValueError("Criteria list is empty.")

    values: list[float] = []
    for item in items:
        value = float(item)
        if value <= 0:
            raise ValueError(f"Criteria must be > 0, got {value}.")
        if value not in values:
            values.append(value)
    return values


def find_fixation_edfs(dataset_dir: Path) -> list[Path]:
    candidates = []
    for path in dataset_dir.iterdir():
        if not path.is_file() or path.suffix.lower() != ".edf":
            continue
        name = path.name.lower()
        if "fixation_dots" in name:
            candidates.append(path)
    return sorted(candidates)


class BatchApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("S1 + S2 Batch Runner")
        self.geometry("940x680")

        self.dataset_var = tk.StringVar(value=str(DEFAULT_DATASETS_ROOT))
        self.criteria_var = tk.StringVar(value="0.1,0.15,0.2,0.3")
        self.conda_env_var = tk.StringVar(value="edfenv")
        self.use_conda_var = tk.BooleanVar(value=True)
        self.running = False

        self._build_ui()

    def _build_ui(self) -> None:
        top = tk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        tk.Label(top, text="Dataset folder (example: .../datasets/0010)").grid(row=0, column=0, sticky="w")
        tk.Entry(top, textvariable=self.dataset_var, width=95).grid(row=1, column=0, sticky="we", padx=(0, 6))
        tk.Button(top, text="Browse...", command=self.browse_dataset).grid(row=1, column=1, sticky="e")

        tk.Label(top, text="Criteria array (comma separated)").grid(row=2, column=0, sticky="w", pady=(10, 0))
        tk.Entry(top, textvariable=self.criteria_var, width=95).grid(row=3, column=0, sticky="we", padx=(0, 6))

        opts = tk.Frame(top)
        opts.grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 0))
        tk.Checkbutton(opts, text="Run with conda env", variable=self.use_conda_var).pack(side="left")
        tk.Label(opts, text="env:").pack(side="left", padx=(16, 4))
        tk.Entry(opts, textvariable=self.conda_env_var, width=16).pack(side="left")

        actions = tk.Frame(top)
        actions.grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.run_btn = tk.Button(actions, text="Run S1 -> S2", command=self.start_run, width=16)
        self.run_btn.pack(side="left")
        tk.Button(actions, text="Clear Log", command=self.clear_log, width=12).pack(side="left", padx=(8, 0))

        top.columnconfigure(0, weight=1)

        self.log_text = tk.Text(self, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log("Ready.")

    def browse_dataset(self) -> None:
        initial = self.dataset_var.get().strip() or str(DEFAULT_DATASETS_ROOT)
        selected = filedialog.askdirectory(title="Select dataset folder", initialdir=initial)
        if selected:
            self.dataset_var.set(selected)

    def clear_log(self) -> None:
        self.log_text.delete("1.0", tk.END)

    def log(self, message: str) -> None:
        self.log_text.insert(tk.END, message.rstrip() + "\n")
        self.log_text.see(tk.END)
        self.update_idletasks()

    def thread_log(self, message: str) -> None:
        self.after(0, self.log, message)

    def start_run(self) -> None:
        if self.running:
            return

        dataset_dir = Path(self.dataset_var.get().strip()).expanduser()
        if not dataset_dir.exists() or not dataset_dir.is_dir():
            messagebox.showerror("Invalid folder", f"Dataset folder does not exist:\n{dataset_dir}")
            return

        try:
            criteria = parse_criteria(self.criteria_var.get())
        except Exception as exc:
            messagebox.showerror("Invalid criteria", str(exc))
            return

        if self.use_conda_var.get():
            if shutil.which("conda") is None:
                messagebox.showerror("Conda not found", "conda is not available in PATH.")
                return
            env_name = self.conda_env_var.get().strip()
            if not env_name:
                messagebox.showerror("Invalid env", "Please provide a conda env name.")
                return
        else:
            env_name = ""

        self.running = True
        self.run_btn.configure(state="disabled")
        self.thread_log("")
        self.thread_log(f"Dataset: {dataset_dir}")
        self.thread_log(f"Criteria: {criteria}")
        worker = threading.Thread(
            target=self.run_pipeline,
            args=(dataset_dir, criteria, env_name, self.use_conda_var.get()),
            daemon=True,
        )
        worker.start()

    def build_py_cmd(self, script: Path, use_conda: bool, env_name: str) -> list[str]:
        if use_conda:
            return ["conda", "run", "-n", env_name, "python", str(script)]
        return [sys.executable, str(script)]

    def run_pipeline(self, dataset_dir: Path, criteria: list[float], env_name: str, use_conda: bool) -> None:
        try:
            if not S1_SCRIPT.exists() or not S2_SCRIPT.exists():
                raise RuntimeError("S1/S2 scripts are missing in this folder.")

            edf_files = find_fixation_edfs(dataset_dir)
            if not edf_files:
                raise RuntimeError(f"No fixation_dots EDF files found in {dataset_dir}.")

            self.thread_log(f"Found {len(edf_files)} fixation_dots EDF file(s):")
            for p in edf_files:
                self.thread_log(f"  - {p.name}")

            tsv_files: list[Path] = []
            for idx, edf in enumerate(edf_files, start=1):
                self.thread_log("")
                self.thread_log(f"[S1 {idx}/{len(edf_files)}] {edf.name}")
                s1_cmd = self.build_py_cmd(S1_SCRIPT, use_conda, env_name) + ["--edf", str(edf)]
                self.run_command_stream(s1_cmd)

                tsv_path = edf.with_suffix(".tsv.gz")
                if not tsv_path.exists():
                    raise RuntimeError(f"S1 completed but TSV not found: {tsv_path}")
                tsv_files.append(tsv_path)

            total_s2 = len(tsv_files) * len(criteria)
            done = 0
            for tsv in tsv_files:
                for crit in criteria:
                    done += 1
                    self.thread_log("")
                    self.thread_log(f"[S2 {done}/{total_s2}] {tsv.name} | criteria={crit}")
                    s2_cmd = self.build_py_cmd(S2_SCRIPT, use_conda, env_name) + [
                        "--input",
                        str(tsv),
                        "--criteria-ratio",
                        str(crit),
                        "--no-gui-picker",
                    ]
                    self.run_command_stream(s2_cmd)

            self.thread_log("")
            self.thread_log("All jobs completed successfully.")
            self.after(0, messagebox.showinfo, "Done", "S1 + S2 batch run completed.")
        except Exception as exc:
            self.thread_log("")
            self.thread_log(f"ERROR: {exc}")
            self.after(0, messagebox.showerror, "Failed", str(exc))
        finally:
            self.running = False
            self.after(0, self.run_btn.configure, {"state": "normal"})

    def run_command_stream(self, cmd: list[str]) -> None:
        pretty = " ".join(shlex.quote(x) for x in cmd)
        self.thread_log(f"$ {pretty}")

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            self.thread_log(line.rstrip("\n"))

        code = proc.wait()
        if code != 0:
            raise RuntimeError(f"Command failed with exit code {code}: {pretty}")


def main() -> int:
    app = BatchApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

