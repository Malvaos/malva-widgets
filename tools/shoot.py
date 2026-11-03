#!/usr/bin/env python3
"""Renders every page of the kit to screenshots/<name>-light.png and -dark.png.

    python3 tools/shoot.py            # all pages
    python3 tools/shoot.py dialogs    # one page

Needs slint-viewer (https://slint.dev). Point SLINT_VIEWER at the binary if it is not on PATH.
"""
import os, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VIEWER = os.environ.get("SLINT_VIEWER", "slint-viewer")
DARK = os.path.join(ROOT, "tools", "dark.json")
OUT = os.path.join(ROOT, "screenshots")

# name, file, component
PAGES = [
    ("widgets", "pages/widgets_page.slint", "WidgetsPage"),
    ("controls", "pages/controls_page.slint", "ControlsPage"),
    ("dialogs", "pages/dialogs_page.slint", "DialogsPage"),
    ("dialogs-more", "pages/dialogs_page.slint", "MoreDialogsPage"),
]

WRAP = '''import { Theme } from "theme.slint";
import { %(comp)s } from "%(file)s";
export component Shot inherits Window {
    width: p.width;
    height: p.height;
    background: Theme.page;
    default-font-family: Theme.font;
    in-out property <bool> dark <=> Theme.dark;
    p := %(comp)s { x: 0px; y: 0px; }
}
'''

def run(args):
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        sys.exit(1)

def main():
    only = sys.argv[1:]
    os.makedirs(OUT, exist_ok=True)
    wrapper = os.path.join(ROOT, "ui", "_shot.slint")
    try:
        for name, file, comp in PAGES:
            if only and name not in only:
                continue
            open(wrapper, "w").write(WRAP % {"comp": comp, "file": file})
            run([VIEWER, "--screenshot", os.path.join(OUT, name + "-light.png"), wrapper])
            run([VIEWER, "--screenshot", os.path.join(OUT, name + "-dark.png"), "--load-data", DARK, wrapper])
            print("ok", name)
    finally:
        if os.path.exists(wrapper):
            os.remove(wrapper)
    if not only or "app" in only:
        app = os.path.join(ROOT, "ui", "app.slint")
        run([VIEWER, "--screenshot", os.path.join(OUT, "app-light.png"), "--size", "1440x900", app])
        run([VIEWER, "--screenshot", os.path.join(OUT, "app-dark.png"), "--size", "1440x900", "--load-data", DARK, app])
        print("ok app")

main()
