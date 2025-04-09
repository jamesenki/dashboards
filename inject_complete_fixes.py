#!/usr/bin/env python3
"""
Inject complete fixes into IoTSphere templates

This script injects our complete fixes script into the HTML templates
to ensure it loads on both list and details pages.
"""

import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("inject_fixes")

# Constants
TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "frontend", "templates"
)
SCRIPT_TAG = '\n<!-- CRITICAL FIXES: Injects comprehensive fixes for duplication and temperature history issues -->\n<script src="/static/js/complete-fixes.js"></script>\n'


def inject_script_into_template(template_path):
    """Inject script tag into template if not already present"""
    with open(template_path, "r") as f:
        content = f.read()

    # Check if script is already injected
    if "complete-fixes.js" in content:
        logger.info(f"Script already injected in {template_path}")
        return False

    # Find head or body section to inject into
    if "</head>" in content:
        # Inject before end of head section
        content = content.replace("</head>", f"{SCRIPT_TAG}</head>")
    elif "<body" in content:
        # Inject right after body tag
        body_pos = content.find("<body")
        body_end = content.find(">", body_pos)

        if body_end > 0:
            inject_pos = body_end + 1
            content = content[:inject_pos] + SCRIPT_TAG + content[inject_pos:]
    else:
        logger.warning(f"Could not find injection point in {template_path}")
        return False

    # Write back to file
    with open(template_path, "w") as f:
        f.write(content)

    logger.info(f"✅ Injected script into {template_path}")
    return True


def main():
    """Inject script into all relevant templates"""
    logger.info("Injecting complete fixes script into templates")

    if not os.path.exists(TEMPLATE_DIR):
        logger.error(f"Template directory not found: {TEMPLATE_DIR}")
        sys.exit(1)

    # Find all HTML templates
    templates_modified = 0

    for root, _, files in os.walk(TEMPLATE_DIR):
        for file in files:
            if file.endswith(".html"):
                template_path = os.path.join(root, file)
                logger.info(f"Processing {template_path}")

                if inject_script_into_template(template_path):
                    templates_modified += 1

    logger.info(f"Injected script into {templates_modified} templates")

    # Also verify the script is in the static directory
    script_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "frontend",
        "static",
        "js",
        "complete-fixes.js",
    )

    if os.path.exists(script_path):
        logger.info(f"Script file exists at {script_path}")
    else:
        logger.error(f"Script file not found at {script_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
