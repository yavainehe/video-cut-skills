Video Cut Skills / 视频剪辑 Skills
This repository stores reusable Codex skills for video editing workflows.

这个仓库用于保存可复用的 Codex 视频剪辑技能。

Included Skills / 已包含的 Skill
Chinese Talking-Head Rough Cut / 中文口播粗剪
Path / 路径：

skills/chinese-talking-head-rough-cut

This skill is for Chinese solo talking-head videos, especially knowledge, education, and medical explainers where the speaker repeatedly records the same sentence until the final version is smoother.

这个 skill 面向中文单人口播视频，尤其适合知识类、教育类、医学科普类内容。它针对的典型场景是：创作者会反复录同一句或同一段，通常最后一版更顺、更接近成片。

What It Does / 它做什么
The workflow is review-first:

它的流程是“先审核，再剪辑”：

Transcribe source videos. 转录原始视频。
Use Whisper's original segments as the editing unit. 使用 Whisper 原始 segment 作为选段单位。
Compare the transcript with the written script. 把视频转录文本和原始文字稿进行比对。
Search from the end of the footage backward, because the last repeated take is often the best one. 从视频后面往前找，因为重复录制时，最后一遍往往是更顺的版本。
Return selected clips in normal script order. 选完后再按文字稿正序排列。
Generate a Markdown/JSON review list before rendering any video. 在真正生成视频前，先输出 Markdown/JSON 审核清单。
Why This Exists / 为什么需要它
Normal pause removal is not enough for this kind of footage. The main problem is not only silence; it is repeated attempts, false starts, partial sentences, and re-recorded lines.

这类视频不能只靠“删除停顿”来粗剪。真正的问题不只是静音，而是反复重录、说一半放弃、口误、残句、重复句，以及后面重新录了一版更完整的表达。

This workflow tries to identify the last usable version of each script unit, while keeping the creator in control before any final video is generated.

这个流程的目标是：帮创作者找到每个稿件片段最后一个可用版本，但在生成最终视频前，仍然保留人工审核和确认。

Current Status / 当前状态
Experimental but promising.

目前仍是实验阶段，但方向已经验证可行。

Tested so far:

已经测试出的结论：

Whisper segments worked better than FunASR boundaries for selecting clips. 用 Whisper segment 做选段单位，比用 FunASR 边界更适合这个任务。
FunASR can still be useful as a Chinese text reference. FunASR 仍然可以作为中文文本参考。
Bottom-up selection matched the creator's manual review style better than top-down matching. 从后往前选，比从前往后选更符合反复重录的口播习惯。
Markdown review output is more useful than immediately rendering a video. 先输出 Markdown 审核清单，比直接生成视频更适合调试和人工确认。
Safety Rules / 安全规则
Do not modify original videos. 不修改原始视频。
Put generated files under an output folder such as edit/. 所有生成文件放在 edit/ 等输出目录里。
Generate review candidates before rendering. 先生成审核候选，再渲染视频。
Ask for human approval before creating the final EDL or video. 生成最终 EDL 或视频前，需要人工确认。
Avoid automatic fades unless requested. 不默认添加自动淡入淡出。
Use Chinese-friendly subtitles, not uppercase English two-word chunks. 中文字幕应按中文自然语义分组，不使用英文两词一组、全部大写的字幕样式。
