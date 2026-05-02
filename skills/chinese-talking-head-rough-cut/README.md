# Chinese Talking-Head Rough Cut

This skill helps with rough-cut editing for Chinese solo talking-head videos, especially when the speaker repeatedly records the same sentence until the last version is the smoothest.

It is designed for creators who want AI to clean up spoken drafts, not to make complex cinematic edits.

## What It Does

The workflow:

1. Transcribe each source video.
2. Use Whisper's original segments as the candidate editing units.
3. Compare those segments with the creator's written script.
4. Search from the end of the footage backward, because later repeated takes are usually better.
5. Save the chosen segments back in normal script order.
6. Output a Markdown review list before any video is rendered.

This lets a human check the selected takes before generating an EDL or final video.

## Why Search From Back To Front

In this recording style, the speaker may say sentence A, move to sentence B, then decide A was not good and re-record A and B again. A normal top-to-bottom search often keeps an early failed attempt.

This skill assumes:

- repeated material later in the same batch is usually closer to the final intended delivery;
- the selected clips must still be arranged in normal script order;
- uncertain matches should be shown for review, not silently used.

## Whisper And FunASR Roles

Current tested rule:

- Whisper is used for segment boundaries and candidate selection.
- FunASR can be used as a Chinese text reference.
- FunASR should not decide cut boundaries in this workflow.

This is because the tested videos showed that Whisper's raw segments matched the user's manual review better, while FunASR could be useful for reading Chinese text but sometimes created boundary or timestamp problems.

## Included Script

`scripts/select_whisper_bottom_up.py` reads:

- a written script Markdown file;
- one or more transcript JSON files containing Whisper-style `segments`;
- output paths for a Markdown and JSON report.

Example:

```bash
python scripts/select_whisper_bottom_up.py \
  --script samples/script.md \
  --transcript samples/edit/transcripts/FragmentVideo_001.json \
  --transcript samples/edit/transcripts/FragmentVideo_002.json \
  --out-md samples/edit/whisper_bottom_up_candidates.md \
  --out-json samples/edit/whisper_bottom_up_candidates.json
```

Useful options:

- `--threshold`: similarity threshold for accepted matches. Default: `0.58`.
- `--max-group`: maximum adjacent Whisper segments to merge into one candidate. Default: `5`.
- `--max-gap`: maximum allowed gap in seconds between merged segments. Default: `2.0`.

## Output

The Markdown report contains:

- a normal-order stitching list;
- one section per selected script unit;
- the source video name;
- Whisper segment number or range;
- start and end time;
- score, recall, and precision;
- Whisper text for manual checking;
- low-confidence related clips in a review-only section.

The JSON report stores the same information for later conversion into an EDL.

## Current Limitations

This is still an experimental rough-cut workflow.

- It does not guarantee perfect semantic understanding.
- It may miss words when Whisper text is imperfect.
- It may need manual correction when a line is split awkwardly.
- It should not render or delete anything without user approval.
- It should not match script sections whose source videos have not been provided.

## Safe Usage Rules

- Never modify original source videos.
- Put all generated files under an output folder such as `edit/`.
- Generate review candidates before rendering.
- Ask the creator to approve or correct the list.
- Avoid automatic fades for Chinese speech unless requested.
- Use Chinese-friendly subtitle grouping, not uppercase English two-word chunks.
