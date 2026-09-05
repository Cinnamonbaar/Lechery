"""Restyling pygbag's loading page.

pygbag builds the page from a template it fetches from its CDN. The default
is powder blue with a green box, shows no progress (the bar exists but is
hidden), and looks nothing like the game.

The template is patched rather than vendored. A copy of all 438 lines would
drift the moment pygbag changed anything, and drift silently; these are
targeted replacements that raise when they no longer match, so a pygbag
update fails the build with the exact line that moved instead of quietly
restoring the default look.

Each anchor is a single line, chosen to be unique in the file -- multi-line
blocks would break on any reindent.
"""

from __future__ import annotations

from urllib.request import urlopen

#: Where pygbag keeps its templates. Version comes from the installed pygbag.
CDN = "https://pygame-web.github.io/cdn/{version}/"
TEMPLATE = "default.tmpl"

BACKGROUND = "#0d0c10"
ACCENT = "#e2c48c"
TEXT = "#cec8c4"
MUTED = "#8a8494"
TRACK = "#241f2b"

#: (anchor, replacement). Every one must match, exactly once.
PATCHES: list[tuple[str, str]] = [
    # The grey flash before the canvas appears, set from the template's
    # python half.
    (
        'platform.document.body.style.background = "#7f7f7f"',
        f'platform.document.body.style.background = "{BACKGROUND}"',
    ),
    # The page itself, before that runs.
    ("background-color:powderblue;", f"background-color: {BACKGROUND};"),
    # The green "Loading, please wait" box.
    ("background: green;", "background: transparent;"),
    ("color: blue;", f"color: {MUTED};"),
    # The status line under the progress bar.
    ("color: rgb(120, 120, 120);", f"color: {MUTED};"),
    # The progress bar, which the default template sizes and then hides.
    ("height: 20px;", "height: 6px;"),
    ("width: 300px;", "width: min(260px, 62vw);"),
    # Keep the progress area visible: the default hides it unless debugging,
    # which is why a bar exists but is never seen.
    ("transfer.hidden = debug_hidden", "transfer.hidden = false"),
    # The avatar library and our bridge to it, loaded before the game so
    # the module exists by the time python asks for it. Deferred so they do
    # not hold up the first paint of the loading screen.
    (
        '<script src="{{cookiecutter.cdn}}/browserfs.min.js"></script>',
        '<script src="{{cookiecutter.cdn}}/browserfs.min.js"></script>\n'
        '    <script src="da.js" defer></script>\n'
        '    <script src="avatar.js" defer></script>',
    ),
    # A title above the bar, so the wait shows the game's name.
    (
        '<div class="emscripten" id="status">Downloading...</div>',
        '<div id="brand">Lechery</div>\n'
        '        <div class="emscripten" id="status">Loading</div>',
    ),
]

#: Added just before the template's closing </style>.
EXTRA_CSS = f"""
        /* --- Lechery loading screen ------------------------------------ */
        #transfer {{
            position: fixed;
            inset: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 18px;
            z-index: 100;
            /* Painted over by the canvas once the game starts drawing. */
            pointer-events: none;
        }}

        /* The template hides this with the `hidden` attribute, which works
           by applying display:none from the browser's own stylesheet. The
           rule above is an author rule and beats it, so without this the
           loading screen stays on screen over the game, hidden in name
           only. */
        #transfer[hidden] {{
            display: none !important;
        }}

        #brand {{
            font-family: Georgia, "Times New Roman", serif;
            font-size: 34px;
            letter-spacing: 0.06em;
            color: {ACCENT};
        }}

        #status {{
            font-family: Georgia, "Times New Roman", serif;
            font-size: 13px;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin: 0;
            color: {MUTED};
        }}

        /* A <progress> needs each engine's own pseudo-elements; without
           these it keeps the platform's default blue lozenge. */
        #progress {{
            appearance: none;
            -webkit-appearance: none;
            border: 0;
            border-radius: 3px;
            background-color: {TRACK};
            overflow: hidden;
        }}
        #progress::-webkit-progress-bar {{ background-color: {TRACK}; }}
        #progress::-webkit-progress-value {{ background-color: {ACCENT}; }}
        #progress::-moz-progress-bar {{ background-color: {ACCENT}; }}

        #infobox {{
            font-family: Georgia, "Times New Roman", serif;
            font-size: 12px;
            letter-spacing: 0.1em;
            border: 0;
        }}
"""


def cdn_url(version: str) -> str:
    return CDN.format(version=version) + TEMPLATE


def patch(source: str) -> str:
    """Apply every patch, or explain which one no longer fits."""
    result = source
    for anchor, replacement in PATCHES:
        found = result.count(anchor)
        if found != 1:
            raise ValueError(
                f"loading screen: expected exactly one {anchor!r} in pygbag's "
                f"template, found {found}. The template has changed; update "
                f"tools/loadingscreen.py rather than shipping the default look."
            )
        result = result.replace(anchor, replacement)

    if result.count("    </style>") != 1:
        raise ValueError("loading screen: cannot find the template's </style>")
    return result.replace("    </style>", EXTRA_CSS + "    </style>")


def fetch(version: str, timeout: int = 30) -> str:
    with urlopen(cdn_url(version), timeout=timeout) as response:
        return response.read().decode("utf-8")


def build(version: str, destination) -> bool:
    """Write a patched template. Returns whether it worked.

    A network failure falls back to pygbag's own template rather than
    failing the build: an ugly loading screen is better than no game. A
    *patch* failure is different and does raise -- that means the template
    changed shape and someone should look.
    """
    try:
        source = fetch(version)
    except Exception as error:  # network only; patch errors propagate
        print(f"loading screen: could not fetch the template ({error})")
        return False

    destination.write_text(patch(source), encoding="utf-8")
    return True
