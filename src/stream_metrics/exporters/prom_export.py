from __future__ import annotations

def format_prometheus(summary: dict) -> str:
    lines = []
    for k, v in summary.items():
        if v is None:
            continue
        metric = f"stream_{k}".replace(".", "_")
        lines.append(f"# TYPE {metric} gauge")
        lines.append(f"{metric} {v}")
    return "\n".join(lines) + "\n"
