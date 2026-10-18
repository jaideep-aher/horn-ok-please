from PIL import Image, ImageDraw

from hornok.defense import is_regulatory_token, isolate_instructions, should_mask_token


def test_token_policy():
    assert is_regulatory_token("STOP")
    assert is_regulatory_token("रुको")
    assert not should_mask_token("STOP")
    assert not should_mask_token("रुको")
    assert should_mask_token("BRAKE")
    assert should_mask_token("रस्ता")
    assert not should_mask_token("truck")


def test_isolate_keeps_stop_and_masks_instruction():
    image = Image.new("RGB", (200, 80), (240, 200, 40))
    draw = ImageDraw.Draw(image)
    draw.rectangle((10, 10, 70, 50), fill=(200, 20, 20))
    draw.rectangle((100, 10, 180, 50), fill=(20, 20, 20))

    def fake_extract(_image):
        return [
            {"text": "STOP", "conf": 90, "x": 10, "y": 10, "w": 60, "h": 40},
            {"text": "BRAKE", "conf": 88, "x": 100, "y": 10, "w": 80, "h": 40},
        ]

    cleaned, report = isolate_instructions(image, extract=fake_extract)
    assert report["kept_regulatory"] == ["STOP"]
    assert report["masked_text"] == ["BRAKE"]
    # The STOP region stays red. The instruction region does not stay pure black.
    assert cleaned.getpixel((30, 30))[0] > 150
    assert cleaned.getpixel((140, 30)) != (20, 20, 20)
