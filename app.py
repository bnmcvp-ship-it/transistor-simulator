"""Flask application — BJT DC Bias Web App (ENG29 2121 Lab 02 → Lab 04).

HTTP routes รับ request แล้วเรียก engineering module
ตัว route ไม่ทำฟิสิกส์ — สมการอยู่ใน dc_bias.py ผลจำลองอยู่ใน spice_engine.py

Lab 03: เลือกได้ 3 โหมด divider / fixed / emitter ผ่านฟิลด์ `circuit`
Lab 04: analysis=spice ใช้ /simulate เรียก ngspice จริง แยกจาก /calculate เดิม
"""

import spice_engine
from flask import Flask, render_template, request

from dc_bias import BiasError, analyze, analyze_emitter, analyze_fixed, parse_field
from spice_engine import SpiceError, parse_spice_form

# โหมดที่รองรับ + ชื่อที่แสดง + รายชื่อฟิลด์ที่โหมดนั้นใช้จริง
CIRCUITS = {
    "divider": {
        "label": "Voltage-Divider Bias",
        "fields": ["vcc", "r1", "r2", "rc", "re", "beta", "vbe"],
    },
    "fixed": {
        "label": "Fixed Bias",
        "fields": ["vcc", "rb", "rc", "beta", "vbe"],
    },
    "emitter": {
        "label": "Emitter Bias",
        "fields": ["vcc", "rb", "rc", "re", "beta", "vbe"],
    },
}

# (ป้ายกำกับ, ค่าตัวอย่างสำหรับ placeholder) ของแต่ละฟิลด์
FIELD_DEFS = {
    "vcc": ("VCC — แหล่งจ่าย [V]", "12"),
    "r1": ("R1 — บนเบส [kΩ]", "100"),
    "r2": ("R2 — ล่างเบส [kΩ]", "22"),
    "rb": ("RB — ตัวต้านทานเบส [kΩ]", "1000"),
    "rc": ("RC — ตัวเก็บ [kΩ]", "2.2"),
    "re": ("RE — อิมิตเตอร์ [kΩ]", "1"),
    "beta": ("β — current gain", "100"),
    "vbe": ("VBE — แรงดันเบส-อิมิตเตอร์ [V]", "0.7"),
}


def _fields_for(mode: str) -> list[tuple[str, str, str]]:
    return [
        (name, FIELD_DEFS[name][0], FIELD_DEFS[name][1])
        for name in CIRCUITS[mode]["fields"]
    ]


# Lab 04 — ฟอร์ม SPICE (หน่วยที่ผู้ใช้กรอก → ตัวคูณเป็น SI ก่อนส่งเข้า netlist)
SPICE_FIELDS = {
    "vcc": ("VCC — แหล่งจ่าย [V]", "12", 1.0),
    "r1": ("R1 — บนเบส [kΩ]", "100", 1e3),
    "r2": ("R2 — ล่างเบส [kΩ]", "22", 1e3),
    "rc": ("RC — ตัวเก็บ [kΩ]", "2.2", 1e3),
    "re": ("RE — อิมิตเตอร์ [kΩ]", "1", 1e3),
    "rl": ("RL — โหลดที่ Vout [kΩ]", "10", 1e3),
    "cin": ("CIN — ตัวจับคู่เข้า [µF]", "10", 1e-6),
    "cout": ("COUT — ตัวจับคู่ออก [µF]", "10", 1e-6),
    "amplitude": ("Vin — แอมพลิจูด [V peak]", "0.01", 1.0),
    "frequency": ("Vin — ความถี่ [Hz]", "1000", 1.0),
}

ANALYSIS_MODES = {
    "dc": "DC Operating Point (.op)",
    "ac": "AC Bode (.ac)",
    "tran": "Transient (.tran)",
}


def _spice_fields() -> list[tuple[str, str, str]]:
    return [(name, label, placeholder) for name, (label, placeholder, _) in SPICE_FIELDS.items()]


def _cutoff_text(value) -> str:
    return f"{value:.4g}" if isinstance(value, (int, float)) else str(value)


def _spice_presentation(mode: str, result: dict) -> tuple[list, dict | None]:
    """แปลงผล ngspice เป็นตาราง + โครงสร้างกราฟ (ไม่แต่งตัวเลข)."""
    if mode == "dc":
        s = result["scalars"]
        rows = [
            ("VB — แรงดันเบส", f"{s['vb']:.3f}", "V"),
            ("VE — แรงดันอิมิตเตอร์", f"{s['ve']:.3f}", "V"),
            ("VC — แรงดันคอลเลกเตอร์", f"{s['vc']:.3f}", "V"),
            ("VCE — คอลเลกเตอร์-อิมิตเตอร์", f"{s['vce']:.3f}", "V"),
            ("IC — กระแสคอลเลกเตอร์", f"{s['ic'] * 1e3:.3f}", "mA"),
            ("IB — กระแสเบส", f"{s['ib'] * 1e6:.2f}", "µA"),
        ]
        return rows, None

    series = result["series"]
    x = series["x"]
    if mode == "ac":
        peak = max(range(len(series["y"])), key=lambda i: series["y"][i])
        rows = [
            ("Gain สูงสุด", f"{series['y'][peak]:.2f}", "dB"),
            ("f_L (−3 dB)", _cutoff_text(series["cutoff_low"]), "Hz"),
            ("f_H (−3 dB)", _cutoff_text(series["cutoff_high"]), "Hz"),
            ("Phase ที่ gain สูงสุด", f"{series['series']['phase'][peak]:.2f}", "°"),
        ]
        plot = {
            "x": x,
            "series": [{"name": "Gain (dB)", "y": series["y"]}],
            "x_label": "Frequency (Hz)",
            "y_label": "Gain (dB)",
            "phase": {
                "x": x,
                "series": [{"name": "Phase (°)", "y": series["series"]["phase"]}],
                "x_label": "Frequency (Hz)",
                "y_label": "Phase (°)",
            },
        }
        return rows, plot

    vin = series["series"]["vin"]
    vout = series["series"]["vout"]
    rows = [
        ("Vin peak", f"{max(abs(v) for v in vin):.4f}", "V"),
        ("Vout peak", f"{max(abs(v) for v in vout):.4f}", "V"),
    ]
    plot = {
        "x": x,
        "series": [
            {"name": "Vin (V)", "y": vin},
            {"name": "Vout (V)", "y": vout},
        ],
        "x_label": "Time (s)",
        "y_label": "Voltage (V)",
    }
    return rows, plot


def create_app() -> Flask:
    """App factory — ให้ tests เรียก test_client() ได้โดยไม่แตะ global state"""
    app = Flask(__name__)

    def render(mode="divider", form=None, rows=None, region=None, warnings=None, error=None,
               analysis="analytical", spice_form=None, spice_result=None,
               plot=None, engine_status=None, spice_mode="dc"):
        """render เดียวสำหรับทุก route — ผล/error แนบชื่อโหมดเสมอ"""
        if mode not in CIRCUITS:
            mode = "divider"
        return render_template(
            "index.html",
            circuits=[(key, cfg["label"]) for key, cfg in CIRCUITS.items()],
            circuit=mode,
            circuit_label=CIRCUITS[mode]["label"],
            fields=_fields_for(mode),
            form=form or {},
            rows=rows,
            region=region,
            warnings=warnings,
            error=error,
            analysis=analysis,
            spice_fields=_spice_fields(),
            spice_form=spice_form or {},
            spice_modes=ANALYSIS_MODES,
            spice_mode=spice_mode,
            spice_result=spice_result,
            plot=plot,
            engine_status=engine_status,
        )

    @app.route("/")
    def index():
        # GET /?analysis=spice|analytical + ?circuit=fixed|emitter — ไม่ใช้ JavaScript
        analysis = request.args.get("analysis", "analytical")
        error = None
        if analysis not in {"analytical", "spice"}:
            error = f"analysis ไม่ถูกต้อง: {analysis}"
            analysis = "analytical"
        mode = request.args.get("circuit", "divider")
        if mode not in CIRCUITS:
            error = error or f"โหมดวงจรไม่ถูกต้อง: {mode}"
        return render(mode=mode, analysis=analysis, error=error)

    @app.route("/calculate", methods=["POST"])
    def calculate():
        mode = request.form.get("circuit", "divider")
        if mode not in CIRCUITS:
            # ตรวจโหมดก่อนอ่านfield — ห้ามแอบไปคำนวณแบบ Divider
            return render(mode="divider", error=f"โหมดวงจรไม่ถูกต้อง: {mode}")

        fields = _fields_for(mode)
        form = {name: request.form.get(name, "") for name, _, _ in fields}

        try:
            values = {
                name: parse_field(request.form.get(name), label.split(" ")[0])
                for name, label, _ in fields
            }
            if mode == "divider":
                result = analyze(
                    vcc=values["vcc"], r1=values["r1"], r2=values["r2"],
                    rc=values["rc"], re=values["re"],
                    beta=values["beta"], vbe=values["vbe"],
                )
            elif mode == "fixed":
                result = analyze_fixed(
                    vcc=values["vcc"], rb=values["rb"], rc=values["rc"],
                    beta=values["beta"], vbe=values["vbe"],
                )
            else:  # emitter
                result = analyze_emitter(
                    vcc=values["vcc"], rb=values["rb"], rc=values["rc"],
                    re=values["re"], beta=values["beta"], vbe=values["vbe"],
                )
        except BiasError as exc:
            # หน้าไม่ล้ม (HTTP 200) และไม่ส่ง rows → ไม่โชว์ผลรอบก่อน
            return render(mode=mode, form=form, error=str(exc))

        # แปลงหน่วยสำหรับแสดงผล (SI → หน่วยที่อ่านง่าย)
        rows = [
            ("VB — แรงดันเบส", f"{result['vb']:.2f}", "V"),
            ("VE — แรงดันอิมิตเตอร์", f"{result['ve']:.2f}", "V"),
            ("VC — แรงดันคอลเลกเตอร์", f"{result['vc']:.2f}", "V"),
            ("VCE — คอลเลกเตอร์-อิมิตเตอร์", f"{result['vce']:.2f}", "V"),
            ("IC — กระแสคอลเลกเตอร์", f"{result['ic'] * 1e3:.2f}", "mA"),
            ("IB — กระแสเบส", f"{result['ib'] * 1e6:.2f}", "µA"),
            ("IE — กระแสอิมิตเตอร์", f"{result['ie'] * 1e3:.2f}", "mA"),
        ]
        return render(
            mode=mode, form=form, rows=rows,
            region=result["region"], warnings=result["warnings"],
        )

    @app.route("/simulate", methods=["POST"])
    def simulate():
        """Lab 04 — แปลงฟอร์ม→SI→validate→รัน ngspice; error ต้องไม่เหลือผลเก่า."""
        spice_mode = request.form.get("spice_mode", "dc")
        form = {name: request.form.get(name, "") for name in SPICE_FIELDS}

        if spice_mode not in ANALYSIS_MODES:
            return render(
                analysis="spice", spice_form=form,
                error=f"โหมด analysis ไม่ถูกต้อง: {spice_mode}",
                engine_status="error",
            )

        try:
            raw = {
                name: parse_spice_form(form[name], label.split(" ")[0])
                for name, (label, _, _) in SPICE_FIELDS.items()
            }
            values = {
                name: number * SPICE_FIELDS[name][2]
                for name, number in raw.items()
            }
            result = spice_engine.run(spice_mode, values)
            rows, plot = _spice_presentation(spice_mode, result)
        except (SpiceError, BiasError) as exc:
            return render(
                analysis="spice", spice_form=form, spice_mode=spice_mode,
                error=str(exc), engine_status="error",
            )

        return render(
            analysis="spice", spice_form=form, spice_mode=spice_mode,
            spice_result=result, rows=rows, plot=plot,
            engine_status="success",
        )

    return app


# ใช้รันด้วย: py -m flask --app app run --debug
app = create_app()
