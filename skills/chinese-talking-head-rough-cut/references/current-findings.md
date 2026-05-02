# Current Findings

These notes summarize the tested assumptions behind this skill.

## Tested Scenario

The workflow was tested on Chinese medical/knowledge talking-head videos where the speaker repeatedly re-records sentences. The user's manual selections were made from Whisper segments, and the best automated attempt also used Whisper segments as the selection unit.

## What Worked

- Searching from the bottom of the video upward matched the user's habit of keeping the last fluent version.
- Returning the selected segments in normal script order made the review list readable.
- Whisper raw segment boundaries were more useful for choosing clips than earlier semantic-block experiments.
- A Markdown review list was more useful than directly rendering a video, because the user could quickly approve or correct individual selections.

## What Did Not Work Well

- Directly deleting pauses did not produce good semantic cuts.
- Matching full script sentences was sometimes too rigid; comma-level half-sentences worked better when sentences were long.
- FunASR text was useful, but relying on FunASR boundaries could create poor cuts.
- Automatic fades made Chinese speech cuts less desirable.
- English subtitle assumptions such as uppercase two-word chunks are not suitable for Chinese.

## Current Practical Rules

- Use Whisper segments as the atomic selection unit.
- Use bottom-up search for candidate selection.
- Output selected clips in script order.
- Keep low-confidence matches in a review-only section.
- Use small gap limits when merging adjacent Whisper segments.
- Avoid over-merging candidates that include the start of the next sentence.
- Ask for human approval before rendering.

## Suggested Later Improvements

- Add an optional script range, such as `--script-start 27 --script-end 40`, to avoid matching parts whose videos have not been provided.
- Add an EDL generator that consumes approved JSON candidates.
- Add optional safety padding for render time, such as a small start pad and a slightly larger end pad.
- Add Chinese subtitle grouping by natural phrase length and punctuation.
