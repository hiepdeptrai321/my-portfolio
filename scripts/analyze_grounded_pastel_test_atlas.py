"""Create review previews and print metrics for the single Day test atlas."""

from __future__ import annotations

import hashlib
from pathlib import Path

import cv2
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = REPO_ROOT / "public" / "textures" / "room" / "day" / "first-texture-set-day.webp"
TEST = REPO_ROOT / "artifacts" / "grounded-pastel-test" / "first-texture-set-day-test.png"
OUTPUT_DIR = TEST.parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def to_rgb8(image: np.ndarray) -> np.ndarray:
    color = cv2.cvtColor(image[:, :, :3], cv2.COLOR_BGR2RGB)
    if color.dtype == np.uint16:
        color = np.rint(color.astype(np.float32) / 257.0).astype(np.uint8)
    return color


def metrics(label: str, image: np.ndarray) -> None:
    rgb = to_rgb8(image)
    maximum = rgb.max(axis=2)
    luminance = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    print(f"{label}_SIZE {rgb.shape[1]}x{rgb.shape[0]}")
    print(f"{label}_RGB_MEAN {rgb.mean(axis=(0, 1))}")
    print(f"{label}_LUMA_PERCENTILES {np.percentile(luminance, [1, 5, 25, 50, 75, 95, 99])}")
    print(f"{label}_BLACK_PERCENT {np.mean(maximum < 8) * 100:.6f}")
    print(f"{label}_DARK_PERCENT {np.mean(maximum < 24) * 100:.6f}")
    if image.shape[2] == 4:
        alpha = image[:, :, 3]
        alpha_max = np.iinfo(alpha.dtype).max
        print(f"{label}_ALPHA_ZERO_PERCENT {np.mean(alpha == 0) * 100:.6f}")
        print(f"{label}_ALPHA_PARTIAL_PERCENT {np.mean((alpha > 0) & (alpha < alpha_max)) * 100:.6f}")
        print(f"{label}_ALPHA_OPAQUE_PERCENT {np.mean(alpha == alpha_max) * 100:.6f}")


def preview(image: np.ndarray, checker: bool = False) -> np.ndarray:
    rgb = to_rgb8(image)
    if checker and image.shape[2] == 4:
        alpha = image[:, :, 3].astype(np.float32) / np.iinfo(image.dtype).max
        yy, xx = np.indices(alpha.shape)
        tile = ((xx // 48 + yy // 48) % 2).astype(np.uint8)
        checker_rgb = np.where(tile[:, :, None] == 0, 210, 245).astype(np.uint8)
        rgb = np.rint(rgb * alpha[:, :, None] + checker_rgb * (1.0 - alpha[:, :, None])).astype(np.uint8)
    return cv2.resize(rgb, (1024, 1024), interpolation=cv2.INTER_AREA)


def title_panel(image: np.ndarray, title: str) -> np.ndarray:
    panel = np.full((72, image.shape[1], 3), (241, 233, 222), dtype=np.uint8)
    cv2.putText(panel, title, (22, 47), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (64, 93, 82), 2, cv2.LINE_AA)
    return np.vstack((panel, image))


production = cv2.imread(str(PRODUCTION), cv2.IMREAD_UNCHANGED)
test = cv2.imread(str(TEST), cv2.IMREAD_UNCHANGED)
if production is None or test is None:
    raise FileNotFoundError(f"Missing comparison image: production={PRODUCTION.exists()} test={TEST.exists()}")

print(f"PRODUCTION_SHA256 {sha256(PRODUCTION)}")
print(f"TEST_SHA256 {sha256(TEST)}")
metrics("PRODUCTION", production)
metrics("TEST", test)

production_preview = preview(production)
test_preview = preview(test, checker=True)
cv2.imwrite(str(OUTPUT_DIR / "production-first-day-preview.png"), cv2.cvtColor(production_preview, cv2.COLOR_RGB2BGR))
cv2.imwrite(str(OUTPUT_DIR / "test-first-day-preview.png"), cv2.cvtColor(test_preview, cv2.COLOR_RGB2BGR))

comparison = np.hstack(
    (
        title_panel(production_preview, "Current production Day atlas 1"),
        title_panel(test_preview, "Native Cycles test (alpha shown as checkerboard)"),
    )
)
cv2.imwrite(str(OUTPUT_DIR / "first-day-atlas-comparison.png"), cv2.cvtColor(comparison, cv2.COLOR_RGB2BGR))
print(f"COMPARISON_PREVIEW {OUTPUT_DIR / 'first-day-atlas-comparison.png'}")
