import os
from datetime import datetime, timezone
from typing import Optional

def append_run(
    log_dir: str,
    phase: str,
    agent_name: str,
    task_description: str,
    assigned_by: str,
    thoughts: str,
    result: str,
    produced_files: Optional[list[str]] = None,
) -> str:
    """
    Append one run record to the log file for the given agent and phase.

    Log file path: {log_dir}/{phase}/{agent_name}.md
    Creates the directory and file if they do not exist.
    Returns the absolute path of the log file written.
    """
    # Build log file path
    log_file_dir = os.path.join(log_dir, phase)
    os.makedirs(log_file_dir, exist_ok=True)
    log_file_path = os.path.join(log_file_dir, f"{agent_name}.md")

    # Timestamp in UTC ISO-8601 format
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build produced files section if needed
    produced_files_section = ""
    if produced_files:
        produced_files_section = "\n### Produced Files\n"
        for f in produced_files:
            fname = os.path.basename(f)
            rel_path = os.path.relpath(f, log_dir)
            produced_files_section += f"- [{fname}]({rel_path})\n"

    # Compose log entry
    entry = (
        f"## Run — {timestamp}\n\n"
        f"**Task:** {task_description}\n"
        f"**Assigned by:** {assigned_by}\n\n"
        f"### Thoughts\n{thoughts}\n\n"
        f"### Result\n{result}\n\n"
    )
    if produced_files_section:
        entry += produced_files_section + "\n"
    entry += "---\n"

    # Append to file
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(entry)

    return os.path.abspath(log_file_path)
