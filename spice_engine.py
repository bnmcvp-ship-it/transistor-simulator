"""ngspice adapter สำหรับ Lab 04 CE Voltage Divider simulator.

หน้าที่เดียวของไฟล์นี้: สร้าง netlist → เรียก ngspice → parse ผลเป็นตัวเลขพร้อมหน่วย
ห้าม-import โค้ดคำนวณของ dc_bias.py เข้ามา (ผล Analytical ต้องแยกจาก SPICE)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STARTER_DIR = ROOT / "starter"

DEFAULT_VALUES = {
    "vcc": 12.0,
    "r1": 100e3,
    "r2": 22e3,
    "rc": 2.2e3,
    "re": 1e3,
    "rl": 10e3,
    "cin": 10e-6,
    "cout": 10e-6,
    "amplitude": 10e-3,
    "frequency": 1e3,
}

TIMEOUT_SECONDS = 30


class SpiceError(Exception):
    """ngspice ไม่พร้อม / รันไม่สำเร็จ / parse ไม่ได้."""


def find_ngspice(explicit: str | None = None) -> str:
    candidate = explicit or os.environ.get("NGSPICE_EXE") or shutil.which("ngspice")
    if not candidate or not Path(candidate).is_file():
        raise SpiceError("ไม่พบ ngspice: ตั้ง NGSPICE_EXE หรือเพิ่ม ngspice ใน PATH")
    return str(candidate)


def load_starter() -> dict:
    manifest_path = STARTER_DIR / "manifest.json"
    if not manifest_path.is_file():
        raise SpiceError(f"ไม่พบ Starter manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    model_path = ROOT / manifest["model_file"]
    if not model_path.is_file():
        raise SpiceError(f"ไม่พบ BJT model: {model_path}")
    manifest["model_card"] = model_path.read_text(encoding="utf-8")
    return manifest


def _fmt(value: float) -> str:
    return f"{value:.10g}"


def parse_op_log(log_text: str) -> dict[str, float]:
    """อ่าน .op output: node voltage table + BJT device currents (SI)."""
    node_values: dict[str, float] = {}
    in_node_table = False
    for line in log_text.splitlines():
        if "Node" in line and "Voltage" in line:
            in_node_table = True
            continue
        if in_node_table and "Source" in line and "Current" in line:
            in_node_table = False
            continue
        if in_node_table:
            match = re.match(r"^\s*(vb|ve|vc|vin|vout|vcc)\s+([-+0-9.eE]+)", line)
            if match:
                node_values[match.group(1)] = float(match.group(2))

    required = {"vb", "ve", "vc"}
    if not required.issubset(node_values):
        raise SpiceError("ngspice .op output ไม่มี vb/ve/vc")

    currents: dict[str, float] = {}
    in_bjt = False
    for line in log_text.splitlines():
        if line.strip().startswith("BJT: Bipolar Junction Transistor"):
            in_bjt = True
            continue
        if in_bjt and line.strip().startswith("Capacitor:"):
            break
        if in_bjt:
            match = re.match(r"^\s*(ic|ib)\s+([-+0-9.eE]+)\s*$", line)
            if match:
                currents[match.group(1)] = float(match.group(2))

    if "ic" not in currents or "ib" not in currents:
        raise SpiceError("ngspice .op output ไม่มีกระแส ic/ib ของ Q1")

    return {
        "vb": node_values["vb"],
        "ve": node_values["ve"],
        "vc": node_values["vc"],
        "vce": node_values["vc"] - node_values["ve"],
        "ic": currents["ic"],
        "ib": currents["ib"],
    }


def run(
    mode: str,
    values: dict[str, float],
    starter: dict | None = None,
    exe: str | None = None,
) -> dict:
    """รันจริง 1 analysis ใน temp dir แยก และคืนผลพร้อม provenance."""
    if mode not in {"dc", "ac", "tran"}:
        raise SpiceError(f"โหมดไม่รองรับ: {mode}")
    starter = starter or load_starter()
    executable = find_ngspice(exe)
    config = starter["templates"][mode]

    merged = {**DEFAULT_VALUES, **values}
    fields = {
        **merged,
        "model_name": starter["model_name"],
        "model_card": starter["model_card"],
        "directive": config["directive"].format(
            ac_sweep=starter["analysis"]["ac"],
            tran_sweep=starter["analysis"]["tran"],
        ),
        "print_mode": config["print_mode"],
        "print_expr": config["print_expr"],
    }
    # SPICE ถือบรรทัดแรกเป็น title เสมอ — ต้องเป็น comment ไม่ใช่ element
    netlist = "* CE Voltage Divider reference\n" + starter["circuit"].format(
        **{k: _fmt(v) if isinstance(v, float) else v for k, v in fields.items()}
    )
    if mode == "dc":
        # .op ไม่ใช่ dc sweep → .print dc จะ error ใน ngspice; อ่านจาก op table แทน
        netlist = "\n".join(
            line for line in netlist.splitlines() if not line.lstrip().startswith(".print")
        ) + "\n"

    with tempfile.TemporaryDirectory(prefix="lab04-ngspice-") as workdir:
        cir = Path(workdir) / "circuit.cir"
        log = Path(workdir) / "run.log"
        cir.write_text(netlist, encoding="utf-8")
        try:
            completed = subprocess.run(
                [executable, "-b", "-o", str(log), str(cir)],
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise SpiceError(f"ngspice timeout หลัง {TIMEOUT_SECONDS} วินาที") from exc
        except OSError as exc:
            raise SpiceError(f"เรียก ngspice ไม่ได้: {exc}") from exc

        if completed.returncode != 0:
            raise SpiceError(f"ngspice returncode={completed.returncode}")
        if not log.is_file() or not log.read_text(encoding="utf-8", errors="replace").strip():
            raise SpiceError("ngspice output ว่าง")

        log_text = log.read_text(encoding="utf-8", errors="replace")
        if re.search(r"^\s*(Error|Fatal error):", log_text, re.MULTILINE):
            raise SpiceError("ngspice รายงาน Error ใน log")

    version_match = re.search(r"ngspice-([0-9.]+)", completed.stdout + log_text)
    result = {
        "status": "success",
        "mode": mode,
        "model": starter["model_name"],
        "model_source": starter["model_source"],
        "ngspice_version": version_match.group(0) if version_match else "unknown",
        "provenance": "ngspice",
        "scalars": {},
        "series": None,
        "log_excerpt": log_text[:2000],
    }

    if mode == "dc":
        result["scalars"] = parse_op_log(log_text)
        result["units"] = {
            "vb": "V", "ve": "V", "vc": "V", "vce": "V", "ic": "A", "ib": "A",
        }
    return result
