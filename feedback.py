from typing import Dict, Any, List


def _summarize_errors(errors: List[Dict[str, Any]], max_items: int = 8) -> str:
    lines = []
    for e in errors[:max_items]:
        scope = e.get("entity") or e.get("file") or ""
        t = e.get("type", "issue")
        msg = e.get("message", "")
        if scope:
            lines.append(f"• [{t}] {scope}: {msg}")
        else:
            lines.append(f"• [{t}] {msg}")
    remaining = len(errors) - len(lines)
    if remaining > 0:
        lines.append(f"… and {remaining} more")
    return "\n".join(lines)


def process_report(report: Dict[str, Any], conversation_history: list, spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns:
      - {"next_action": "deliver", "message": "ok"}                         # everything fine
      - {"next_action": "ask_user", "message": "...human-readable..."}     # ask user what to do next
      - {"next_action": "auto_fix", "message": "attempting fix"}           # suggest auto regeneration
    """
    if not report or report.get("status") == "ok":
        return {"next_action": "deliver", "message": "ok"}

    errors = report.get("errors", [])
    summary = _summarize_errors(errors)

    # Simple heuristic: if most errors are "logic" (missing attrs/templates), try auto-fix (regen)
    logic_count = sum(1 for e in errors if e.get("type") == "logic")
    if logic_count >= len(errors) and len(errors) > 0:
        return {
            "next_action": "auto_fix",
            "message": "I found logical issues that might be fixed by regenerating templates. Attempting auto-fix…\n\n" + summary
        }

    # Otherwise ask the user (or route back to interpreter in outer flow)
    return {
        "next_action": "ask_user",
        "message": (
            "I found issues during validation:\n\n"
            f"{summary}\n\n"
            "Would you like me to refine the specification (ask follow-up questions) or try to regenerate the module?"
        ),
    }