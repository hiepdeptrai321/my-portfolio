"""Generate First/Second/Third Day Grounded Pastel test atlases.

Fourth Day remains the approved reference and is read only. The workflow is
identical to Fourth: 2x antialiased UV masks, CIELAB chroma mapping with the
original L channel preserved, dark-pixel protection, and lossless WebP output.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
UV_DATA_PATH = (
    ROOT
    / "artifacts/grounded-pastel-no-rebake/remaining-day-recolor-uv-polygons.json"
)
TEST_ROOT = ROOT / "public/textures/room/grounded-pastel-test"
MASK_ROOT = TEST_ROOT / "masks"
DEBUG_ROOT = TEST_ROOT / "debug"
METRICS_PATH = (
    ROOT
    / "artifacts/grounded-pastel-no-rebake/remaining-day-test-metrics.json"
)
FOURTH_TEST = TEST_ROOT / "fourth-texture-set-day-grounded-test.webp"

ATLAS_FILES = {
    "first": {
        "source": ROOT / "public/textures/room/day/first-texture-set-day.webp",
        "test": TEST_ROOT / "first-texture-set-day-grounded-test.webp",
    },
    "second": {
        "source": ROOT / "public/textures/room/day/second-texture-set-day.webp",
        "test": TEST_ROOT / "second-texture-set-day-grounded-test.webp",
    },
    "third": {
        "source": ROOT / "public/textures/room/day/third-texture-set-day.webp",
        "test": TEST_ROOT / "third-texture-set-day-grounded-test.webp",
    },
}
DEBUG_COLORS = {
    "first/room-shell": "#FF3B30",
    "first/stone-structure": "#00C7FF",
    "first/neutral-structure": "#FFD60A",
    "first/cream-structure": "#AF52DE",
    "second/backdrop": "#34C759",
    "second/poster-frame": "#FF9500",
    "third/piano-body": "#0A84FF",
    "third/welcome-mat": "#FF2D55",
}
SUPERSAMPLE = 2
DEBUG_SIZE = (1024, 1024)


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
                int(
                    round(
                        (1.0 - min(max(uv[1], 0.0), 1.0))
                        * (render_height - 1)
                    )
                ),
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
    source: Image.Image,
    mask: Image.Image,
    atlas_key: str,
    group_name: str,
    output_path: Path,
) -> None:
    preview = source.resize(DEBUG_SIZE, Image.Resampling.LANCZOS).convert("RGB")
    preview_mask = mask.resize(DEBUG_SIZE, Image.Resampling.LANCZOS)
    mask_array = np.asarray(preview_mask, dtype=np.uint8)
    mask_float = mask_array.astype(np.float32) / 255.0

    source_array = np.asarray(preview, dtype=np.float32)
    debug_color = np.asarray(
        hex_to_rgb(DEBUG_COLORS[f"{atlas_key}/{group_name}"]), dtype=np.float32
    )
    alpha = (mask_float * 0.66)[..., None]
    overlay = source_array * (1.0 - alpha) + debug_color * alpha

    binary = (mask_array >= 128).astype(np.uint8)
    kernel = np.ones((3, 3), dtype=np.uint8)
    boundary = cv2.dilate(binary, kernel) - cv2.erode(binary, kernel)
    overlay[boundary > 0] = np.asarray([255, 255, 255], dtype=np.float32)

    output = Image.fromarray(np.clip(overlay, 0, 255).astype(np.uint8), "RGB")
    draw = ImageDraw.Draw(output)
    label = f"{atlas_key.title()} Day mask: {group_name}"
    draw.rectangle((12, 12, 390, 48), fill=(0, 0, 0))
    draw.text((22, 21), label, fill=(255, 255, 255), font=ImageFont.load_default())
    output.save(output_path, format="PNG", optimize=True)


def make_comparison(
    source: Image.Image, recolored: Image.Image, atlas_key: str, output_path: Path
) -> None:
    panel_width = 1024
    panel_height = 1024
    label_height = 46
    comparison = Image.new(
        "RGB", (panel_width * 2, panel_height + label_height), "#202522"
    )
    comparison.paste(
        source.resize((panel_width, panel_height), Image.Resampling.LANCZOS),
        (0, label_height),
    )
    comparison.paste(
        recolored.resize((panel_width, panel_height), Image.Resampling.LANCZOS),
        (panel_width, label_height),
    )
    draw = ImageDraw.Draw(comparison)
    font = ImageFont.load_default()
    draw.text(
        (18, 16), f"ORIGINAL {atlas_key.upper()} DAY", fill="white", font=font
    )
    draw.text(
        (panel_width + 18, 16),
        "GROUNDED PASTEL TEST",
        fill="white",
        font=font,
    )
    comparison.save(output_path, format="PNG", optimize=True)


def make_all_day_comparison(output_path: Path) -> None:
    cell_width = 1024
    image_height = 480
    label_height = 44
    cell_height = image_height + label_height
    sheet = Image.new("RGB", (cell_width * 2, cell_height * 2), "#202522")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    all_atlases = {
        **ATLAS_FILES,
        "fourth": {
            "source": ROOT / "public/textures/room/day/fourth-texture-set-day.webp",
            "test": FOURTH_TEST,
        },
    }
    for index, (atlas_key, paths) in enumerate(all_atlases.items()):
        column = index % 2
        row = index // 2
        x = column * cell_width
        y = row * cell_height
        source = Image.open(paths["source"]).convert("RGB")
        test = Image.open(paths["test"]).convert("RGB")
        source_preview = source.resize((cell_width // 2, image_height), Image.Resampling.LANCZOS)
        test_preview = test.resize((cell_width // 2, image_height), Image.Resampling.LANCZOS)
        sheet.paste(source_preview, (x, y + label_height))
        sheet.paste(test_preview, (x + cell_width // 2, y + label_height))
        draw.text(
            (x + 14, y + 15),
            f"{atlas_key.upper()} — ORIGINAL | GROUNDED TEST",
            fill="white",
            font=font,
        )
    sheet.save(output_path, format="PNG", optimize=True)


uv_data = json.loads(UV_DATA_PATH.read_text(encoding="utf-8"))
MASK_ROOT.mkdir(parents=True, exist_ok=True)
DEBUG_ROOT.mkdir(parents=True, exist_ok=True)
METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)

fourth_hash_before = sha256(FOURTH_TEST)
atlas_metrics: dict[str, object] = {}

for atlas_key, atlas_definition in uv_data["atlases"].items():
    paths = ATLAS_FILES[atlas_key]
    source_path = paths["source"]
    test_path = paths["test"]
    if source_path.resolve() == test_path.resolve():
        raise RuntimeError(f"{atlas_key}: test path cannot be the production atlas")

    source_hash_before = sha256(source_path)
    source_image = Image.open(source_path).convert("RGB")
    width, height = source_image.size
    if (width, height) != (4096, 4096):
        raise RuntimeError(
            f"{atlas_key}: expected 4096x4096 atlas, got {width}x{height}"
        )

    masks: dict[str, np.ndarray] = {}
    mask_reports: dict[str, object] = {}
    for group_name, group in atlas_definition["groups"].items():
        mask_image = render_mask(group["polygons"], width, height)
        mask_path = MASK_ROOT / f"{atlas_key}-mask-{group_name}.png"
        overlay_path = DEBUG_ROOT / f"{atlas_key}-debug-{group_name}-overlay.png"
        mask_image.save(mask_path, format="PNG", optimize=True)
        save_debug_overlay(
            source_image, mask_image, atlas_key, group_name, overlay_path
        )

        mask_array = np.asarray(mask_image, dtype=np.uint8)
        masks[group_name] = mask_array
        mask_reports[group_name] = {
            "file": mask_path.relative_to(ROOT).as_posix(),
            "debug_overlay": overlay_path.relative_to(ROOT).as_posix(),
            "dimensions": [width, height],
            "core_pixels": int(np.count_nonzero(mask_array >= 128)),
            "coverage_percent": round(
                float(np.count_nonzero(mask_array >= 128))
                * 100.0
                / (width * height),
                6,
            ),
            "bbox_xyxy": mask_bbox(mask_array),
        }

    core_stack = np.stack([mask >= 128 for mask in masks.values()], axis=0)
    overlap_count = np.sum(core_stack, axis=0)
    overlap_pixels = int(np.count_nonzero(overlap_count > 1))
    if overlap_pixels:
        raise RuntimeError(
            f"{atlas_key}: mask validation failed; {overlap_pixels} core pixels overlap"
        )

    source_rgb = np.asarray(source_image, dtype=np.uint8)
    source_lab = cv2.cvtColor(
        source_rgb.astype(np.float32) / 255.0, cv2.COLOR_RGB2LAB
    )
    working_lab = source_lab.copy()
    union_alpha = np.zeros((height, width), dtype=np.float32)
    for group_name, group in atlas_definition["groups"].items():
        alpha = masks[group_name].astype(np.float32) / 255.0
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
    converted_u8 = np.clip(np.rint(converted_rgb * 255.0), 0, 255).astype(
        np.uint8
    )
    result_rgb = source_rgb.copy()
    result_rgb[union_alpha > 0] = converted_u8[union_alpha > 0]
    result_image = Image.fromarray(result_rgb, "RGB")
    result_image.save(test_path, format="WEBP", lossless=True, quality=100, method=6)

    decoded_test = np.asarray(Image.open(test_path).convert("RGB"), dtype=np.uint8)
    decoded_lab = cv2.cvtColor(
        decoded_test.astype(np.float32) / 255.0, cv2.COLOR_RGB2LAB
    )
    core_union = np.any(core_stack, axis=0)
    outside_union = union_alpha == 0

    per_group_metrics: dict[str, object] = {}
    for group_name, mask in masks.items():
        core = mask >= 128
        before_l = source_lab[..., 0][core]
        after_l = decoded_lab[..., 0][core]
        per_group_metrics[group_name] = {
            "target_family": atlas_definition["groups"][group_name][
                "target_family"
            ],
            "target_hex": atlas_definition["groups"][group_name]["target_hex"],
            "mean_luminance_before": round(float(before_l.mean()), 6),
            "mean_luminance_after": round(float(after_l.mean()), 6),
            "mean_absolute_luminance_delta": round(
                float(np.mean(np.abs(after_l - before_l))), 6
            ),
            "luminance_correlation": round(
                (
                    float(np.corrcoef(before_l, after_l)[0, 1])
                    if before_l.size > 1
                    and before_l.std() > 0
                    and after_l.std() > 0
                    else 1.0
                ),
                9,
            ),
        }

    black_before = np.all(source_rgb <= 1, axis=2)
    black_after = np.all(decoded_test <= 1, axis=2)
    comparison_path = DEBUG_ROOT / f"{atlas_key}-day-original-vs-grounded-test.png"
    make_comparison(
        source_image,
        Image.fromarray(decoded_test, "RGB"),
        atlas_key,
        comparison_path,
    )

    atlas_metrics[atlas_key] = {
        "source_atlas": source_path.relative_to(ROOT).as_posix(),
        "source_sha256_before": source_hash_before,
        "source_sha256_after": sha256(source_path),
        "source_unchanged": source_hash_before == sha256(source_path),
        "test_atlas": test_path.relative_to(ROOT).as_posix(),
        "test_sha256": sha256(test_path),
        "dimensions": [width, height],
        "source_mode": source_image.mode,
        "test_mode": Image.open(test_path).mode,
        "mask_overlap_core_pixels": overlap_pixels,
        "mask_reports": mask_reports,
        "per_group": per_group_metrics,
        "outside_mask_pixel_mismatches": int(
            np.count_nonzero(
                np.any(
                    decoded_test[outside_union] != source_rgb[outside_union], axis=1
                )
            )
        ),
        "black_pixels_before": int(np.count_nonzero(black_before)),
        "black_pixels_after": int(np.count_nonzero(black_after)),
        "new_black_pixels": int(np.count_nonzero(black_after & ~black_before)),
        "removed_black_pixels": int(np.count_nonzero(black_before & ~black_after)),
        "core_mask_pixels": int(np.count_nonzero(core_union)),
        "comparison": comparison_path.relative_to(ROOT).as_posix(),
    }

all_day_comparison = DEBUG_ROOT / "all-four-day-atlas-comparisons.png"
make_all_day_comparison(all_day_comparison)

metrics = {
    "atlases": atlas_metrics,
    "approved_fourth_test": {
        "path": FOURTH_TEST.relative_to(ROOT).as_posix(),
        "sha256_before": fourth_hash_before,
        "sha256_after": sha256(FOURTH_TEST),
        "unchanged": fourth_hash_before == sha256(FOURTH_TEST),
    },
    "all_day_comparison": all_day_comparison.relative_to(ROOT).as_posix(),
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

print("REMAINING_DAY_TEST_METRICS", METRICS_PATH)
for atlas_key, atlas in atlas_metrics.items():
    print(
        "REMAINING_DAY_TEST",
        atlas_key,
        atlas["test_atlas"],
        "source_unchanged",
        atlas["source_unchanged"],
        "overlap",
        atlas["mask_overlap_core_pixels"],
        "outside_mismatch",
        atlas["outside_mask_pixel_mismatches"],
        "new_black",
        atlas["new_black_pixels"],
    )
print("APPROVED_FOURTH_UNCHANGED", metrics["approved_fourth_test"]["unchanged"])
