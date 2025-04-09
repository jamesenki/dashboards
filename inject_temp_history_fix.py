#!/usr/bin/env python3
"""
Temperature Chart Fix Injector
"""
import os

from bs4 import BeautifulSoup


def inject_fix_script():
    template_file = "frontend/templates/water-heater/detail.html"

    # Read template file
    with open(template_file, "r") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Check if fix is already injected
    scripts = soup.find_all("script")
    for script in scripts:
        if script.get("src") and "temperature-history-direct-fix.js" in script["src"]:
            print("Fix script already injected")
            return

    # Find last script tag in head
    head = soup.find("head")
    if not head:
        print("No head tag found in template")
        return

    # Create new script tag
    new_script = soup.new_tag("script")
    new_script[
        "src"
    ] = "/static/js/temperature-history-direct-fix.js?v={{{{now.timestamp()}}}}"

    # Add comment before script
    comment = soup.new_tag("comment")
    comment.string = " DIRECT FIX: Temperature chart display "

    # Insert at end of head
    head.append(comment)
    head.append(new_script)

    # Write updated template
    with open(template_file, "w") as f:
        f.write(str(soup))

    print("Successfully injected temperature history fix")


if __name__ == "__main__":
    inject_fix_script()
