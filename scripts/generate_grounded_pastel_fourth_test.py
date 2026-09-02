"""Create Fourth Day UV masks and a luminance-preserving recolor test.

The original baked atlas is read-only. Outputs are written only beneath
``public/textures/room/grounded-pastel-test`` and the audit artifact folder.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ATLAS = ROOT / "public/textures/room/day/fourth-texture-set-day.webp"
UV_DATA = ROOT / "artifacts/grounded-pastel-no-rebake/fourth-recolor-uv-polygons.json"
TEST_ROOT = ROOT / "public/textures/room/grounded-pastel-test"
MASK_ROOT = TEST_ROOT / "masks"
DEBUG_ROOT = TEST_ROOT / "debug"
TEST_ATLAS = TEST_ROOT / "fourth-texture-set-day-grounded-test.webp"
METRICS_PATH = ROOT / "artifacts/grounded-pastel-no-rebake/fourth-day-test-metrics.json"

SUPERSAMPLE = 2
DEBUG_SIZE = (1024, 1024)
DEBUG_COLORS = {
    "drawer": "#FF3B30",
    "drawer-shelves": "#34C759",
    "computer": "#00C7FF",
    "chair-body": "#FFD60A",
    "chair-cushion": "#FF2D95",
    "desk-pad": "#FF9500",
    "keyboard-body": "#5856D6",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def render_mask(
    polygons: list[list[list[float]]], width: int, height: int
) -> Image.Image:
    render_width = width * SUPERSAMPLE
    render_height = height * SUPERSAMPLE
    mask = Image.new("L", (render_width, render_height), 0)
    draw = ImageDraw.Draw(mask)
    for polygon in polygons:
        points = [
            (
                int(round(min(max(uv[0], 0.0), 1.0) * (render_width - 1))),
                int(round((1.0 - min(max(uv[1], 0.0), 1.0)) * (render_height - 1))),
            )
            for uv in polygon
        ]
        if len(set(points)) >= 3:
            draw.polygon(points, fill=255)
    return mask.resize((width, height), Image.Resampling.LANCZOS)


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def target_lab(value: str) -> np.ndarray:
    rgb = np.asarray([[hex_to_rgb(value)]], dtype=np.float32) / 255.0
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)[0, 0]


def smoothstep(edge0: float, edge1: float, values: np.ndarray) -> np.ndarray:
    scaled = np.clip((values - edge0) / (edge1 - edge0), 0.0, 1.0)
    return scaled * scaled * (3.0 - 2.0 * scaled)


def mask_bbox(mask: np.ndarray) -> list[int] | None:
    rows, columns = np.nonzero(mask > 0)
    if not len(rows):
        return None
    return [
        int(columns.min()),
        int(rows.min()),
        int(columns.max()),
        int(rows.max()),
    ]


def save_debug_overlay(
    source: Image.Image, mask: Image.Image, group_name: str, output_path: Path
) -> None:
    preview = source.resize(DEBUG_SIZE, Image.Resampling.LANCZOS).convert("RGB")
    preview_mask = mask.resize(DEBUG_SIZE, Image.Resampling.LANCZOS)
    mask_array = np.asarray(preview_mask, dtype=np.uint8)
    mask_float = mask_array.astype(np.float32) / 255.0

    source_array = np.asarray(preview, dtype=np.float32)
    debug_color = np.asarray(hex_to_rgb(DEBUG_COLORS[group_name]), dtype=np.float32)
    alpha = (mask_float * 0.66)[..., None]
    overlay = source_array * (1.0 - alpha) + debug_color * alpha

    binary = (mask_array >= 128).astype(np.uint8)
    kernel = np.ones((3, 3), dtype=np.uint8)
    boundary = cv2.dilate(binary, kernel) - cv2.erode(binary, kernel)
    overlay[boundary > 0] = np.asarray([255, 255, 255], dtype=np.float32)

    output = Image.fromarray(np.clip(overlay, 0, 255).astype(np.uint8), "RGB")
    draw = ImageDraw.Draw(output)
    label = f"Fourth Day mask: {group_name}"
    draw.rectangle((12, 12, 360, 48), fill=(0, 0, 0))
    draw.text((22, 21), label, fill=(255, 255, 255), font=ImageFont.load_default())
    output.save(output_path, format="PNG", optimize=True)


def make_comparison(source: Image.Image, recolored: Image.Image, output_path: Path) -> None:
    panel_width = 1024
    panel_height = 1024
    label_height = 46
    comparison = Image.new("RGB", (panel_width * 2, panel_height + label_height), "#202522")
    comparison.paste(source.resize((panel_width, panel_height), Image.Resampling.LANCZOS), (0, label_height))
    comparison.paste(recolored.resize((panel_width, panel_height), Image.Resampling.LANCZOS), (panel_width, label_height))
    draw = ImageDraw.Draw(comparison)
    font = ImageFont.load_default()
    draw.text((18, 16), "ORIGINAL FOURTH DAY", fill="white", font=font)
    draw.text((panel_width + 18, 16), "GROUNDED PASTEL TEST", fill="white", font=font)
    comparison.save(output_path, format="PNG", optimize=True)


if SOURCE_ATLAS.resolve() == TEST_ATLAS.resolve():
    raise RuntimeError("Safety check failed: test output cannot be the production atlas")

source_hash_before = sha256(SOURCE_ATLAS)
uv_data = json.loads(UV_DATA.read_text(encoding="utf-8"))
source_image = Image.open(SOURCE_ATLAS).convert("RGB")
width, height = source_image.size
if (width, height) != (4096, 4096):
    raise RuntimeError(f"Expected 4096x4096 Fourth atlas, got {width}x{height}")

MASK_ROOT.mkdir(parents=True, exist_ok=True)
DEBUG_ROOT.mkdir(parents=True, exist_ok=True)
METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)

masks: dict[str, np.ndarray] = {}
mask_reports: dict[str, object] = {}
for group_name, group in uv_data["groups"].items():
    mask_image = render_mask(group["polygons"], width, height)
    mask_path = MASK_ROOT / f"fourth-mask-{group_name}.png"
    mask_image.save(mask_path, format="PNG", optimize=True)
    save_debug_overlay(
        source_image,
        mask_image,
        group_name,
        DEBUG_ROOT / f"fourth-debug-{group_name}-overlay.png",
    )

    mask_array = np.asarray(mask_image, dtype=np.uint8)
    masks[group_name] = mask_array
    mask_reports[group_name] = {
        "file": mask_path.relative_to(ROOT).as_posix(),
        "debug_overlay": (
            DEBUG_ROOT / f"fourth-debug-{group_name}-overlay.png"
        ).relative_to(ROOT).as_posix(),
        "dimensions": [width, height],
        "core_pixels": int(np.count_nonzero(mask_array >= 128)),
        "coverage_percent": round(
            float(np.count_nonzero(mask_array >= 128)) * 100.0 / (width * height), 6
        ),
        "bbox_xyxy": mask_bbox(mask_array),
    }

core_stack = np.stack([mask >= 128 for mask in masks.values()], axis=0)
overlap_count = np.sum(core_stack, axis=0)
overlap_pixels = int(np.count_nonzero(overlap_count > 1))
if overlap_pixels:
    raise RuntimeError(f"Mask validation failed: {overlap_pixels} core pixels overlap")

source_rgb = np.asarray(source_image, dtype=np.uint8)
source_lab = cv2.cvtColor(source_rgb.astype(np.float32) / 255.0, cv2.COLOR_RGB2LAB)
working_lab = source_lab.copy()
union_alpha = np.zeros((height, width), dtype=np.float32)

for group_name, group in uv_data["groups"].items():
    alpha = masks[group_name].astype(np.float32) / 255.0
    # Preserve true blacks and very dark screen/glass pixels while recoloring
    # the visible baked surface. L remains unchanged for every transformed pixel.
    visible_surface = smoothstep(4.0, 18.0, source_lab[..., 0])
    blend = alpha * float(group["strength"]) * visible_surface
    destination = target_lab(group["target_hex"])
    working_lab[..., 1] = (
        working_lab[..., 1] * (1.0 - blend) + destination[1] * blend
    )
    working_lab[..., 2] = (
        working_lab[..., 2] * (1.0 - blend) + destination[2] * blend
    )
    union_alpha = np.maximum(union_alpha, alpha)

converted_rgb = cv2.cvtColor(working_lab, cv2.COLOR_LAB2RGB)
converted_u8 = np.clip(np.rint(converted_rgb * 255.0), 0, 255).astype(np.uint8)
result_rgb = source_rgb.copy()
result_rgb[union_alpha > 0] = converted_u8[union_alpha > 0]
result_image = Image.fromarray(result_rgb, "RGB")
result_image.save(TEST_ATLAS, format="WEBP", lossless=True, quality=100, method=6)

decoded_test = np.asarray(Image.open(TEST_ATLAS).convert("RGB"), dtype=np.uint8)
decoded_lab = cv2.cvtColor(decoded_test.astype(np.float32) / 255.0, cv2.COLOR_RGB2LAB)
core_union = np.any(core_stack, axis=0)
outside_union = union_alpha == 0

per_group_metrics: dict[str, object] = {}
for group_name, mask in masks.items():
    core = mask >= 128
    before_l = source_lab[..., 0][core]
    after_l = decoded_lab[..., 0][core]
    per_group_metrics[group_name] = {
        "target_family": uv_data["groups"][group_name]["target_family"],
        "target_hex": uv_data["groups"][group_name]["target_hex"],
        "mean_luminance_before": round(float(before_l.mean()), 6),
        "mean_luminance_after": round(float(after_l.mean()), 6),
        "mean_absolute_luminance_delta": round(
            float(np.mean(np.abs(after_l - before_l))), 6
        ),
        "luminance_correlation": round(
            (
                float(np.corrcoef(before_l, after_l)[0, 1])
                if before_l.size > 1 and before_l.std() > 0 and after_l.std() > 0
                else 1.0
            ),
            9,
        ),
    }

black_before = np.all(source_rgb <= 1, axis=2)
black_after = np.all(decoded_test <= 1, axis=2)
comparison_path = DEBUG_ROOT / "fourth-day-original-vs-grounded-test.png"
make_comparison(source_image, Image.fromarray(decoded_test, "RGB"), comparison_path)

metrics = {
    "source_atlas": SOURCE_ATLAS.relative_to(ROOT).as_posix(),
    "source_sha256_before": source_hash_before,
    "source_sha256_after": sha256(SOURCE_ATLAS),
    "source_unchanged": source_hash_before == sha256(SOURCE_ATLAS),
    "test_atlas": TEST_ATLAS.relative_to(ROOT).as_posix(),
    "test_sha256": sha256(TEST_ATLAS),
    "dimensions": [width, height],
    "source_mode": source_image.mode,
    "test_mode": Image.open(TEST_ATLAS).mode,
    "mask_overlap_core_pixels": overlap_pixels,
    "mask_reports": mask_reports,
    "per_group": per_group_metrics,
    "outside_mask_pixel_mismatches": int(
        np.count_nonzero(np.any(decoded_test[outside_union] != source_rgb[outside_union], axis=1))
    ),
    "black_pixels_before": int(np.count_nonzero(black_before)),
    "black_pixels_after": int(np.count_nonzero(black_after)),
    "new_black_pixels": int(np.count_nonzero(black_after & ~black_before)),
    "removed_black_pixels": int(np.count_nonzero(black_before & ~black_after)),
    "core_mask_pixels": int(np.count_nonzero(core_union)),
    "comparison": comparison_path.relative_to(ROOT).as_posix(),
    "method": {
        "color_space": "CIELAB",
        "luminance": "Original L channel preserved",
        "chroma": "Original a/b blended toward each target palette color",
        "dark_pixel_protection": "Smoothstep L=4..18",
        "mask_edges": f"{SUPERSAMPLE}x rasterization then Lanczos antialiasing",
        "output_encoding": "Lossless WebP RGB",
    },
}
METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

print("FOURTH_TEST_ATLAS", TEST_ATLAS)
print("FOURTH_TEST_METRICS", METRICS_PATH)
print("FOURTH_SOURCE_UNCHANGED", metrics["source_unchanged"])
print("FOURTH_MASK_OVERLAP_PIXELS", overlap_pixels)
print("FOURTH_OUTSIDE_MASK_MISMATCHES", metrics["outside_mask_pixel_mismatches"])
print("FOURTH_NEW_BLACK_PIXELS", metrics["new_black_pixels"])
