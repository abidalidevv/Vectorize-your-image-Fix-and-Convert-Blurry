"""
VectorForge AI — Synthetic Test Image Generator
Creates test images programmatically (no copyrighted content).
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

SAMPLES_DIR = Path(__file__).parent.parent.parent / "samples"


def create_test_logo(path: Path):
    """Create a simple flat-color logo image."""
    w, h = 400, 300
    img = Image.new("RGB", (w, h), "#ffffff")
    draw = ImageDraw.Draw(img)

    # Background rectangle
    draw.rectangle([0, 0, w, h], fill="#f0f4ff")

    # Colored shapes
    draw.rectangle([50, 50, 200, 150], fill="#5b6ef7", outline="#2a3070", width=3)
    draw.ellipse([220, 40, 360, 160], fill="#34d399", outline="#1a7a5a", width=3)
    draw.polygon([(100, 200), (200, 250), (50, 270)], fill="#fbbf24", outline="#9a7000", width=2)
    draw.line([(0, 200), (400, 200)], fill="#2c2f3a", width=4)

    img.save(str(path))
    print(f"Created: {path}")


def create_test_bw(path: Path):
    """Create a B&W drawing."""
    w, h = 300, 300
    img = Image.new("RGB", (w, h), "#ffffff")
    draw = ImageDraw.Draw(img)

    draw.ellipse([20, 20, 280, 280], outline="#000000", width=3)
    draw.line([(20, 150), (280, 150)], fill="#000000", width=3)
    draw.line([(150, 20), (150, 280)], fill="#000000", width=3)
    for i in range(50, 251, 50):
        draw.ellipse([150-i//2, 150-i//2, 150+i//2, 150+i//2], outline="#000000", width=1)

    img.save(str(path))
    print(f"Created: {path}")


def create_test_multicolor(path: Path):
    """Create a multi-color geometric image for quantization testing."""
    w, h = 400, 400
    img = Image.new("RGB", (w, h), "#ffffff")
    draw = ImageDraw.Draw(img)

    colors = ["#e63946", "#457b9d", "#2a9d8f", "#e9c46a", "#264653",
              "#f4a261", "#a8dadc", "#1d3557"]

    cell_size = 100
    for row in range(4):
        for col in range(4):
            x1, y1 = col * cell_size, row * cell_size
            x2, y2 = x1 + cell_size, y1 + cell_size
            c = colors[(row * 4 + col) % len(colors)]
            draw.rectangle([x1, y1, x2, y2], fill=c)

    img.save(str(path))
    print(f"Created: {path}")


def create_test_transparent(path: Path):
    """Create an image with transparency."""
    w, h = 300, 300
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.ellipse([20, 20, 280, 280], fill=(91, 110, 247, 255))
    draw.rectangle([80, 80, 220, 220], fill=(52, 211, 153, 200))
    draw.ellipse([100, 100, 200, 200], fill=(251, 191, 36, 255))

    img.save(str(path))
    print(f"Created: {path}")


def create_test_complex(path: Path):
    """Create the required vector test image: circle, rectangle, diagonal, curves."""
    w, h = 500, 400
    img = Image.new("RGB", (w, h), "#f8f9fa")
    draw = ImageDraw.Draw(img)

    # Circle
    draw.ellipse([20, 20, 150, 150], fill="#5b6ef7", outline="#2a3070", width=2)
    # Rectangle
    draw.rectangle([200, 30, 380, 130], fill="#34d399", outline="#1a7a5a", width=2)
    # Diagonal line
    draw.line([(20, 300), (480, 150)], fill="#e63946", width=6)
    # Curved shape (approximate)
    pts = [(50, 300), (150, 250), (250, 350), (350, 280), (450, 380)]
    draw.line(pts, fill="#fbbf24", width=5)
    # Triangle
    draw.polygon([(400, 150), (480, 300), (320, 300)], fill="#f4a261", outline="#9a5000", width=2)

    img.save(str(path))
    print(f"Created: {path}")


if __name__ == "__main__":
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    create_test_logo(SAMPLES_DIR / "test_logo.png")
    create_test_bw(SAMPLES_DIR / "test_bw.png")
    create_test_multicolor(SAMPLES_DIR / "test_multicolor.png")
    create_test_transparent(SAMPLES_DIR / "test_transparent.png")
    create_test_complex(SAMPLES_DIR / "test_complex.png")
    print(f"\nAll sample images created in: {SAMPLES_DIR}")
