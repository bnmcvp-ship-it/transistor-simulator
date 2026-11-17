"""Flask application — BJT DC Bias Web App (ENG29 2121 Lab 02 → Lab 03).

HTTP routes รับ request แล้วเรียก engineering module (dc_bias.py)
ตัว route ไม่ทำฟิสิกส์ — สมการอยู่ใน dc_bias.py เท่านั้น

Lab 03: เลือกได้ 3 โหมด divider / fixed / emitter ผ่านฟิลด์ `circuit`
"""

from flask import Flask, render_template, request

from dc_bias import BiasError, analyze, analyze_emitter, analyze_fixed, parse_field

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


def create_app() -> Flask:
    """App factory — ให้ tests เรียก test_client() ได้โดยไม่แตะ global state"""
    app = Flask(__name__)

    def render(mode, form=None, rows=None, region=None, warnings=None, error=None):
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
        )

    @app.route("/")
    def index():
        # GET /?circuit=fixed|emitter โหลดฟอร์มใหม่ตามโหมด ไม่ต้องใช้ JavaScript
        mode = request.args.get("circuit", "divider")
        error = None
        if mode not in CIRCUITS:
            error = f"โหมดวงจรไม่ถูกต้อง: {mode}"
        return render(mode=mode, error=error)

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

    return app


# ใช้รันด้วย: py -m flask --app app run --debug
app = create_app()
