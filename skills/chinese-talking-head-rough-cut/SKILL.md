---
name: chinese-talking-head-rough-cut
description: Chinese talking-head rough-cut workflow for creators who repeatedly re-record lines and want AI-assisted cleanup before final editing. Use when Codex needs to process Chinese monologue videos, compare local transcripts against a written script, select the last usable repetition from Whisper segments, produce an audit Markdown/JSON candidate list, or prepare reviewable EDL-style rough cuts without modifying original media.
---

# Chinese Talking-Head Rough Cut

## Goal

Use this skill for Chinese knowledge, medical, education, or solo camera monologue footage where the creator repeats the same sentence many times and the last fluent take is usually the keeper.

The first output should usually be an audit list, not a rendered video. Keep the workflow small, reversible, and review-first.

## Core Rule

Use Whisper segments as the editing unit.

- Select from the bottom of the timeline toward the top, because later repetitions are usually better.
- After selecting, present and render in normal top-to-bottom order.
- Use FunASR only as a text reference when available; do not let FunASR boundaries decide cuts.
- Do not delete, overwrite, or move original media.
- Put generated files under an `edit/`, `outputs/`, or similarly named output folder.

## Recommended Workflow

1. Confirm the input folder, script file, and output folder.
2. Transcribe each video locally when possible. Prefer a FunASR plus Whisper pipeline:
   - FunASR: better Chinese text reference and punctuation.
   - Whisper: better segment boundaries for this workflow.
3. Generate a Whisper segment review table before cutting video.
4. Match the written script against Whisper segments from bottom to top.
5. Output a reviewable Markdown and JSON candidate list.
6. Ask the user to approve or correct candidates.
7. Only after approval, build an EDL and render preview/final video.

## Matching Heuristics

When matching script to video:

- Split Chinese script into natural units: full sentence first, then comma-level half-sentences when necessary.
- Ignore very short script units unless the user explicitly asks for them.
- Search later-to-earlier, but output selected clips in script order.
- Allow adjacent Whisper segments to merge only when their time gap is small.
- Penalize candidates that contain too much unrelated next-sentence text.
- Treat low-confidence matches as `review_only`; do not include them in the official cut list.
- When the user has not provided later source videos, do not try to match later script sections.

## Script

Use `scripts/select_whisper_bottom_up.py` to produce the review list from existing transcript JSON files.

Example:

```bash
python scripts/select_whisper_bottom_up.py \
  --script samples/script.md \
  --transcript samples/edit/transcripts/FragmentVideo_001.json \
  --transcript samples/edit/transcripts/FragmentVideo_002.json \
  --out-md samples/edit/whisper_bottom_up_candidates.md \
  --out-json samples/edit/whisper_bottom_up_candidates.json \
  --threshold 0.58 \
  --max-group 5 \
  --max-gap 2.0
```

Expected outputs:

- `whisper_bottom_up_candidates.md`: human-readable review list in script order.
- `whisper_bottom_up_candidates.json`: structured candidate data for later EDL generation.

## Rendering Guidance

Do not render automatically unless the user asks for it.

When rendering later:

- Keep original files unchanged.
- Add a small safety pad around accepted segments if clips cut off final syllables.
- Do not add automatic fade-in/fade-out for Chinese speech unless the user requests it.
- Do not use English-style uppercase two-word subtitle chunks.
- For Chinese subtitles, use natural semantic short phrases.

## References

Read `references/current-findings.md` when you need the reasoning behind this workflow, known failure modes, or the current tested assumptions.
