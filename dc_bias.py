"""Engineering module — BJT Common-Emitter DC Bias (Voltage-Divider Bias).

Python ล้วน ไม่รู้จัก HTML/HTTP — Flask (app.py) เรียกใช้โมดูลนี้

แบบจำลอง: Forward-Active Approximation (β และ VBE คงที่)
อินพุตตัวต้านทานเป็น kΩ (แปลงเป็น Ω ภายในก่อนคำนวณ)

สมการ:
    VTH = VCC × R2 / (R1 + R2)
    RTH = R1×R2 / (R1 + R2)
    IB  = (VTH − VBE) / (RTH + (β+1)×RE)
    IC  = β × IB
    IE  = (β+1) × IB
    VE  = IE × RE
    VB  = VE + VBE
    VC  = VCC − IC × RC
    VCE = VC − VE
"""

SAT_VCE_LIMIT = 0.2  # V — ต่ำกว่าค่านี้ถือว่าเข้าสู่ Saturation


class BiasError(ValueError):
    """ข้อผิดพลาดของข้อมูลอินพุต — ข้อความไทย แสดงต่อผู้ใช้ได้โดยตรง"""


def parse_field(raw: str | None, name: str) -> float:
    """แปลงค่าจากฟอร์ม (string) เป็น float

    raise BiasError ถ้าว่าง หรือไม่ใช่ตัวเลข
    """
    if raw is None or str(raw).strip() == "":
        raise BiasError(f"กรุณากรอกค่า {name}")
    text = str(raw).strip()
    try:
        return float(text)
    except ValueError:
        raise BiasError(f"{name} ต้องเป็นตัวเลข (ได้รับ: {text!r})")


def analyze(vcc: float, r1: float, r2: float, rc: float, re: float,
            beta: float, vbe: float) -> dict:
    """คำนวณ DC Operating Point ของวงจร NPN Common Emitter

    ตัวต้านทาน (r1, r2, rc, re) รับเป็น kΩ — แปลงเป็น Ω ภายใน

    คืน dict: vth [V], rth [Ω], ib/ic/ie [A], vb/ve/vc/vce [V],
             region [str], warnings [list[str]]
    """
    # ---- Validation ก่อนคำนวณ ----
    if vcc <= 0:
        raise BiasError("VCC ต้องมากกว่า 0 (หน่วย V)")
    if beta <= 0:
        raise BiasError("β ต้องมากกว่า 0")
    if vbe < 0:
        raise BiasError("VBE ต้องไม่ติดลบ (หน่วย V)")
    for label, value in (("R1", r1), ("R2", r2), ("RC", rc), ("RE", re)):
        if value <= 0:
            raise BiasError(f"{label} ต้องมากกว่า 0 (หน่วย kΩ)")

    # ---- แปลงหน่วย kΩ → Ω ----
    r1_o = r1 * 1e3
    r2_o = r2 * 1e3
    rc_o = rc * 1e3
    re_o = re * 1e3

    # ---- Thevenin ของวงจรแบ่งแรงดัน ----
    vth = vcc * r2_o / (r1_o + r2_o)
    rth = r1_o * r2_o / (r1_o + r2_o)

    warnings: list[str] = []

    if vth <= vbe:
        # Cutoff: ไม่มีกระแสฐานไหล อิเล็กโทรดทั้งคู่ไม่มี drop
        region = "Cutoff"
        warnings.append(
            "VTH ≤ VBE — ทรานซิสเตอร์ไม่นำกระแส (Cutoff) "
            "แบบจำลอง Forward-Active ใช้ไม่ได้"
        )
        ib = ic = ie = 0.0
        ve = 0.0
        vb = vth          # base ลอยตามวงจรแบ่งแรงดันแบบไม่มีโหลด
        vc = vcc          # ไม่มีกระแสผ่าน RC
        vce = vc - ve
    else:
        ib = (vth - vbe) / (rth + (beta + 1) * re_o)
        ic = beta * ib
        ie = (beta + 1) * ib
        ve = ie * re_o
        vb = ve + vbe
        vc = vcc - ic * rc_o
        vce = vc - ve
        if vce < SAT_VCE_LIMIT or vc <= ve:
            region = "Saturation"
            warnings.append(
                "VCE ต่ำ — ทรานซิสเตอร์เข้าสู่ Saturation "
                "แบบจำลอง Forward-Active ใช้ไม่ได้"
            )
        else:
            region = "Forward-Active"

    return {
        "vth": vth,
        "rth": rth,
        "ib": ib,
        "ic": ic,
        "ie": ie,
        "vb": vb,
        "ve": ve,
        "vc": vc,
        "vce": vce,
        "region": region,
        "warnings": warnings,
    }
