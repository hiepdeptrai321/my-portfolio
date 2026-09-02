"""Create four Grounded Pastel Night TEST atlases without baking.

Every source is an original production Night atlas. The script reuses the
already validated Day UV masks as read-only inputs, preserves the source Lab L
channel, changes only masked chroma, and writes only to the test/debug/artifact
directories.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = ROOT / "public/textures/room/grounded-pastel-test"
MASK_ROOT = TEST_ROOT / "masks"
DEBUG_ROOT = TEST_ROOT / "debug"
METRICS_PATH = (
    ROOT / "artifacts/grounded-pastel-no-rebake/all-night-test-metrics.json"
)
DEBUG_SIZE = (1024, 1024)
TRANSITION_SIZE = (1024, 1024)


ATLASES = {
    "first": {
        "source": ROOT / "public/textures/room/night/first-texture-set-night.webp",
        "day_test": TEST_ROOT / "first-texture-set-day-grounded-test.webp",
        "night_test": TEST_ROOT / "first-texture-set-night-grounded-test.webp",
        "groups": {
            "room-shell": {
                "object_material": "Cube / Room",
                "day_family": "Warm Cream",
                "day_hex": "#F1E9DE",
                "night_family": "Warm Dim Cream",
                "night_hex": "#BEB3A5",
                "strength": 0.90,
            },
            "stone-structure": {
                "object_material": "Cube.039 / Stone wall",
                "day_family": "Mist Gray",
                "day_hex": "#DCE2DE",
                "night_family": "Night Mist Gray",
                "night_hex": "#818D89",
                "strength": 0.86,
            },
            "neutral-structure": {
                "object_material": "Plane.001 / Base Gray.001",
                "day_family": "Mist Gray",
                "day_hex": "#DCE2DE",
                "night_family": "Night Mist Gray",
                "night_hex": "#818D89",
                "strength": 0.88,
            },
            "cream-structure": {
                "object_material": "Cube.020 / Base White.001",
                "day_family": "Warm Cream",
                "day_hex": "#F1E9DE",
                "night_family": "Warm Dim Cream",
                "night_hex": "#BEB3A5",
                "strength": 0.88,
            },
        },
    },
    "second": {
        "source": ROOT / "public/textures/room/night/second-texture-set-night.webp",
        "day_test": TEST_ROOT / "second-texture-set-day-grounded-test.webp",
        "night_test": TEST_ROOT / "second-texture-set-night-grounded-test.webp",
        "groups": {
            "backdrop": {
                "object_material": "Backdrop / Backdrop.001",
                "day_family": "Mist Gray",
                "day_hex": "#DCE2DE",
                "night_family": "Night Mist Gray",
                "night_hex": "#818D89",
                "strength": 0.88,
            },
            "poster-frame": {
                "object_material": "Plane.122 / Poster Frame",
                "day_family": "Deep Sage",
                "day_hex": "#405D52",
                "night_family": "Charcoal Sage",
                "night_hex": "#263C35",
                "strength": 0.84,
            },
        },
    },
    "third": {
        "source": ROOT / "public/textures/room/night/third-texture-set-night.webp",
        "day_test": TEST_ROOT / "third-texture-set-day-grounded-test.webp",
        "night_test": TEST_ROOT / "third-texture-set-night-grounded-test.webp",
        "groups": {
            "piano-body": {
                "object_material": (
                    "Piano / Base Gray.001, Piano.001, Base Purple.001"
                ),
                "day_family": "Dusty Blue",
                "day_hex": "#8FA9B8",
                "night_family": "Night Dusty Blue",
                "night_hex": "#526C7A",
                "strength": 0.90,
            },
            "welcome-mat": {
                "object_material": (
                    "Plane.019 / Welcome Mat.001, Drawer Shelves.001"
                ),
                "day_family": "Sage Green",
                "day_hex": "#718E7A",
                "night_family": "Night Sage",
                "night_hex": "#4E6759",
                "strength": 0.88,
            },
        },
    },
    "fourth": {
        "source": ROOT / "public/textures/room/night/fourth-texture-set-night.webp",
        "day_test": TEST_ROOT / "fourth-texture-set-day-grounded-test.webp",
        "night_test": TEST_ROOT / "fourth-texture-set-night-grounded-test.webp",
        "groups": {
            "drawer": {
                "object_material": "Plane.030 / Drawer",
                "day_family": "Sage Green",
                "day_hex": "#718E7A",
                "night_family": "Night Sage",
                "night_hex": "#4E6759",
                "strength": 0.90,
            },
            "drawer-shelves": {
                "object_material": "Plane.031 / Drawer Shelves.001",
                "day_family": "Warm Cream",
                "day_hex": "#F1E9DE",
                "night_family": "Warm Dim Cream",
                "night_hex": "#BEB3A5",
                "strength": 0.88,
            },
            "computer": {
                "object_material": "Computer + Plane.020 / computer body",
                "day_family": "Dusty Blue",
                "day_hex": "#8FA9B8",
                "night_family": "Night Dusty Blue",
                "night_hex": "#526C7A",
                "strength": 0.90,
            },
            "chair-body": {
                "object_material": "Chair Top + Chair Legs / chair body",
                "day_family": "Warm Cream",
                "day_hex": "#F1E9DE",
                "night_family": "Warm Dim Cream",
                "night_hex": "#BEB3A5",
                "strength": 0.88,
            },
            "chair-cushion": {
                "object_material": "Chair Top / Chair Cushion",
                "day_family": "Soft Terracotta",
                "day_hex": "#D99478",
                "night_family": "Night Terracotta",
                "night_hex": "#9D6253",
                "strength": 0.90,
            },
            "desk-pad": {
                "object_material": "Cube.002 / Desk Pad",
                "day_family": "Soft Terracotta",
                "day_hex": "#D99478",
                "night_family": "Night Terracotta",
                "night_hex": "#9D6253",
                "strength": 0.90,
            },
            "keyboard-body": {
                "object_material": "Cube.003 / Keyboard body",
                "day_family": "Warm Cream",
                "day_hex": "#F1E9DE",
                "night_family": "Warm Dim Cream",
                "night_hex": "#BEB3A5",
                "strength": 0.86,
            },
        },
    },
}

DEBUG_COLORS = {
    "room-shell": "#FF3B30",
    "stone-structure": "#00C7FF",
    "neutral-structure": "#FFD60A",
    "cream-structure": "#AF52DE",
    "backdrop": "#34C759",
    "poster-frame": "#FF9500",
    "piano-body": "#0A84FF",
    "welcome-mat": "#FF2D55",
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


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def target_lab(value: str) -> np.ndarray:
    rgb = np.asarray([[hex_to_rgb(value)]], dtype=np.float32) / 255.0
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)[0, 0]


def smoothstep(edge0: float, edge1: float, values: np.ndarray) -> np.ndarray:
    scaled = np.clip((values - edge0) / (edge1 - edge0), 0.0, 1.0)
    return scaled * scaled * (3.0 - 2.0 * scaled)


def save_night_mask_overlay(
    source: Image.Image,
    mask: Image.Image,
    atlas_key: str,
    group_name: str,
    output_path: Path,
) -> None:
    preview = source.resize(DEBUG_SIZE, Image.Resampling.LANCZOS).convert("RGB")
    preview_mask = mask.resize(DEBUG_SIZE, Image.Resampling.LANCZOS)
    mask_array = np.asarray(preview_mask, dtype=np.uint8)
    source_array = np.asarray(preview, dtype=np.float32)
    debug_color = np.asarray(hex_to_rgb(DEBUG_COLORS[group_name]), dtype=np.float32)
    alpha = (mask_array.astype(np.float32) / 255.0 * 0.66)[..., None]
    overlay = source_array * (1.0 - alpha) + debug_color * alpha

    binary = (mask_array >= 128).astype(np.uint8)
    kernel = np.ones((3, 3), dtype=np.uint8)
    boundary = cv2.dilate(binary, kernel) - cv2.erode(binary, kernel)
    overlay[boundary > 0] = np.asarray([255, 255, 255], dtype=np.float32)

    output = Image.fromarray(np.clip(overlay, 0, 255).astype(np.uint8), "RGB")
    draw = ImageDraw.Draw(output)
    draw.rectangle((12, 12, 430, 48), fill=(0, 0, 0))
    draw.text(
        (22, 21),
        f"{atlas_key.title()} Night reused Day mask: {group_name}",
        fill=(255, 255, 255),
        font=ImageFont.load_default(),
    )
    output.save(output_path, format="PNG", optimize=True)


def make_comparison(
    source: Image.Image,
    recolored: Image.Image,
    atlas_key: str,
    output_path: Path,
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
        (18, 16), f"ORIGINAL {atlas_key.upper()} NIGHT", fill="white", font=font
    )
    draw.text(
        (panel_width + 18, 16),
        "GROUNDED PASTEL NIGHT TEST",
        fill="white",
        font=font,
    )
    comparison.save(output_path, format="PNG", optimize=True)


def make_sheet(
    path_pairs: dict[str, tuple[Path, Path]],
    output_path: Path,
    left_label: str,
    right_label: str,
) -> None:
    cell_width = 1024
    image_height = 480
    label_height = 44
    cell_height = image_height + label_height
    sheet = Image.new("RGB", (cell_width * 2, cell_height * 2), "#202522")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for index, (atlas_key, paths) in enumerate(path_pairs.items()):
        column = index % 2
        row = index // 2
        x = column * cell_width
        y = row * cell_height
        left = Image.open(paths[0]).convert("RGB").resize(
            (cell_width // 2, image_height), Image.Resampling.LANCZOS
        )
        right = Image.open(paths[1]).convert("RGB").resize(
            (cell_width // 2, image_height), Image.Resampling.LANCZOS
        )
        sheet.paste(left, (x, y + label_height))
        sheet.paste(right, (x + cell_width // 2, y + label_height))
        draw.text(
            (x + 14, y + 15),
            f"{atlas_key.upper()} — {left_label} | {right_label}",
            fill="white",
            font=font,
        )
    sheet.save(output_path, format="PNG", optimize=True)


def transition_metrics(
    day_path: Path,
    night_path: Path,
    masks: dict[str, np.ndarray],
    preview_path: Path,
) -> dict[str, object]:
    day = np.asarray(
        Image.open(day_path).convert("RGB").resize(
            TRANSITION_SIZE, Image.Resampling.LANCZOS
        ),
        dtype=np.float32,
    )
    night = np.asarray(
        Image.open(night_path).convert("RGB").resize(
            TRANSITION_SIZE, Image.Resampling.LANCZOS
        ),
        dtype=np.float32,
    )
    resized_masks = {
        name: np.asarray(
            Image.fromarray(mask, "L").resize(
                TRANSITION_SIZE, Image.Resampling.LANCZOS
            ),
            dtype=np.uint8,
        )
        >= 128
        for name, mask in masks.items()
    }
    union = np.any(np.stack(list(resized_masks.values()), axis=0), axis=0)
    day_srgb = day / 255.0
    night_srgb = night / 255.0
    day_linear = np.where(
        day_srgb <= 0.04045,
        day_srgb / 12.92,
        ((day_srgb + 0.055) / 1.055) ** 2.4,
    )
    night_linear = np.where(
        night_srgb <= 0.04045,
        night_srgb / 12.92,
        ((night_srgb + 0.055) / 1.055) ** 2.4,
    )
    ratios = [0.0, 0.25, 0.5, 0.75, 1.0]
    purple_percent: dict[str, float] = {}
    per_group_path: dict[str, list[dict[str, float]]] = {
        name: [] for name in resized_masks
    }
    preview_frames: list[tuple[float, Image.Image]] = []

    for ratio in ratios:
        mixed_linear = day_linear * (1.0 - ratio) + night_linear * ratio
        # Match the unchanged theme shader's finalColor = pow(finalColor, 1/2.2).
        shader_display = np.clip(mixed_linear, 0.0, 1.0) ** (1.0 / 2.2)
        lab = cv2.cvtColor(shader_display.astype(np.float32), cv2.COLOR_RGB2LAB)
        strong_purple = (lab[..., 1] > 12.0) & (lab[..., 2] < -6.0)
        purple_percent[f"{ratio:.2f}"] = round(
            float(np.count_nonzero(strong_purple & union))
            * 100.0
            / max(int(np.count_nonzero(union)), 1),
            6,
        )
        for name, core in resized_masks.items():
            per_group_path[name].append(
                {
                    "mix_ratio": ratio,
                    "mean_lab_a": round(float(lab[..., 1][core].mean()), 6),
                    "mean_lab_b": round(float(lab[..., 2][core].mean()), 6),
                }
            )
        preview_frames.append(
            (
                ratio,
                Image.fromarray(
                    np.clip(np.rint(shader_display * 255.0), 0, 255).astype(
                        np.uint8
                    ),
                    "RGB",
                ).resize((512, 512), Image.Resampling.LANCZOS),
            )
        )

    label_height = 42
    strip = Image.new("RGB", (512 * len(preview_frames), 512 + label_height), "#202522")
    draw = ImageDraw.Draw(strip)
    for index, (ratio, frame) in enumerate(preview_frames):
        x = index * 512
        strip.paste(frame, (x, label_height))
        draw.text(
            (x + 14, 15),
            f"uMixRatio {ratio:.2f}",
            fill="white",
            font=ImageFont.load_default(),
        )
    strip.save(preview_path, format="PNG", optimize=True)

    endpoint_peak = max(purple_percent["0.00"], purple_percent["1.00"])
    intermediate_peak = max(
        purple_percent["0.25"],
        purple_percent["0.50"],
        purple_percent["0.75"],
    )
    return {
        "analysis_dimensions": list(TRANSITION_SIZE),
        "shader_model": (
            "sRGB texture decode -> linear RGB mix(day, night, uMixRatio) -> "
            "pow(1/2.2), matching the current theme shader"
        ),
        "preview": preview_path.relative_to(ROOT).as_posix(),
        "strong_purple_definition": "Lab a > 12 and Lab b < -6 inside recolor masks",
        "strong_purple_percent_by_mix_ratio": purple_percent,
        "intermediate_purple_overshoot_percent": round(
            max(0.0, intermediate_peak - endpoint_peak), 6
        ),
        "purple_flash_detected": intermediate_peak > endpoint_peak + 0.05,
        "per_group_mean_lab_path": per_group_path,
    }


TEST_ROOT.mkdir(parents=True, exist_ok=True)
DEBUG_ROOT.mkdir(parents=True, exist_ok=True)
METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)

approved_day_hashes_before = {
    atlas_key: sha256(atlas["day_test"]) for atlas_key, atlas in ATLASES.items()
}
production_hashes_before = {
    atlas_key: sha256(atlas["source"]) for atlas_key, atlas in ATLASES.items()
}
atlas_metrics: dict[str, object] = {}

for atlas_key, atlas in ATLASES.items():
    source_path = atlas["source"]
    output_path = atlas["night_test"]
    if source_path.resolve() == output_path.resolve():
        raise RuntimeError(f"{atlas_key}: output cannot be a production atlas")

    source_image = Image.open(source_path).convert("RGB")
    width, height = source_image.size
    if (width, height) != (4096, 4096):
        raise RuntimeError(
            f"{atlas_key}: expected 4096x4096 Night atlas, got {width}x{height}"
        )

    masks: dict[str, np.ndarray] = {}
    mask_reports: dict[str, object] = {}
    for group_name in atlas["groups"]:
        mask_path = MASK_ROOT / f"{atlas_key}-mask-{group_name}.png"
        mask_hash_before = sha256(mask_path)
        mask_image = Image.open(mask_path).convert("L")
        if mask_image.size != (width, height):
            raise RuntimeError(
                f"{atlas_key}/{group_name}: Day mask {mask_image.size} does not "
                f"match Night atlas {(width, height)}"
            )
        mask_array = np.asarray(mask_image, dtype=np.uint8)
        masks[group_name] = mask_array
        overlay_path = (
            DEBUG_ROOT / f"{atlas_key}-night-debug-{group_name}-overlay.png"
        )
        save_night_mask_overlay(
            source_image, mask_image, atlas_key, group_name, overlay_path
        )
        mask_reports[group_name] = {
            "reused_day_mask": mask_path.relative_to(ROOT).as_posix(),
            "day_mask_sha256_before": mask_hash_before,
            "day_mask_sha256_after": sha256(mask_path),
            "day_mask_unchanged": mask_hash_before == sha256(mask_path),
            "dimensions_match_night": mask_image.size == source_image.size,
            "core_pixels": int(np.count_nonzero(mask_array >= 128)),
            "night_alignment_overlay": overlay_path.relative_to(ROOT).as_posix(),
        }

    core_stack = np.stack([mask >= 128 for mask in masks.values()], axis=0)
    overlap_pixels = int(np.count_nonzero(np.sum(core_stack, axis=0) > 1))
    if overlap_pixels:
        raise RuntimeError(
            f"{atlas_key}: reused masks overlap at {overlap_pixels} core pixels"
        )

    source_rgb = np.asarray(source_image, dtype=np.uint8)
    source_lab = cv2.cvtColor(
        source_rgb.astype(np.float32) / 255.0, cv2.COLOR_RGB2LAB
    )
    working_lab = source_lab.copy()
    union_alpha = np.zeros((height, width), dtype=np.float32)

    for group_name, group in atlas["groups"].items():
        alpha = masks[group_name].astype(np.float32) / 255.0
        visible_surface = smoothstep(4.0, 18.0, source_lab[..., 0])
        blend = alpha * float(group["strength"]) * visible_surface
        destination = target_lab(group["night_hex"])
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
    Image.fromarray(result_rgb, "RGB").save(
        output_path, format="WEBP", lossless=True, quality=100, method=6
    )

    decoded_image = Image.open(output_path).convert("RGB")
    decoded_test = np.asarray(decoded_image, dtype=np.uint8)
    decoded_lab = cv2.cvtColor(
        decoded_test.astype(np.float32) / 255.0, cv2.COLOR_RGB2LAB
    )
    outside_union = union_alpha == 0
    per_group: dict[str, object] = {}
    for group_name, group in atlas["groups"].items():
        core = masks[group_name] >= 128
        before_l = source_lab[..., 0][core]
        after_l = decoded_lab[..., 0][core]
        per_group[group_name] = {
            "object_material": group["object_material"],
            "day_family": group["day_family"],
            "day_hex": group["day_hex"],
            "night_family": group["night_family"],
            "night_hex": group["night_hex"],
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
    blown_before = source_lab[..., 0] >= 99.0
    blown_after = decoded_lab[..., 0] >= 99.0
    comparison_path = (
        DEBUG_ROOT / f"{atlas_key}-night-original-vs-grounded-test.png"
    )
    make_comparison(source_image, decoded_image, atlas_key, comparison_path)

    atlas_metrics[atlas_key] = {
        "source_atlas": source_path.relative_to(ROOT).as_posix(),
        "source_sha256_before": production_hashes_before[atlas_key],
        "source_sha256_after": sha256(source_path),
        "source_unchanged": production_hashes_before[atlas_key]
        == sha256(source_path),
        "test_atlas": output_path.relative_to(ROOT).as_posix(),
        "test_sha256": sha256(output_path),
        "dimensions": [width, height],
        "source_mode": source_image.mode,
        "test_mode": decoded_image.mode,
        "uv_alignment_basis": (
            "Same 4096x4096 atlas dimensions and the same per-texture-set vUv "
            "used by Day/Night samplers in the unchanged theme shader"
        ),
        "reused_day_masks": mask_reports,
        "new_night_specific_masks": [],
        "mask_overlap_core_pixels": overlap_pixels,
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
        "new_blown_highlight_pixels": int(
            np.count_nonzero(blown_after & ~blown_before)
        ),
        "per_group": per_group,
        "comparison": comparison_path.relative_to(ROOT).as_posix(),
        "transition": transition_metrics(
            atlas["day_test"],
            output_path,
            masks,
            DEBUG_ROOT / f"{atlas_key}-day-night-transition-strip.png",
        ),
    }

night_comparison = DEBUG_ROOT / "all-four-night-atlas-comparisons.png"
make_sheet(
    {
        key: (atlas["source"], atlas["night_test"])
        for key, atlas in ATLASES.items()
    },
    night_comparison,
    "ORIGINAL NIGHT",
    "GROUNDED NIGHT",
)
day_night_comparison = DEBUG_ROOT / "all-four-grounded-day-night-consistency.png"
make_sheet(
    {
        key: (atlas["day_test"], atlas["night_test"])
        for key, atlas in ATLASES.items()
    },
    day_night_comparison,
    "GROUNDED DAY",
    "GROUNDED NIGHT",
)

metrics = {
    "atlases": atlas_metrics,
    "approved_day_tests": {
        key: {
            "path": atlas["day_test"].relative_to(ROOT).as_posix(),
            "sha256_before": approved_day_hashes_before[key],
            "sha256_after": sha256(atlas["day_test"]),
            "unchanged": approved_day_hashes_before[key]
            == sha256(atlas["day_test"]),
        }
        for key, atlas in ATLASES.items()
    },
    "all_night_comparison": night_comparison.relative_to(ROOT).as_posix(),
    "all_day_night_consistency": day_night_comparison.relative_to(ROOT).as_posix(),
    "mask_alignment": {
        "reused_validated_day_masks": True,
        "new_night_specific_masks": [],
        "reason": (
            "Every mask is 4096x4096, uses the same baked UV/object membership, "
            "and Day/Night samplers share vUv in the unchanged shader."
        ),
    },
    "method": {
        "source": "Original production Night atlases only",
        "color_space": "CIELAB",
        "luminance": "Original Night L channel preserved",
        "chroma": "Original a/b blended toward darker Grounded Pastel targets",
        "dark_pixel_protection": "Smoothstep L=4..18",
        "masks": "Validated Day masks reused read-only",
        "output_encoding": "Lossless WebP RGB",
    },
}
METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

print("ALL_NIGHT_TEST_METRICS", METRICS_PATH)
for atlas_key, atlas in atlas_metrics.items():
    print(
        "NIGHT_TEST",
        atlas_key,
        atlas["test_atlas"],
        "source_unchanged",
        atlas["source_unchanged"],
        "outside_mismatch",
        atlas["outside_mask_pixel_mismatches"],
        "new_black",
        atlas["new_black_pixels"],
        "new_blown",
        atlas["new_blown_highlight_pixels"],
        "purple_flash",
        atlas["transition"]["purple_flash_detected"],
    )
print(
    "APPROVED_DAY_TESTS_UNCHANGED",
    all(item["unchanged"] for item in metrics["approved_day_tests"].values()),
)
