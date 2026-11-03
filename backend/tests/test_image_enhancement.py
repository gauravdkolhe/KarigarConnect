from pathlib import Path
from PIL import Image
import pytest

from backend.app.services.image_service import (
    ENHANCED_DIR,
    ORIGINALS_DIR,
    STYLE_CONFIGS,
    enhance_product_image,
)


@pytest.fixture
def sample_original_image():
    ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
    img_path = ORIGINALS_DIR / "test_craft_sample.jpg"

    # Create a test craft sample image (600x600 with grey workshop background and colored craft subject)
    img = Image.new("RGB", (600, 600), (180, 180, 180))  # Workshop grey table
    # Draw a craft object in center (e.g. wooden pottery brown (150, 75, 25))
    for x in range(150, 450):
        for y in range(120, 480):
            if (x - 300) ** 2 / 120**2 + (y - 300) ** 2 / 160**2 <= 1.0:
                img.putpixel((x, y), (160, 82, 45))

    img.save(img_path, format="JPEG", quality=90)
    yield img_path

    # Cleanup
    img_path.unlink(missing_ok=True)


def test_enhance_image_studio_white_background(sample_original_image):
    """Test standard studio white style produces white background and centered alignment."""
    res = enhance_product_image(sample_original_image, style="studio_white")

    assert res["style_applied"]["key"] == "studio_white"
    assert res["enhanced_dimensions"] == [1200, 1200]
    enhanced_file = Path(res["enhanced_path"])
    assert enhanced_file.is_file()

    # Verify background is pure white at outer border corners
    with Image.open(enhanced_file) as enhanced:
        assert enhanced.size == (1200, 1200)
        # Corner pixels should be white (255, 255, 255)
        top_left = enhanced.getpixel((10, 10))
        top_right = enhanced.getpixel((1190, 10))
        assert top_left == (255, 255, 255)
        assert top_right == (255, 255, 255)

    # Cleanup generated file
    enhanced_file.unlink(missing_ok=True)


def test_enhance_image_three_styles(sample_original_image):
    """Test all 3 user-selectable style presets: studio_white, warm_heritage, modern_minimalist."""
    styles = ["studio_white", "warm_heritage", "modern_minimalist"]

    for style_key in styles:
        res = enhance_product_image(sample_original_image, style=style_key)
        assert res["style_applied"]["key"] == style_key
        assert res["style_applied"]["name"] == STYLE_CONFIGS[style_key]["name"]

        enhanced_file = Path(res["enhanced_path"])
        assert enhanced_file.is_file()

        with Image.open(enhanced_file) as enhanced:
            assert enhanced.size == (1200, 1200)
            # Center of the craft should have enhanced vibrant pixels
            center_pixel = enhanced.getpixel((600, 600))
            # The wooden terracotta center pixel should have healthy non-zero RGB
            assert center_pixel[0] > 0
            assert center_pixel[1] > 0

        enhanced_file.unlink(missing_ok=True)

