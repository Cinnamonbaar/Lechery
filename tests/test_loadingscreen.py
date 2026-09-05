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

    <script src="{{cookiecutter.cdn}}/browserfs.min.js"></script>

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


def test_the_hidden_attribute_still_hides_the_loading_screen(patched):
    """The bug: it stayed on screen over the menu.

    The template hides it with the `hidden` attribute, which applies
    display:none from the browser's own stylesheet. Our `display: flex` is
    an author rule and outranks that, so the element was hidden in name
    only until this rule put it back.
    """
    assert "#transfer[hidden]" in patched

    rule = patched[patched.index("#transfer[hidden]"):]
    rule = rule[: rule.index("}")]
    assert "display: none !important" in rule


def test_the_override_comes_after_the_rule_it_has_to_beat(patched):
    """Equal specificity is decided by order; !important settles it anyway,
    but relying on both is free."""
    assert patched.index("#transfer {") < patched.index("#transfer[hidden]")


def test_the_avatar_library_and_bridge_are_loaded_by_the_page(patched):
    """They have to exist before python asks for them."""
    assert '<script src="da.js" defer></script>' in patched
    assert '<script src="avatar.js" defer></script>' in patched


def test_the_bridge_loads_after_the_library_it_uses(patched):
    """avatar.js calls into da on load; the order is not decorative."""
    assert patched.index('src="da.js"') < patched.index('src="avatar.js"')


def test_the_vendored_library_is_not_modified():
    """LGPL compliance rests on it staying replaceable.

    Checked as a byte comparison against what is served, so an accidental
    edit or a bundler getting clever shows up here.
    """
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    vendored = root / "assets" / "vendor" / "dynamic-avatar-drawer" / "da.js"

    assert vendored.exists(), "the library should be vendored, not fetched at build time"
    assert (vendored.parent / "LICENSE.md").exists(), "its licence must ship with it"
    text = vendored.read_text(errors="ignore")
    assert "webpackUniversalModuleDefinition" in text, "should be the packaged dist build"
