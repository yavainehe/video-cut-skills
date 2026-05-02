from __future__ import annotations

import argparse
import difflib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


PUNCT_RE = re.compile(r"[\s，。！？、；：,.!?;:\"'“”‘’（）()《》#\-—…`]+")


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("allostasis", "异稳态")
    text = text.replace("allerstasis", "异稳态")
    text = text.replace("petersterling", "petersterling")
    text = PUNCT_RE.sub("", text)
    return text.strip()


def fmt_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    sec = seconds - minutes * 60
    return f"{minutes:02d}:{sec:05.2f}"


def split_script(text: str) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    text = re.sub(r"^#.*$", "", text, flags=re.M)
    paragraphs = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    idx = 1
    for paragraph in paragraphs:
        sentences = [s for s in re.split(r"(?<=[。！？；])", paragraph) if s.strip()]
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            parts = [p.strip() for p in re.split(r"(?<=[，,])", sentence) if p.strip()]
            current = ""
            for part in parts:
                if not current:
                    current = part
                    continue
                if len(normalize(current + part)) <= 34:
                    current += part
                else:
                    units.append({"script_index": idx, "text": current})
                    idx += 1
                    current = part
            if current:
                units.append({"script_index": idx, "text": current})
                idx += 1
    return units


def char_recall(script_norm: str, cand_norm: str) -> float:
    if not script_norm:
        return 0.0
    script_counts = Counter(script_norm)
    cand_counts = Counter(cand_norm)
    hit = sum(min(n, cand_counts.get(ch, 0)) for ch, n in script_counts.items())
    return hit / max(1, sum(script_counts.values()))


def char_precision(script_norm: str, cand_norm: str) -> float:
    if not cand_norm:
        return 0.0
    script_counts = Counter(script_norm)
    cand_counts = Counter(cand_norm)
    hit = sum(min(n, script_counts.get(ch, 0)) for ch, n in cand_counts.items())
    return hit / max(1, sum(cand_counts.values()))


def similarity(script: str, candidate: str) -> dict[str, float]:
    s = normalize(script)
    c = normalize(candidate)
    ratio = difflib.SequenceMatcher(None, s, c).ratio() if s and c else 0.0
    recall = char_recall(s, c)
    precision = char_precision(s, c)
    score = 0.42 * ratio + 0.43 * recall + 0.15 * precision
    return {
        "score": round(score, 4),
        "ratio": round(ratio, 4),
        "recall": round(recall, 4),
        "precision": round(precision, 4),
    }


def load_segments(paths: list[Path]) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    global_index = 0
    for video_order, path in enumerate(paths):
        payload = json.loads(path.read_text())
        video = Path(payload.get("source") or path.stem).name
        for seg_index, seg in enumerate(payload.get("segments", []), start=1):
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", start))
            text = re.sub(r"\s+", "", str(seg.get("text") or ""))
            if not text or end <= start:
                continue
            timeline.append({
                "global_index": global_index,
                "video_order": video_order,
                "video": video,
                "seg_start_index": seg_index,
                "seg_end_index": seg_index,
                "start": start,
                "end": end,
                "whisper_text": text,
            })
            global_index += 1
    return timeline


def make_candidate(timeline: list[dict[str, Any]], start_i: int, end_i: int, max_gap: float) -> dict[str, Any] | None:
    group = timeline[start_i : end_i + 1]
    if not group:
        return None
    if len({g["video"] for g in group}) != 1:
        return None
    for left, right in zip(group, group[1:]):
        if float(right["start"]) - float(left["end"]) > max_gap:
            return None
    start = float(group[0]["start"])
    end = float(group[-1]["end"])
    if end - start > 35:
        return None
    text = "".join(g["whisper_text"] for g in group)
    return {
        "global_start": group[0]["global_index"],
        "global_end": group[-1]["global_index"],
        "video": group[0]["video"],
        "seg_start_index": group[0]["seg_start_index"],
        "seg_end_index": group[-1]["seg_end_index"],
        "start": start,
        "end": end,
        "duration": round(end - start, 3),
        "whisper_text": text,
    }


def select_bottom_up(
    script_units: list[dict[str, Any]],
    timeline: list[dict[str, Any]],
    threshold: float,
    max_group: int,
    max_gap: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected_reversed: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []
    cursor = len(timeline) - 1

    for unit in reversed(script_units):
        if len(normalize(unit["text"])) < 6:
            continue
        best_below_threshold: dict[str, Any] | None = None
        chosen: dict[str, Any] | None = None
        considered = 0

        for end_i in range(cursor, -1, -1):
            for size in range(1, max_group + 1):
                start_i = end_i - size + 1
                if start_i < 0:
                    break
                cand = make_candidate(timeline, start_i, end_i, max_gap)
                if cand is None:
                    continue
                metrics = similarity(unit["text"], cand["whisper_text"])
                item = {**cand, **metrics, "script_index": unit["script_index"], "script_text": unit["text"]}
                considered += 1
                if best_below_threshold is None or item["score"] > best_below_threshold["score"]:
                    best_below_threshold = item
                enough = item["score"] >= threshold and item["recall"] >= 0.55 and item["precision"] >= 0.62
                if enough:
                    if chosen is None:
                        chosen = item
                    else:
                        item_rank = (item["score"], item["recall"], item["precision"], item["global_end"])
                        chosen_rank = (chosen["score"], chosen["recall"], chosen["precision"], chosen["global_end"])
                        if item_rank > chosen_rank:
                            chosen = item
            if considered > 1400:
                break

        if chosen:
            chosen["selection_direction"] = "bottom_up"
            selected_reversed.append(chosen)
            cursor = chosen["global_start"] - 1
        elif best_below_threshold and best_below_threshold["score"] >= 0.46:
            best_below_threshold["selection_direction"] = "bottom_up_review_only"
            review.append(best_below_threshold)

    return list(reversed(selected_reversed)), list(reversed(review))


def write_outputs(selected: list[dict[str, Any]], review: list[dict[str, Any]], out_md: Path, out_json: Path) -> None:
    data = {"selected": selected, "review_only": review}
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    lines: list[str] = []
    lines.append("# Whisper 倒序选段候选（正序展示）")
    lines.append("")
    lines.append("说明：这份清单只用 Whisper segment 作为选段单位；算法从两个新视频的最后面往前找，优先选择后录、相似度足够高的版本；下面按稿件顺序展示，方便你审核。")
    lines.append("")
    lines.append("## 正序拼接清单")
    lines.append("")
    for item in selected:
        if item["seg_start_index"] == item["seg_end_index"]:
            seg = f"seg {item['seg_start_index']}"
        else:
            seg = f"seg {item['seg_start_index']}-{item['seg_end_index']}"
        lines.append(
            f"- {item['video']} {seg} {fmt_time(item['start'])}-{fmt_time(item['end'])} "
            f"score={item['score']:.2f} recall={item['recall']:.2f}"
        )
    lines.append("")
    lines.append("## 逐句审核")
    lines.append("")
    for item in selected:
        lines.append(f"### {item['script_index']}. {item['script_text']}")
        lines.append("")
        lines.append(f"- 推荐片段：`{item['video']}` seg {item['seg_start_index']}-{item['seg_end_index']} `{fmt_time(item['start'])}-{fmt_time(item['end'])}`")
        lines.append(f"- 匹配分数：score `{item['score']:.2f}` / recall `{item['recall']:.2f}` / precision `{item['precision']:.2f}`")
        lines.append(f"- Whisper 文本：{item['whisper_text']}")
        lines.append("")
    if review:
        lines.append("## 低置信度但可能相关")
        lines.append("")
        lines.append("这些没有进入正序拼接清单，只是提示可能需要人工看一下。")
        lines.append("")
        for item in review[:40]:
            lines.append(f"- 稿件 {item['script_index']}：{item['script_text']}")
            lines.append(f"  - 可能片段：`{item['video']}` seg {item['seg_start_index']}-{item['seg_end_index']} `{fmt_time(item['start'])}-{fmt_time(item['end'])}` score `{item['score']:.2f}`")
            lines.append(f"  - Whisper：{item['whisper_text']}")
    out_md.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--transcript", type=Path, action="append", required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.58)
    parser.add_argument("--max-group", type=int, default=5)
    parser.add_argument("--max-gap", type=float, default=2.0)
    args = parser.parse_args()

    script_units = split_script(args.script.read_text())
    timeline = load_segments(args.transcript)
    selected, review = select_bottom_up(script_units, timeline, args.threshold, args.max_group, args.max_gap)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    write_outputs(selected, review, args.out_md, args.out_json)
    print(f"script units: {len(script_units)}")
    print(f"timeline segments: {len(timeline)}")
    print(f"selected: {len(selected)}")
    print(f"review_only: {len(review)}")
    print(f"saved md: {args.out_md}")
    print(f"saved json: {args.out_json}")


if __name__ == "__main__":
    main()
