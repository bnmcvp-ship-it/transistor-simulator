"""Flask application — BJT DC Bias Web App (ENG29 2121 Lab 02).

HTTP routes รับ request แล้วเรียก engineering module (dc_bias.py)
ตัว route ไม่ทำฟิสิกส์ — สมการอยู่ใน dc_bias.py เท่านั้น
"""

from flask import Flask, render_template, request

from dc_bias import BiasError, analyze, parse_field

# (ชื่อฟิลด์ในฟอร์ม, ป้ายกำกับ, ค่าตัวอย่างสำหรับ placeholder)
FIELDS = [
    ("vcc", "VCC — แหล่งจ่าย [V]", "12"),
    ("r1", "R1 — บนเบส [kΩ]", "100"),
    ("r2", "R2 — ล่างเบส [kΩ]", "22"),
    ("rc", "RC — ตัวเก็บ [kΩ]", "2.2"),
    ("re", "RE — อิมิตเตอร์ [kΩ]", "1"),
    ("beta", "β — current gain", "100"),
    ("vbe", "VBE — แรงดันเบส-อิมิตเตอร์ [V]", "0.7"),
]


def create_app() -> Flask:
    """App factory — ให้ tests เรียก test_client() ได้โดยไม่แตะ global state"""
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template(
            "index.html",
            fields=FIELDS,
            form={},
            rows=None,
            region=None,
            warnings=None,
            error=None,
        )

    @app.route("/calculate", methods=["POST"])
    def calculate():
        form = {field: request.form.get(field, "") for field, _, _ in FIELDS}
        try:
            values = {
                field: parse_field(request.form.get(field), label.split(" ")[0])
                for field, label, _ in FIELDS
            }
            result = analyze(
                vcc=values["vcc"],
                r1=values["r1"],
                r2=values["r2"],
                rc=values["rc"],
                re=values["re"],
                beta=values["beta"],
                vbe=values["vbe"],
            )
        except BiasError as exc:
            # A4: แสดง error ในหน้าเดิม หน้าเว็บไม่ล้ม (HTTP 200)
            return render_template(
                "index.html",
                fields=FIELDS,
                form=form,
                rows=None,
                region=None,
                warnings=None,
                error=str(exc),
            )

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
        return render_template(
            "index.html",
            fields=FIELDS,
            form=form,
            rows=rows,
            region=result["region"],
            warnings=result["warnings"],
            error=None,
        )

    return app


# ใช้รันด้วย: py -m flask --app app run --debug
app = create_app()
