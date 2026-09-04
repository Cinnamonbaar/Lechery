# Fonts

Drop `body.ttf` and `heading.ttf` here to replace the fallback typeface.

They are loaded by path rather than by system name because a pygbag build
has no OS font list — `SysFont` silently degrades in the browser, so a
desktop build and a web build would render differently and you would only
find out after packaging.

Files here are optional; without them the game uses the font bundled inside
pygame, which is always present on every platform.
