#!/usr/bin/env python3
"""Build reviewable Palmier split/delete plans without modifying the project."""
import argparse
import json
import math
from pathlib import Path


def number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return value


def frame(value, label):
    number(value, label)
    if int(value) != value:
        raise ValueError(f"{label} must be an integer frame")
    return int(value)


def build(data):
    fps = number(data["fps"], "fps")
    if fps <= 0:
        raise ValueError("fps must be positive")
    start, end = [frame(v, "clip_frames") for v in data["clip_frames"]]
    if start < 0 or end <= start:
        raise ValueError("clip_frames must be a nonnegative half-open range")
    cfg = data.get("settings", {})
    defaults = {"split_min_seconds": 0.5, "clean_min_seconds": 1.5,
                "split_padding_seconds": 0.15, "clean_after_seconds": 0.4,
                "clean_before_seconds": 0.25, "coalesce_frames": 0}
    if set(cfg) - set(defaults):
        raise ValueError("Unknown settings: " + ", ".join(sorted(set(cfg) - set(defaults))))
    for key, default in defaults.items():
        defaults[key] = number(cfg.get(key, default), key)
        if defaults[key] < 0:
            raise ValueError(f"{key} must be nonnegative")
    proximity = frame(defaults["coalesce_frames"], "coalesce_frames")
    cuts, drops = set(), []
    for pause in data.get("pauses_seconds", []):
        a, b = [number(v, "pause") for v in pause]
        if a < 0 or b <= a:
            raise ValueError("Each pause must satisfy 0 <= start < end")
        a, b = max(a, start / fps), min(b, end / fps)
        if b <= a:
            continue
        if b - a >= defaults["split_min_seconds"]:
            left = math.ceil((a + defaults["split_padding_seconds"]) * fps)
            right = math.floor((b - defaults["split_padding_seconds"]) * fps)
            if left < right:
                if a > start / fps:
                    cuts.add(left)
                if b < end / fps:
                    cuts.add(right)
        if b - a >= defaults["clean_min_seconds"]:
            left = start if a == start / fps else math.ceil((a + defaults["clean_after_seconds"]) * fps)
            right = end if b == end / fps else math.floor((b - defaults["clean_before_seconds"]) * fps)
            if left < right:
                drops.append([left, right])
    for item in data.get("drop_frames", []):
        a, b = [frame(v, "drop_frames") for v in item]
        if a < start or b > end or a >= b:
            raise ValueError("Editorial drops must be inside clip_frames")
        drops.append([a, b])
        cuts.update([a, b])
    for item in data.get("split_frames", []):
        pos = frame(item, "split_frames")
        if not start < pos < end:
            raise ValueError("Explicit splits must be strictly inside clip_frames")
        cuts.add(pos)
    merged = []
    for a, b in sorted(drops):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    consolidated = []
    for pos in sorted(c for c in cuts if start < c < end):
        if not consolidated or pos - consolidated[-1] > proximity:
            consolidated.append(pos)
    removed = sum(b - a for a, b in merged)
    return {"fps": fps, "clip_frames": [start, end], "split_frames": consolidated,
            "delete_ranges_frames": merged, "removed_frames": removed,
            "kept_frames": end - start - removed,
            "kept_seconds": (end - start - removed) / fps,
            "note": "Candidates require editorial review. Map source times to timeline first."}


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog='Input JSON: {"fps":30,"clip_frames":[0,300],"pauses_seconds":[[2,4]],"drop_frames":[[180,210]],"split_frames":[150],"settings":{}}. Pauses use timeline seconds; editorial ranges and splits use project frames. Optional settings: split_min_seconds=.5, clean_min_seconds=1.5, split_padding_seconds=.15, clean_after_seconds=.4, clean_before_seconds=.25, coalesce_frames=0. Set coalesce_frames only when nearby cuts can safely be unified.')
    parser.add_argument("input", type=Path, help="Reviewed evidence JSON")
    parser.add_argument("--output", type=Path, help="Write plan JSON instead of stdout")
    args = parser.parse_args()
    try:
        result = build(json.loads(args.input.read_text()))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.error(str(exc))
    content = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(content)
    else:
        print(content, end="")


if __name__ == "__main__":
    main()
