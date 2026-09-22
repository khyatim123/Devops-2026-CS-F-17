
from datetime import datetime
import os

build_number = os.getenv("BUILD_NUMBER", "Local")
build_status = os.getenv("BUILD_STATUS", "SUCCESS")

feedback = f"""WEEKLY PROGRESS FEEDBACK
=========================
Project: Devops-2026-CS-F-17
Build Number: {build_number}
Build Status: {build_status}
Generated At: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Feedback:
The weekly Jenkins build was completed successfully.
The project is being monitored through continuous integration.
"""

with open("feedback.txt", "w", encoding="utf-8") as file:
    file.write(feedback)

print("Weekly feedback file generated successfully.")
