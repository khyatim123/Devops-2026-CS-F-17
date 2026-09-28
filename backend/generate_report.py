
from datetime import datetime, timedelta
from pathlib import Path
import os
import subprocess


ROOT = Path(__file__).resolve().parent
REPORTS_DIR = ROOT / "reports"


def run_git(args):
    """Run a Git command and return its output."""
    result = subprocess.run(
        ["git"] + args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True
    )
    return result.stdout.strip()


def escape_markdown(text):
    return text.replace("|", "\\|").replace("\n", " ")


def main():
    now = datetime.now().astimezone()
    start = now - timedelta(days=7)

    build_number = os.getenv("BUILD_NUMBER", "Local")
    build_status = os.getenv("REPORT_BUILD_STATUS", "MANUAL")
    job_name = os.getenv("JOB_NAME", "Local Run")
    build_url = os.getenv("BUILD_URL", "")

    # Exclude earlier automatically generated report commits.
    git_args = [
        "log",
        "--since=7.days",
        "--invert-grep",
        "--grep=Generate weekly progress report",
        "--date=short",
        "--pretty=format:%h%x1f%an%x1f%ad%x1f%s",
    ]

    output = run_git(git_args)
    commits = []

    if output:
        for line in output.splitlines():
            parts = line.split("\x1f", 3)
            if len(parts) == 4:
                commits.append(parts)

    contributors = sorted({commit[1] for commit in commits})

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"weekly-report-{now:%Y-%m-%d}.md"
    report_path = REPORTS_DIR / filename

    lines = [
        "# Weekly Project Progress Report",
        "",
        f"**Project:** Devops-2026-CS-F-17",
        f"**Reporting period:** {start:%Y-%m-%d} to {now:%Y-%m-%d}",
        f"**Generated at:** {now:%Y-%m-%d %H:%M:%S %Z}",
        f"**Jenkins job:** {job_name}",
        f"**Build number:** {build_number}",
        f"**Jenkins build status:** {build_status}",
        "",
        "## 1. Weekly Summary",
        "",
        f"- Repository commits found: {len(commits)}",
        f"- Contributors found in commit history: {len(contributors)}",
        "- Data source: Git commit history from the checked-out branch.",
        "",
        "## 2. Contributors",
        "",
    ]

    if contributors:
        lines.extend(f"- {name}" for name in contributors)
    else:
        lines.append(
            "No qualifying commits were found in the reporting period."
        )

    lines.extend([
        "",
        "## 3. Work Recorded in Git",
        "",
    ])

    if commits:
        lines.extend([
            "| Commit | Author | Date | Commit message |",
            "|---|---|---|---|",
        ])

        for commit_hash, author, date, message in commits:
            lines.append(
                f"| {commit_hash} | {escape_markdown(author)} "
                f"| {date} | {escape_markdown(message)} |"
            )
    else:
        lines.append(
            "No qualifying Git commits were recorded during this period."
        )

    lines.extend([
        "",
        "## 4. Build Information",
        "",
        f"- Status: **{build_status}**",
        f"- Build URL: {build_url if build_url else 'Not available'}",
        "",
        "Note: The Jenkins build status is not a complete test-coverage "
        "or code-quality assessment.",
        "",
        "## 5. Next Week's Plan",
        "",
        "- Review the week's completed commits.",
        "- Record outstanding tasks and blockers.",
        "- Define the next week's project milestones.",
        "",
        "_Planning suggestions only; the team must confirm actual priorities._",
        "",
    ])

    report_path.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print(f"Report generated: {report_path}")
    print(f"Commits recorded: {len(commits)}")
    print(f"Build status: {build_status}")


if __name__ == "__main__":
    main()
