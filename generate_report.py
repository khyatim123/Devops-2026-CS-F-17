import subprocess
from collections import defaultdict, Counter
import datetime
import io
import sys
import html
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER


# ============================================================
# 1. CONFIGURATION
# ============================================================

COLLEGE_NAME = (
    "Swami Keshvanand Institute of Technology, "
    "Management & Gramothan, Jaipur"
)

DEPARTMENT_NAME = "Department of Computer Science & Engineering"

# Use this dictionary if one contributor uses multiple Git names.
# Example:
# AUTHOR_ALIASES = {
#     "Khyati": "Khyati Mishra",
#     "Khyati Mishra": "Khyati Mishra"
# }
AUTHOR_ALIASES = {}

MAX_COMMIT_LOGS = 250


# ============================================================
# 2. GIT UTILITIES
# ============================================================

def run_git(args, check=True):
    """Execute a Git command and return its result."""

    result = subprocess.run(
        ["git"] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False
    )

    if check and result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
            or f"Git command failed: {' '.join(args)}"
        )

    return result


def get_repo_info():
    """Get repository name, root, branch and remote URL."""

    root = Path(
        run_git(["rev-parse", "--show-toplevel"]).stdout.strip()
    ).resolve()

    branch = run_git(
        ["branch", "--show-current"],
        check=False
    ).stdout.strip()

    if not branch:
        branch = "detached HEAD"

    remote = run_git(
        ["config", "--get", "remote.origin.url"],
        check=False
    ).stdout.strip()

    repo_name = root.name

    if remote:
        repo_name = (
            remote.rstrip("/")
            .split("/")[-1]
            .removesuffix(".git")
        ) or repo_name

    return root, repo_name, branch, remote


# ============================================================
# 3. COLLECT GIT METRICS
# ============================================================

def collect_git_metrics(interval="monthly"):
    """
    Collect commit history, contributor statistics,
    lines added/deleted and activity timeline.

    Supported intervals: weekly, monthly, final
    """

    today = datetime.date.today()

    git_args = [
        "log",
        "--no-merges",
        "--pretty=format:COMMIT%x1f%h%x1f%an%x1f%ad%x1f%s",
        "--date=short",
        "--numstat"
    ]

    if interval == "weekly":
        since_date = (
            today - datetime.timedelta(days=7)
        ).strftime("%Y-%m-%d")

        git_args.append(f"--since={since_date}")
        scope_title = f"Last 7 Days (Since {since_date})"

    elif interval == "monthly":
        since_date = (
            today - datetime.timedelta(days=30)
        ).strftime("%Y-%m-%d")

        git_args.append(f"--since={since_date}")
        scope_title = f"Last 30 Days (Since {since_date})"

    else:
        scope_title = "Complete Available Project Git History"

    raw_output = run_git(git_args).stdout

    contributors = defaultdict(
        lambda: {
            "commits": 0,
            "added": 0,
            "deleted": 0,
            "active_days": set()
        }
    )

    timeline = defaultdict(Counter)
    all_commits = []
    current_author = None

    for line in raw_output.splitlines():

        if line.startswith("COMMIT\x1f"):

            parts = line.split("\x1f", 4)

            if len(parts) < 5:
                current_author = None
                continue

            _, sha, author, date_str, message = parts

            # Exclude automated bot activity.
            if (
                "bot" in author.lower()
                or "github-actions" in author.lower()
            ):
                current_author = None
                continue

            current_author = AUTHOR_ALIASES.get(author, author)

            try:
                commit_date = datetime.datetime.strptime(
                    date_str, "%Y-%m-%d"
                ).date()
            except ValueError:
                commit_date = None

            contributors[current_author]["commits"] += 1
            contributors[current_author]["active_days"].add(date_str)

            all_commits.append(
                (date_str, sha, current_author, message)
            )

            if commit_date:

                if interval == "weekly":
                    period = commit_date.strftime("%a (%b %d)")
                elif interval == "monthly":
                    period = commit_date.strftime("%Y-%m-%d")
                else:
                    period = commit_date.strftime("%Y-%m")

                timeline[period][current_author] += 1

        elif current_author:

            # Git --numstat output:
            # added<TAB>deleted<TAB>filename
            parts = line.split("\t")

            if (
                len(parts) >= 3
                and parts[0].isdigit()
                and parts[1].isdigit()
            ):
                contributors[current_author]["added"] += int(parts[0])
                contributors[current_author]["deleted"] += int(parts[1])

    all_commits.sort(
        key=lambda item: (item[0], item[1]),
        reverse=True
    )

    return contributors, timeline, scope_title, all_commits


# ============================================================
# 4. CREATE CHARTS
# ============================================================

def create_charts(contributors, timeline, interval):
    """Create commit activity and net line-change charts."""

    figure, axes = plt.subplots(
        1, 2, figsize=(10.5, 3.5)
    )

    timeline_axis, lines_axis = axes

    authors = list(contributors.keys())
    periods = sorted(timeline.keys())

    # Chart 1: Commit activity
    if periods and authors:

        for author in authors:

            counts = [
                timeline[period].get(author, 0)
                for period in periods
            ]

            timeline_axis.plot(
                periods,
                counts,
                marker="o",
                linewidth=1.7,
                label=author
            )

        timeline_axis.set_title(
            f"Commit Activity ({interval.capitalize()})"
        )

        timeline_axis.set_ylabel("Commits")

        timeline_axis.tick_params(
            axis="x",
            rotation=45,
            labelsize=7
        )

        timeline_axis.grid(
            True,
            linestyle="--",
            alpha=0.35
        )

        timeline_axis.legend(fontsize=7)

    else:

        timeline_axis.text(
            0.5, 0.5,
            "No commits in selected period",
            ha="center",
            va="center"
        )

        timeline_axis.set_axis_off()

    # Chart 2: Net lines changed by contributor
    if authors:

        net_lines = [
            contributors[author]["added"]
            - contributors[author]["deleted"]
            for author in authors
        ]

        lines_axis.bar(authors, net_lines)

        lines_axis.set_title("Net Line Changes")

        lines_axis.set_ylabel(
            "Lines Added Minus Lines Deleted"
        )

        lines_axis.tick_params(
            axis="x",
            rotation=30,
            labelsize=7
        )

        lines_axis.grid(
            axis="y",
            linestyle="--",
            alpha=0.35
        )

    else:

        lines_axis.text(
            0.5, 0.5,
            "No line-change data",
            ha="center",
            va="center"
        )

        lines_axis.set_axis_off()

    figure.tight_layout()

    image_buffer = io.BytesIO()

    figure.savefig(
        image_buffer,
        format="png",
        dpi=170,
        bbox_inches="tight"
    )

    plt.close(figure)
    image_buffer.seek(0)

    return Image(
        image_buffer,
        width=500,
        height=165
    )


# ============================================================
# 5. PDF FORMATTING HELPERS
# ============================================================

def add_page_number(canvas, doc):
    """Add footer and page number to each page."""

    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748B"))

    canvas.drawString(
        36, 18,
        "Project report - generated from repository evidence"
    )

    canvas.drawRightString(
        letter[0] - 36,
        18,
        f"Page {doc.page}"
    )

    canvas.restoreState()


def build_styles():

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            "CollegeCustom",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=16,
            textColor=colors.HexColor("#0F172A"),
            alignment=TA_CENTER,
            spaceAfter=2
        )
    )

    styles.add(
        ParagraphStyle(
            "DeptCustom",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569"),
            alignment=TA_CENTER,
            spaceAfter=7
        )
    )

    styles.add(
        ParagraphStyle(
            "ReportTitleCustom",
            parent=styles["Heading2"],
            fontSize=15,
            leading=19,
            textColor=colors.HexColor("#1D4ED8"),
            alignment=TA_CENTER,
            spaceAfter=8
        )
    )

    styles.add(
        ParagraphStyle(
            "SectionCustom",
            parent=styles["Heading2"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=8,
            spaceAfter=5
        )
    )

    styles.add(
        ParagraphStyle(
            "SmallCustom",
            parent=styles["Normal"],
            fontSize=7.8,
            leading=10,
            textColor=colors.HexColor("#334155")
        )
    )

    styles.add(
        ParagraphStyle(
            "TinyCustom",
            parent=styles["Normal"],
            fontSize=7,
            leading=8.5,
            textColor=colors.HexColor("#334155")
        )
    )

    return styles


def make_table(data, widths, header=True, font_size=7.5):

    table = Table(
        data,
        colWidths=widths,
        repeatRows=1 if header else 0,
        hAlign="LEFT"
    )

    commands = [
        ("GRID", (0, 0), (-1, -1), 0.4,
         colors.HexColor("#CBD5E1")),

        ("VALIGN", (0, 0), (-1, -1), "TOP"),

        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),

        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),

        ("FONTSIZE", (0, 0), (-1, -1), font_size)
    ]

    if header and data:

        commands.extend([
            (
                "BACKGROUND", (0, 0), (-1, 0),
                colors.HexColor("#1E293B")
            ),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")
        ])

        if len(data) > 1:
            commands.append(
                (
                    "ROWBACKGROUNDS",
                    (0, 1), (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F8FAFC")
                    ]
                )
            )

    table.setStyle(TableStyle(commands))

    return table


# ============================================================
# 6. GENERATE THE PDF REPORT
# ============================================================

def generate_pdf(interval="monthly"):

    if interval not in {"weekly", "monthly", "final"}:
        raise ValueError(
            "Choose report type: weekly, monthly, or final"
        )

    root, repo_name, branch_name, remote_url = get_repo_info()

    (
        contributors,
        timeline,
        scope_title,
        all_commits
    ) = collect_git_metrics(interval)

    date_stamp = datetime.date.today().strftime("%Y-%m-%d")

    if interval == "monthly":

        report_title = "Monthly Progress Report"

        filename = (
            f"{repo_name}_Monthly_Progress_Report_"
            f"{date_stamp}.pdf"
        )

    elif interval == "weekly":

        report_title = "Weekly Progress Report"

        filename = (
            f"{repo_name}_Weekly_Progress_Report_"
            f"{date_stamp}.pdf"
        )

    else:

        report_title = "Final Project Report"

        filename = (
            f"{repo_name}_Final_Project_Report_"
            f"{date_stamp}.pdf"
        )

    styles = build_styles()

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=32,
        bottomMargin=32
    )

    story = []

    # --------------------------------------------------------
    # REPORT HEADER
    # --------------------------------------------------------

    story.append(
        Paragraph(
            html.escape(COLLEGE_NAME),
            styles["CollegeCustom"]
        )
    )

    story.append(
        Paragraph(
            html.escape(DEPARTMENT_NAME),
            styles["DeptCustom"]
        )
    )

    story.append(
        Paragraph(
            f"<b>{html.escape(report_title)}</b>",
            styles["ReportTitleCustom"]
        )
    )

    story.append(
        Paragraph(
            f"<b>Repository:</b> {html.escape(repo_name)}"
            f"&nbsp;&nbsp; <b>Branch:</b> "
            f"{html.escape(branch_name)}<br/>"
            f"<b>Generated:</b> {date_stamp}<br/>"
            f"<b>Scope:</b> {html.escape(scope_title)}",
            styles["Normal"]
        )
    )

    if remote_url:

        story.append(
            Paragraph(
                f"<b>Remote repository:</b> "
                f"{html.escape(remote_url)}",
                styles["SmallCustom"]
            )
        )

    story.append(Spacer(1, 8))

    # --------------------------------------------------------
    # CALCULATE TOTALS
    # --------------------------------------------------------

    total_commits = sum(
        data["commits"]
        for data in contributors.values()
    )

    total_added = sum(
        data["added"]
        for data in contributors.values()
    )

    total_deleted = sum(
        data["deleted"]
        for data in contributors.values()
    )

    # ========================================================
    # SECTION 1: INDIVIDUAL CONTRIBUTION
    # ========================================================

    story.append(
        Paragraph(
            "1. Individual Contribution",
            styles["SectionCustom"]
        )
    )

    table_data = [[
        "Contributor",
        "Commits",
        "Lines Added",
        "Lines Deleted",
        "Net LOC",
        "Active Days"
    ]]

    if contributors:

        for name, data in sorted(
            contributors.items(),
            key=lambda item: (
                -item[1]["commits"],
                item[0].lower()
            )
        ):

            net_lines = data["added"] - data["deleted"]

            table_data.append([
                Paragraph(
                    html.escape(name),
                    styles["TinyCustom"]
                ),
                str(data["commits"]),
                f"{data['added']:,}",
                f"{data['deleted']:,}",
                f"{net_lines:,}",
                str(len(data["active_days"]))
            ])

    else:

        table_data.append([
            "No commits found", "-", "-", "-", "-", "-"
        ])

    story.append(
        make_table(
            table_data,
            [135, 50, 70, 75, 65, 65],
            font_size=7
        )
    )

    story.append(Spacer(1, 5))

    story.append(
        Paragraph(
            f"<b>Total commits:</b> {total_commits} &nbsp; "
            f"<b>Added:</b> {total_added:,} &nbsp; "
            f"<b>Deleted:</b> {total_deleted:,} &nbsp; "
            f"<b>Net:</b> {total_added - total_deleted:,}",
            styles["SmallCustom"]
        )
    )

    # ========================================================
    # SECTION 2: VISUAL TRENDS
    # ========================================================

    story.append(
        Paragraph(
            "2. Visual Trends",
            styles["SectionCustom"]
        )
    )

    story.append(
        create_charts(
            contributors,
            timeline,
            interval
        )
    )

    # ========================================================
    # SECTION 3: DETAILED COMMIT LOGS
    # ========================================================

    if interval == "monthly":
        log_heading = "3. Detailed Commit Logs (Monthly)"
    elif interval == "weekly":
        log_heading = "3. Detailed Commit Logs (Weekly)"
    else:
        log_heading = "3. Detailed Commit Logs (Final)"

    story.append(
        Paragraph(
            log_heading,
            styles["SectionCustom"]
        )
    )

    log_rows = [[
        "Date",
        "Hash",
        "Author",
        "Commit Message"
    ]]

    sorted_commits = sorted(
        all_commits,
        key=lambda item: (item[0], item[1]),
        reverse=True
    )[:MAX_COMMIT_LOGS]

    for date_val, sha, author, message in sorted_commits:

        log_rows.append([
            Paragraph(
                html.escape(date_val),
                styles["TinyCustom"]
            ),
            Paragraph(
                html.escape(sha),
                styles["TinyCustom"]
            ),
            Paragraph(
                html.escape(author),
                styles["TinyCustom"]
            ),
            Paragraph(
                html.escape(message),
                styles["TinyCustom"]
            )
        ])

    if not sorted_commits:
        log_rows.append([
            "No commits found in this period", "", "", ""
        ])

    story.append(
        make_table(
            log_rows,
            [65, 48, 105, 300],
            font_size=6.5
        )
    )

    # ========================================================
    # BUILD THE PDF
    # ========================================================

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number
    )

    print("\n[SUCCESS] Report generated successfully.")
    print(f"File: {Path(filename).resolve()}")
    print(f"Report type: {interval}")
    print(f"Contributors: {len(contributors)}")
    print(f"Total commits: {total_commits}")


# ============================================================
# 7. MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    chosen_interval = (
        sys.argv[1].lower()
        if len(sys.argv) > 1
        else "monthly"
    )

    try:
        generate_pdf(chosen_interval)

    except (RuntimeError, ValueError) as error:
        print(f"\n[ERROR] {error}")
        print(
            "Check that Git is working and that you are "
            "running this script inside the project repository."
        )
        sys.exit(1)