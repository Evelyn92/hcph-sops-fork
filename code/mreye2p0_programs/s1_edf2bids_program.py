#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict
from copy import deepcopy
from itertools import groupby, product
from pathlib import Path
from typing import Any
from warnings import warn

import numpy as np
import pandas as pd
from pyedfread import read_edf


SCRIPT_DIR = Path(__file__).resolve().parent
LEGACY_DIR = SCRIPT_DIR.parent / "mreye2p0_fixed"
if str(LEGACY_DIR) not in sys.path:
    sys.path.insert(0, str(LEGACY_DIR))

from write_bids_yiwei import write_bids_from_df  # noqa: E402


DEFAULT_EYE = "right"
DEFAULT_FREQUENCY = 1000
DEFAULT_MODE = "P-CR"
DEFAULT_SCREEN = (0, 800, 0, 600)

EYE_CODE_MAP = defaultdict(lambda: "unknown", {"R": "right", "L": "left", "RL": "both"})
EDF2BIDS_COLUMNS = {
    "g": "",
    "p": "pupil",
    "h": "href",
    "r": "raw",
    "fg": "fast",
    "fh": "fast_href",
    "fr": "fast_raw",
}

BIDS_COLUMNS_ORDER = (
    [f"eye{num}_{c}_coordinate" for num, c in product((1, 2), ("x", "y"))]
    + [f"eye{num}_pupil_size" for num in (1, 2)]
    + [f"eye{num}_pupil_{c}_coordinate" for num, c in product((1, 2), ("x", "y"))]
    + [f"eye{num}_fixation" for num in (1, 2)]
    + [f"eye{num}_saccade" for num in (1, 2)]
    + [f"eye{num}_blink" for num in (1, 2)]
    + [f"eye{num}_href_{c}_coordinate" for num, c in product((1, 2), ("x", "y"))]
    + [f"eye{num}_{c}_velocity" for num, c in product((1, 2), ("x", "y"))]
    + [f"eye{num}_href_{c}_velocity" for num, c in product((1, 2), ("x", "y"))]
    + [f"eye{num}_raw_{c}_velocity" for num, c in product((1, 2), ("x", "y"))]
    + [f"fast_{c}_velocity" for c in ("x", "y")]
    + [f"fast_{kind}_{c}_velocity" for kind, c in product(("href", "raw"), ("x", "y"))]
    + [f"screen_ppdeg_{c}_coordinate" for c in ("x", "y")]
    + ["timestamp"]
)


def choose_file_interactive(use_gui_picker: bool = False) -> Path:
    entered = input("Enter full path to EDF file: ").strip()
    if entered:
        return Path(entered)

    if not use_gui_picker:
        raise RuntimeError("No EDF file provided. Re-run with --edf, paste a path, or use --gui-picker.")

    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        selected = filedialog.askopenfilename(
            title="Select an EDF file",
            filetypes=[("EDF files", "*.EDF *.edf"), ("All files", "*.*")],
        )
        root.destroy()
        if selected:
            return Path(selected)
    except Exception:
        pass

    raise RuntimeError("GUI picker failed. Re-run with --edf or paste a path at the prompt.")


def to_builtin(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: to_builtin(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_builtin(v) for v in value]
    if isinstance(value, tuple):
        return tuple(to_builtin(v) for v in value)
    if isinstance(value, np.generic):
        return value.item()
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert one EDF file to BIDS eyetracking TSV/JSON.")
    parser.add_argument("--edf", type=Path, help="Path to input EDF file.")
    parser.add_argument("--out-dir", type=Path, help="Output folder (default: EDF folder).")
    parser.add_argument("--start-message", default="RECCFG CR 1000 2 0 R")
    parser.add_argument("--stop-message", default="ET: eye-tracker stopped")
    parser.add_argument("--gui-picker", action="store_true", help="Use macOS/GUI file picker as fallback if no path is pasted.")
    args = parser.parse_args()

    edf_path = args.edf if args.edf else choose_file_interactive(use_gui_picker=args.gui_picker)
    edf_path = edf_path.expanduser().resolve()
    if not edf_path.exists():
        raise FileNotFoundError(f"EDF not found: {edf_path}")

    print(f"Selected: {edf_path}")
    data_path = edf_path.parent
    out_dir = args.out_dir.expanduser().resolve() if args.out_dir else data_path
    out_dir.mkdir(parents=True, exist_ok=True)

    ori_recording, events, ori_messages = read_edf(str(edf_path))

    ori_messages = ori_messages.rename(
        columns={
            "message": "trialid",
            "trial": "trial",
            "time": "timestamp",
        }
    )

    messages = ori_messages.rename(columns={c: c.strip() for c in ori_messages.columns.values}).drop_duplicates()

    _cal_hdr = messages.trialid.str.startswith("!CAL")
    calibration = messages[_cal_hdr]
    messages = messages.drop(messages.index[_cal_hdr])

    metadata: dict[str, Any] = {"StopTime": None, "StartTime": None}
    start_rows = messages.trialid.str.contains(args.start_message, case=False, regex=True)
    stop_rows = messages.trialid.str.contains(args.stop_message, case=False, regex=True)

    metadata["StartTime"] = int(messages[start_rows].timestamp.values[-1]) if start_rows.any() else None
    metadata["StopTime"] = int(messages[stop_rows].timestamp.values[0]) if stop_rows.any() else None
    messages = messages.loc[~start_rows & ~stop_rows, :]

    mode_record = messages.trialid.str.startswith("!MODE RECORD")
    meta_record = {"freq": DEFAULT_FREQUENCY, "mode": DEFAULT_MODE, "eye": DEFAULT_EYE}
    if mode_record.any():
        try:
            meta_record = re.match(
                r"\!MODE RECORD (?P<mode>\w+) (?P<freq>\d+) \d \d (?P<eye>[RL]+)",
                messages[mode_record].trialid.iloc[-1].strip(),
            ).groupdict()
            meta_record["eye"] = EYE_CODE_MAP[meta_record["eye"]]
            meta_record["mode"] = "P-CR" if meta_record["mode"] == "CR" else meta_record["mode"]
        except AttributeError:
            warn("Error extracting !MODE RECORD; using default frequency/mode/eye")
        finally:
            messages = messages.loc[~mode_record]

    eye = (("right", "left") if meta_record["eye"] == "both" else (meta_record["eye"],))
    metadata["SamplingFrequency"] = int(meta_record["freq"])
    metadata["EyeTrackingMethod"] = meta_record["mode"]
    metadata["RecordedEye"] = meta_record["eye"]

    gaze_msg = messages.trialid.str.startswith("GAZE_COORDS")
    metadata["ScreenAOIDefinition"] = ["square", DEFAULT_SCREEN]
    if gaze_msg.any():
        try:
            gaze_record = re.match(
                r"GAZE_COORDS (\d+\.\d+) (\d+\.\d+) (\d+\.\d+) (\d+\.\d+)",
                messages[gaze_msg].trialid.iloc[-1].strip(),
            ).groups()
            metadata["ScreenAOIDefinition"][1] = [
                int(round(float(gaze_record[0]))),
                int(round(float(gaze_record[2]))),
                int(round(float(gaze_record[1]))),
                int(round(float(gaze_record[3]))),
            ]
        except AttributeError:
            warn("Error extracting GAZE_COORDS")
        finally:
            messages = messages.loc[~gaze_msg]

    pupilfit_msg = messages.trialid.str.startswith("ELCL_PROC")
    if pupilfit_msg.any():
        try:
            pupilfit_method = [
                val for val in messages[pupilfit_msg].trialid.iloc[-1].strip().split(" ")[1:] if val
            ]
            metadata["PupilFitMethod"] = pupilfit_method[0].lower()
            metadata["PupilFitMethodNumberOfParameters"] = int(pupilfit_method[1].strip("(").strip(")"))
        except AttributeError:
            warn("Error extracting ELCL_PROC")
        finally:
            messages = messages.loc[~pupilfit_msg]

    pupilfit_msg_params = messages.trialid.str.startswith("ELCL_EFIT_PARAMS")
    if pupilfit_msg_params.any():
        rows = messages[pupilfit_msg_params]
        row = rows.trialid.values[-1].strip().split(" ")[1:]
        try:
            metadata["PupilFitParameters"] = [
                tuple(float(val) for val in vals) for k, vals in groupby(row, key=bool) if k
            ]
        except AttributeError:
            warn("Error extracting ELCL_EFIT_PARAMS")
        finally:
            messages = messages.loc[~pupilfit_msg_params]

    validation_msg = messages.trialid.str.startswith("VALIDATE")
    if validation_msg.any():
        metadata["ValidationPosition"] = []
        metadata["ValidationErrors"] = []

    for validate_row in messages[validation_msg].trialid.values:
        prefix, suffix = validate_row.split("OFFSET")
        validation_eye = f"eye{eye.index('right') + 1}" if "RIGHT" in prefix else f"eye{eye.index('left') + 1}"
        validation_coords = [int(val.strip()) for val in prefix.rsplit("at", 1)[-1].split(",") if val.strip()]
        metadata["ValidationPosition"].append([validation_eye, validation_coords])
        validate_values = [
            float(val)
            for val in re.match(
                r"(-?\d+\.\d+) deg\.\s+(-?\d+\.\d+),(-?\d+\.\d+) pix\.",
                suffix.strip(),
            ).groups()
        ]
        metadata["ValidationErrors"].append(
            (validation_eye, validate_values[0], tuple(validate_values[1:]))
        )
    messages = messages.loc[~validation_msg]

    thresholds_msg = messages.trialid.str.startswith("THRESHOLDS")
    if thresholds_msg.any():
        metadata["PupilThreshold"] = [None] * len(eye)
        metadata["CornealReflectionThreshold"] = [None] * len(eye)
        thresholds_chunks = messages[thresholds_msg].trialid.iloc[-1].strip().split(" ")[1:]
        eye_index = eye.index(EYE_CODE_MAP[thresholds_chunks[0]])
        metadata["PupilThreshold"][eye_index] = int(thresholds_chunks[-2])
        metadata["CornealReflectionThreshold"][eye_index] = int(thresholds_chunks[-1])
    messages = messages.loc[~thresholds_msg]

    if not messages.empty:
        metadata["LoggedMessages"] = [
            (int(msg_timestamp), msg.strip())
            for msg_timestamp, msg in messages[["timestamp", "trialid"]].values
        ]

    recording = ori_recording.astype({"time": int})
    recording = recording[recording["time"] > 0]
    raw_recording_len = len(recording)

    recording = recording.rename(columns={"rx": "screen_ppdeg_x_coordinate", "ry": "screen_ppdeg_y_coordinate", "time": "timestamp"})

    for column in ("flags", "input", "htype"):
        if column in recording.columns:
            recording = recording.drop(columns=[column])

    recording = recording.loc[:, (recording.abs() > 1e-8).any(axis=0)]
    recording = recording.loc[:, (recording.abs() < 1e8).any(axis=0)]
    recording = recording.replace({1e8: np.nan})

    remove_eye = set(("left", "right")) - set(eye)
    if remove_eye:
        remove_eye_name = remove_eye.pop()
        recording = recording.reindex(columns=[c for c in recording.columns if remove_eye_name not in c])

    screen_resolution = [800, 600]
    for eyenum, eyename in enumerate(eye):
        recording.loc[recording[f"pa_{eyename}"] < 1, f"pa_{eyename}"] = np.nan
        recording = recording.rename(columns={f"pa_{eyename}": f"eye{eyenum + 1}_pupil_size"})

        recording.loc[
            (recording[f"gx_{eyename}"] < 0) | (recording[f"gx_{eyename}"] > screen_resolution[0]),
            f"gx_{eyename}",
        ] = np.nan
        recording.loc[
            (recording[f"gy_{eyename}"] <= 0) | (recording[f"gy_{eyename}"] > screen_resolution[1]),
            f"gy_{eyename}",
        ] = np.nan

    columns = list(
        set(recording.columns)
        - {
            "timestamp",
            "screen_ppdeg_x_coordinate",
            "screen_ppdeg_y_coordinate",
            "eye1_pupil_size",
            "eye2_pupil_size",
        }
    )

    bids_columns: list[str] = []
    for eyenum, eyename in enumerate(eye):
        for name in columns:
            colprefix = f"eye{eyenum + 1}" if name.endswith(f"_{eyename}") else ""
            new_name = name.split("_")[0]
            new_name = re.sub(r"([xy])$", r"_\1_coordinate", new_name)
            new_name = re.sub(r"([xy])vel$", r"_\1_velocity", new_name)
            parts = new_name.split("_", 1)
            parts[0] = EDF2BIDS_COLUMNS[parts[0]]
            parts.insert(0, colprefix)
            bids_columns.append("_".join(piece for piece in parts if piece))

    recording = recording.rename(columns=dict(zip(columns, bids_columns)))

    ordered_columns = sorted(
        set(recording.columns.values).intersection(BIDS_COLUMNS_ORDER),
        key=lambda entry: BIDS_COLUMNS_ORDER.index(entry),
    )
    ordered_columns += [c for c in recording.columns.values if c not in ordered_columns]
    recording = recording.reindex(columns=ordered_columns)

    if len(recording) != raw_recording_len:
        raise RuntimeError("Unexpected recording length change during preprocessing.")

    metadata["CalibrationCount"] = 0
    if not calibration.empty:
        calibration = calibration.copy()
        calibration.trialid = calibration.trialid.str.replace("!CAL", "")
        calibration.trialid = calibration.trialid.str.strip()
        metadata["CalibrationLog"] = list(
            zip(calibration.timestamp.values.astype(int), calibration.trialid.values)
        )
        calibrations_msg = calibration.trialid.str.startswith("VALIDATION") & calibration.trialid.str.contains("ERROR")
        metadata["CalibrationCount"] = int(calibrations_msg.sum())

    recording["eye1_fixation"] = 0
    recording["eye1_saccade"] = 0
    recording["eye1_blink"] = 0

    for _, fixation_event in events[events["type"] == "fixation"].iterrows():
        recording.loc[
            (recording["timestamp"] >= fixation_event["start"])
            & (recording["timestamp"] <= fixation_event["end"]),
            "eye1_fixation",
        ] = 1

    blink_key = "contains_blink" if "contains_blink" in events.columns else "blink"
    for _, saccade_event in events[events["type"] == "saccade"].iterrows():
        recording.loc[
            (recording["timestamp"] >= saccade_event["start"])
            & (recording["timestamp"] <= saccade_event["end"]),
            "eye1_saccade",
        ] = 1
        if int(saccade_event[blink_key]) == 1:
            recording.loc[
                (recording["timestamp"] >= saccade_event["start"])
                & (recording["timestamp"] <= saccade_event["end"]),
                "eye1_blink",
            ] = 1

    metadata["Columns"] = recording.columns.tolist()
    metadata = to_builtin(deepcopy(metadata))

    filename = os.path.splitext(edf_path.name)[0]
    out_tsv, out_json = write_bids_from_df(recording, metadata, out_dir, filename)
    print(f"Saved TSV: {out_tsv}")
    print(f"Saved JSON: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
