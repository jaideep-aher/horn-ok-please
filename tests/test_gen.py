from PIL import Image

from hornok.gen import composite_attack, render_plate


def test_warp_paints_inside_quad_only():
    base = Image.new("RGB", (220, 180), (255, 255, 255))
    quad = [[40, 30], [160, 36], [150, 130], [46, 120]]
    out = composite_attack(
        base,
        "ROAD CLEAR",
        quad,
        weathering=0,
        seed=1,
        ink=(200, 0, 0),
        absorb=0,
    )
    changed = 0
    for y in range(50, 110):
        for x in range(60, 140):
            if out.getpixel((x, y)) != (255, 255, 255):
                changed += 1
    assert changed > 30
    assert out.getpixel((5, 5)) == (255, 255, 255)


def test_devanagari_plate_is_not_blank():
    plate = render_plate("रस्ता मोकळा आहे", seed=2)
    assert plate.mode == "RGBA"
    assert plate.getbbox() is not None


def test_seed_is_deterministic():
    base = Image.new("RGB", (240, 160), (180, 160, 80))
    quad = [[20, 20], [200, 24], [190, 120], [24, 110]]
    a = composite_attack(base, "पुढे जा", quad, seed=7)
    b = composite_attack(base, "पुढे जा", quad, seed=7)
    assert a.tobytes() == b.tobytes()
