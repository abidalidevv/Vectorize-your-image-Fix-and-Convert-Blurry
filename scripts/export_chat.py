import json
import re
import os
from datetime import datetime

transcript_path = r"C:\Users\Abid\.gemini\antigravity-ide\brain\33b58ac1-16de-49e4-a376-2974737980a9\.system_generated\logs\transcript_full.jsonl"
output_path_repo = r"c:\Users\Abid\Desktop\vector\vectorforge-ai\CHAT_TRANSCRIPT.md"
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
    "# 📜 VectorForge AI — Complete Conversation Transcript",
    "",
    "> **Project**: VectorForge AI (Local Raster-to-Vector Studio)",
    "> **Conversation ID**: `33b58ac1-16de-49e4-a376-2974737980a9`",
    f"> **Exported At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    "",
    "---",
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
