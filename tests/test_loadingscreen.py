"""Tests for the loading-screen patcher.

The fixture below is copied from pygbag's real default.tmpl (read out of a
CI log, since the CDN is unreachable from the development sandbox). It is
deliberately verbatim: the patcher matches exact lines, so a paraphrased
fixture would prove nothing.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import loadingscreen  # noqa: E402

TEMPLATE = '''<html lang="en-us"><script src="{{cookiecutter.cdn}}pythons.js">#<!--
async def custom_site():
    import embed
    platform.document.body.style.background = "#7f7f7f"

    platform.window.transfer.hidden = true
    platform.window.canvas.style.visibility = "visible"
# --></script><head><!--
    <style>
        #status {
            display: inline-block;
            vertical-align: top;
            margin-top: 20px;
            margin-left: 30px;
            font-weight: bold;
            color: rgb(120, 120, 120);
        }

        #progress {
            height: 20px;
            width: 300px;
        }

        #infobox {
            position: fixed; /* center relative to viewport */
            background: green;
            color: blue;
            font-weight: bold;
            padding: 12px 24px;
            z-index: 999999;
        }

        body {
            font-family: arial;
            margin: 0;
            padding: none;
            background-color:powderblue;
        }
    </style>
</head>
<body>
    <div id="transfer" align=center>
        <div class="emscripten" id="status">Downloading...</div>
        <div class="emscripten">
            <progress value="0" max="100" id="progress"></progress>
        </div>
    </div>
    <canvas class="emscripten" id="canvas"></canvas>
    <div id="infobox">Loading, please wait ...</div>
    <script type="application/javascript">
    async function custom_onload(debug_hidden) {
        pyconsole.hidden = debug_hidden
        transfer.hidden = debug_hidden
        show_infobox()
    }
    </script>
</body>
</html>
'''


@pytest.fixture
def patched():
    return loadingscreen.patch(TEMPLATE)


def test_the_grey_flash_is_replaced(patched):
    """The body colour set from the template's python half."""
    assert '"#7f7f7f"' not in patched
    assert loadingscreen.BACKGROUND in patched


def test_the_powder_blue_page_is_replaced(patched):
    assert "powderblue" not in patched


def test_the_green_box_is_gone(patched):
    assert "background: green;" not in patched
    assert "color: blue;" not in patched


def test_the_progress_area_is_no_longer_hidden(patched):
    """A bar exists in the default template and is never shown."""
    assert "transfer.hidden = debug_hidden" not in patched
    assert "transfer.hidden = false" in patched


def test_the_game_is_named_while_it_loads(patched):
    assert '<div id="brand">Lechery</div>' in patched
    assert "Downloading..." not in patched


def test_the_progress_bar_is_styled_for_every_engine(patched):
    """A bare <progress> keeps the platform's default blue lozenge."""
    for pseudo in ("::-webkit-progress-value", "::-moz-progress-bar"):
        assert pseudo in patched


def test_the_extra_styles_land_inside_the_stylesheet(patched):
    """Outside the <style> block they would be text on the page."""
    style_open = patched.index("<style>")
    style_close = patched.index("</style>")
    assert style_open < patched.index("#brand") < style_close


def test_a_template_that_no_longer_matches_fails_loudly():
    """A pygbag update must break the build, not silently restore defaults."""
    moved = TEMPLATE.replace("background: green;", "background: darkgreen;")
    with pytest.raises(ValueError, match="template has changed"):
        loadingscreen.patch(moved)


def test_an_anchor_appearing_twice_is_also_refused():
    """Two matches means the anchor is no longer specific enough."""
    doubled = TEMPLATE.replace(
        "        body {", "        .other { background-color:powderblue; }\n        body {"
    )
    with pytest.raises(ValueError):
        loadingscreen.patch(doubled)


def test_a_network_failure_falls_back_instead_of_failing_the_build(tmp_path, monkeypatch):
    """An ugly loading screen beats no game."""
    def unreachable(version, timeout=30):
        raise OSError("no network")

    monkeypatch.setattr(loadingscreen, "fetch", unreachable)
    assert loadingscreen.build("0.9.3", tmp_path / "out.tmpl") is False


def test_a_successful_build_writes_a_patched_template(tmp_path, monkeypatch):
    monkeypatch.setattr(loadingscreen, "fetch", lambda version, timeout=30: TEMPLATE)
    destination = tmp_path / "out.tmpl"

    assert loadingscreen.build("0.9.3", destination) is True
    assert "powderblue" not in destination.read_text()
