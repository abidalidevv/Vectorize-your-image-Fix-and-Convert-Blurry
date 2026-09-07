import json
import re
import os
from datetime import datetime

transcript_path = r"C:\Users\Abid\.gemini\antigravity-ide\brain\33b58ac1-16de-49e4-a376-2974737980a9\.system_generated\logs\transcript_full.jsonl"
output_path_repo = r"c:\Users\Abid\Desktop\vector\vectorforge-ai\md\CHAT_TRANSCRIPT.md"
output_path_root = r"c:\Users\Abid\Desktop\vector\CHAT_TRANSCRIPT.md"

def clean_user_prompt(text):
    if not text:
        return ""
    # Extract content inside <USER_REQUEST> if present
    match = re.search(r'<USER_REQUEST>(.*?)</USER_REQUEST>', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Remove system metadata tags
    text = re.sub(r'<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>', '', text, flags=re.DOTALL)
    text = re.sub(r'<SYSTEM_MESSAGE>.*?</SYSTEM_MESSAGE>', '', text, flags=re.DOTALL)
    text = re.sub(r'<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>', '', text, flags=re.DOTALL)
    return text.strip()

records = []
if os.path.exists(transcript_path):
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                records.append(data)
            except Exception:
                continue

md_lines = [
    "# 📜 VectorForge AI — Complete Conversation Transcript & Development Memory",
    "",
    "> **Project**: VectorForge AI (Local Raster-to-Vector Studio)",
    "> **Conversation ID**: `33b58ac1-16de-49e4-a376-2974737980a9`",
    f"> **Exported At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    "> **Author**: [Abid Ali](https://abidalidev.com) • [GitHub (@abidalidevv)](https://github.com/abidalidevv)",
    "",
    "---",
    "",
    "## 🤖 Purpose & Antigravity Future-Maintenance Guide",
    "",
    "This document preserves the **complete conversational memory, debugging steps, architectural discoveries, and design rationale** for VectorForge AI.",
    "If you are an AI assistant (Google Antigravity, Claude, or any LLM) resuming development on this project months or years later, **read this section first** before modifying code:",
    "",
    "### 🔑 Key Architectural Discoveries & Core Rules",
    "1. **Cutout vs. Stacked Hierarchy (`vtracer_engine.py`)**:",
    "   - In `stacked` mode, VTracer fills outer shapes as solid polygons and stacks inner shapes on top. Curve fitting mismatches cause giant background wedges (e.g. dark brown wedges under triangles) and layer bleed.",
    "   - In `cutout` mode, all shapes are non-overlapping planar paths (adjacent puzzle pieces). Outlines and borders are traced cleanly without underlying ghost polygons.",
    "   - Sub-pixel antialiasing edge seams in cutout mode are eliminated by inserting an opaque `<rect width=\"100%\" height=\"100%\" fill=\"{bg_color}\"/>` matching the dominant background of opaque images.",
    "",
    "2. **Connected-Component Anti-Alias Filtering (`MAX_ANTIALIAS_COMPONENT_PX = 40`)**:",
    "   - Simple percentage-based color merging (`pct < 0.7%`) fails on thin strokes because their total pixel count is low, causing legitimate outlines (like dark brown borders) to be merged into nearby fills.",
    "   - Using `cv2.connectedComponentsWithStats` allows checking `max_component_size`. Isolated anti-alias blend noise (tiny disconnected clusters < 40px at corner intersections) is merged, while long continuous thin outlines are preserved.",
    "",
    "3. **Primitive Detector Axis-Specific Line Deduplication (`primitive_detector.py`)**:",
    "   - Horizontal lines must be deduplicated across Y coordinates (`[1]` and `[3]`), while vertical lines must be deduplicated across X coordinates (`[0]` and `[2]`). Checking the wrong axis previously split horizontal lines in circles into two pieces.",
    "",
    "4. **AI Models & Offline Weights (`backend/app/weights/`)**:",
    "   - VectorForge AI runs 100% offline. Heavy weights (`.onnx`, `.pth`) are gitignored.",
    "   - 1-click batch downloader: `download_models.bat` (Windows) and `download_models.sh` (Linux/Mac).",
    "   - Models include: YuNet (face detection), GFPGAN v1.4 (face restoration), LaMa FP32 (Magic Eraser inpainting), Real-ESRGAN x4v3 & x4plus (Image Enhancer), BiRefNet & IS-Net (Background Remover).",
    "",
    "5. **Running Dev Servers & Tests**:",
    "   - Backend: `cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`",
    "   - Frontend: `cd frontend && npm run dev`",
    "   - Unit Tests: `pytest tests/test_vectorforge.py -v` (23/23 tests passing)",
    "",
    "---",
    "",
    "## 📑 Chronological Conversation Turns",
    ""
]

step_count = 0
for entry in records:
    entry_type = entry.get("type")
    source = entry.get("source")
    content = entry.get("content", "")
    created_at = entry.get("created_at", "")
    tool_calls = entry.get("tool_calls", [])

    if entry_type == "USER_INPUT":
        step_count += 1
        cleaned = clean_user_prompt(content)
        if not cleaned:
            cleaned = content.strip()
        md_lines.append(f"## 👤 User (Turn #{step_count})")
        if created_at:
            md_lines.append(f"*Timestamp: {created_at}*")
        md_lines.append("")
        md_lines.append(cleaned)
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    elif entry_type == "PLANNER_RESPONSE":
        has_content = bool(content and content.strip())
        has_tools = bool(tool_calls and len(tool_calls) > 0)
        
        if has_content:
            md_lines.append("## 🤖 Assistant (Antigravity)")
            if created_at:
                md_lines.append(f"*Timestamp: {created_at}*")
            md_lines.append("")
            md_lines.append(content.strip())
            md_lines.append("")
            md_lines.append("---")
            md_lines.append("")
        elif has_tools:
            # Short summary of tool actions
            actions = []
            for tc in tool_calls:
                name = tc.get("name", "tool")
                args = tc.get("args", {})
                action_summary = args.get("toolSummary") or args.get("toolAction") or name
                actions.append(f"`{name}`: {action_summary}")
            if actions:
                md_lines.append(f"> 🛠️ **System Action**: {', '.join(actions)}")
                md_lines.append("")

final_md = "\n".join(md_lines)

for p in [output_path_repo, output_path_root]:
    with open(p, "w", encoding="utf-8") as f:
        f.write(final_md)

print(f"Exported transcript successfully to:")
print(f"1. {output_path_repo}")
print(f"2. {output_path_root}")
