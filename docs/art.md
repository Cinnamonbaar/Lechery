# Art research: anime faces, hair, bodies, line and shading

What established references say, how the current doll measures up, and
what to change. Sources are linked at the end of each section; most are
tutorial sites rather than books, so where they disagree that is noted and
the choice is ours.

## 0. Visual references, measured

Text alone is not enough, so the main references were downloaded, broken
into frames and measured pixel by pixel. They are not committed — they
are other people's work — but each is linked and its numbers are below.

**Slynyrd, Pixelblog 29: Anime Faces and Hair** — pixel art, our exact
medium. [Link](https://www.slynyrd.com/blog/2020/7/28/pixelblog-29-anime-faces-and-hair).
Head outlines measured from the final frame, on a 34-pixel-wide head,
crown 0 to chin 1:

| | Female | Male | Ours (before) |
|---|---|---|---|
| width ÷ height | 0.85 | 0.81 | 0.87 |
| brow line | 0.40 | 0.40 | 0.43 |
| eye centre | 0.525 | 0.55 | 0.585 |
| eye width ÷ head width | 0.18–0.2 | 0.18 | 0.22 |
| gap between eyes ÷ head width | 0.29 | 0.29 | 0.22 |
| jaw starts to narrow | 0.65 | 0.62 | 0.56 |
| chin width ÷ head width | 0.06 | 0.12 | 0.36 |
| mouth | 0.825 | 0.83 | 0.86 |
| neck width ÷ head width | 0.47 | — | ~0.5 |

What the frames show beyond the numbers:
- The head is built as a circle, then a jaw that angles in to a soft
  point; the neck leaves the jaw near the chin.
- **Line**: one pixel, a dusty dark purple-grey, never black, with lighter
  in-between pixels where a curve steps — hand anti-aliasing.
- **Hair** is drawn in four steps: flow lines from a cowlick toward the
  back of the head; one flat colour blocked in; then refined into clumps
  with shadows; then highlights. Clumps are split by thin dark strand
  lines that converge toward the crown. The silhouette ends in jagged,
  outward-flaring tips. The hair stands well off the skull. Lighter patches
  sit on the upper dome between strand lines. Hair casts a shadow on the
  face under the bangs and at the temples. Bangs may cross the eyes — a
  style choice, not a rule.
- The **face** is barely shaded: dot blush, a one-or-two-pixel nose, small
  lips, the jaw line, a shadow under the jaw on the neck.

**Slynyrd, Pixelblog 49: Realistic Human Anatomy** — the 8-head model.
[Link](https://www.slynyrd.com/blog/2024/3/25/pixelblog-49-realistic-human-anatomy).
Built exactly the way we now build the doll: head, torso, arms and legs
blocked out separately in flat colours, measured, then dressed. Labelled
measurements: man 96 px tall, head 12 px tall and 9 wide, shoulders 27 px
(0.28 of height); woman 88 px tall, head 11 px tall and 9 wide, shoulders
23 px (0.26). About eight colours per figure.

**Slynyrd, Pixelblog 17: Human Anatomy** — the stylised 6-head sprite
model. [Link](https://www.slynyrd.com/blog/2019/5/21/pixelblog-17-human-anatomy).
The clearest lesson for us is how a body reads *without* pillow shading:
flat fill, an outline in a darker skin tone, and anatomy given by a few
interior marks — collarbones, the line under the chest, navel, knee caps,
the groin V, the inner elbow. Limbs are substantial: an upper arm about 7%
of the figure's height, thighs that touch and taper, real hands and feet.
**Ours are about half as thick** — sticks with a gap between the legs —
which no text source flagged. His model is deliberately stocky, so ours
should not go all the way, but it should go most of it.

## 1. Shading — the biggest flaw: we pillow-shade

**What the references say.** *Pillow shading* is the classic pixel-art
mistake: shading follows the outline of each shape, banding inward from
every edge, instead of following a light. The test is "where is the light
coming from?" — if you cannot answer, it is pillow shaded. The fix is one
light direction (usually top-left or top-front), and shadow placed where
that light does not reach: the undersides of forms, cast shadows.

Anime cel shading is two or three tones per material — base, shadow,
sometimes a highlight — with **hard edges and no gradients**. Shadows are
*shapes with meaning*:

- the hair casts a shadow on the forehead, under the bangs;
- the head casts a shadow on the neck, under the chin, matching the chin's
  shape in front view, falling to the side away from the light;
- the nose gets a small shadow on one side;
- shadows sit under the arms, under the chest, on the side of the torso
  away from the light;
- shadow colours are warm and saturated, never grey.

**Where we are.** Our shading rule darkens the bottom/right edge band and
lightens the top/left band of *every part*. That is pillow shading with a
slight lean: it outlines each shape in shadow rather than lighting a form.
It is why the figure reads flat and "drawn by a program".

**Change.** Replace edge bands with **shadow shapes**: each part declares
where its shadows fall for one fixed light (front, from the upper left),
as hard-edged regions — neck under the chin, forehead under the fringe,
under the bust, inner thighs, the torso's far side, hair's underside and
clump ends. Highlights only where they mean something (hair's shine band,
eyes, maybe the top of the bust and shoulders).

Sources: [pixnote — Shading & Lighting](https://pixnote.net/en/learn/shading),
[OpenGameArt — Shadow and light](https://opengameart.org/content/chapter-4-shadow-and-light),
[Pixel Grimoire #4](https://medium.com/pixel-grimoire/how-to-start-making-pixel-art-4-f57f51dcfa02),
[AnimeOutline — Shade an anime face](https://www.animeoutline.com/how-to-shade-an-anime-face-in-different-lighting/),
[Clip Studio — Anime skin colouring](https://www.clipstudio.net/how-to-draw/archives/161037),
[2D figure cel shading guide](https://2dfigurepainting.com/blogs/article/cel-shading-guide),
[AnimeOutline — Colour an anime character](https://www.animeoutline.com/how-to-color-anime-character-step-by-step/),
[sprite-ai — Anime pixel art](https://www.sprite-ai.art/blog/anime-pixel-art).

## 2. Line

**What the references say.**
- **Line weight varies.** A thick outer line around each part (skin, hair,
  clothes), thinner lines for inner detail (face, folds). The contrast
  alone adds life; bold outer and thin interior lines is the norm in
  illustration generally.
- Lines **thicken where they meet**, and thin out on the lit side.
- **Colour, not black.** A very dark tint of the local hue — near-black
  brown for skin, dark purple or navy per character. Pure black reads as a
  hole in the sprite.
- **Selective outline**: lighter or dropped where light hits.

**Where we are.** One outline weight everywhere, tinted (good), selective
(good). Inner lines between parts are just the shadow band, not lines.

**Change.** Two weights: a heavier silhouette line, a thin inner line
between parts and for detail; thicken at junctions (armpit, crotch, under
the chin, where hair meets face).

Sources: [MediBang — thick and thin lines](https://medibangpaint.com/en/use/2022/07/how-to-draw-a-line-drawing-for-people-who-are-not-good-at-the-strength-of-line-drawing/),
[Clip Studio — anime line art](https://www.clipstudio.net/how-to-draw/archives/165695),
[Clip Studio — line quality](https://www.clipstudio.net/how-to-draw/archives/163108),
[YamPuff — inking](https://www.yampuff.com/inking-tutorial-yampuff/),
[Northwestern NPR course](https://users.cs.northwestern.edu/~ago820/NPRcourse1/node5.html),
[pixel-editor — outlines](https://www.pixel-editor.com/articles/pixel-art-outlines).

## 3. Face

**What the references say.**
- Construction: a circle for the skull, a centre line, a jaw tapering to
  the chin.
- **Anime jaws are narrower and more tapered than real ones, and the chin
  small and pointed** — softer and pointed for women, straighter and more
  angular for men.
- **Age reads from the face**: young = rounder face, larger eyes, shorter
  chin; adult = narrower face, more structure, smaller eyes, longer chin.
- Placement: eyes roughly halfway down; nose about halfway from eyes to
  chin; mouth halfway from nose to chin. Thirds and the rule of fifths, as
  before.
- **Eyes**: the upper lash line is the heaviest shape and carries the
  expression. The iris is a *vertical oval, cropped by the upper lid*
  (sources disagree how much: a fifth to more than half — a style choice).
  At least three iris tones: dark top rim under the lid's shadow, lighter
  below, one hard highlight; a second, smaller highlight optional. Anime
  eyes are generally *wider than tall*; feminine eyes rounder, masculine
  flatter.

**Where we are.** The head is wide and round (0.87 of its height) with a
small chin — the *young* end of the age cues, which works against adult
characters. Our eyes are taller than wide (1.22), the iris is a centred
oval not cropped by the lid, and the eyes do not change with the face.

**Change.** Narrow the head and lengthen the chin toward the adult end;
taper the jaw, softer for curvy builds and squarer for straight ones.
Make eyes a little wider than tall, crop the iris top under the lid, keep
the three-tone iris. Nose: a small one-sided shadow (we have this). Add the
hair's cast shadow on the forehead.

Sources: [Skyrye — anime head](https://skyryedesign.com/art/drawing/anime-manga/how-to-draw-anime-head/),
[Lunarmimi — anime face and head](https://lunarmimi.net/anime-art-tips/draw-anime-face-and-head/),
[Xencelabs — anime head](https://www.xencelabs.com/community/creative-corner/how-to-draw-manga-or-anime-head-and-face-step-by-step),
[Domestika — face proportions](https://www.domestika.org/en/blog/8861-anime-tutorial-face-proportions-for-beginners),
[Jerwood — anime face](https://jerwoodvisualarts.org/blog/how-to-draw-an-anime-face/),
[Jerwood — anime head](https://jerwoodvisualarts.org/blog/how-to-draw-an-anime-head/),
[Skyrye — anime eyes](https://skyryedesign.com/art/drawing/anime-eyes-drawing/),
[Biorust — anime eyes](https://www.biorust.com/tutorials/anime-eyes/),
[Animefacelab — anime eyes](https://animefacelab.com/tutorials/how-to-draw-anime-eyes/).

## 4. Hair

**What the references say.**
- **Order**: skull first, then the **hairline** (following the skull's
  curve), then the **parting** (centre, side or swept), then big clumps.
- **Clumps, not strands**: a few big clumps of *varied* size — typically
  one large centre clump with split ends and smaller ones each side.
  Identical locks look stiff and artificial. Gaps between clumps don't go
  above the hairline.
- **Volume**: leave air between hair and skull; even a few pixels at the
  crown read as volume. Clumps fan out from the crown.
- **Shading**: clumps curving in toward the head shadow their own lower
  ends and their neighbours; shadows along the bottom and sides of clumps;
  the inner/back hair darker. No gradients.
- **Shine**: the "angel ring" — a crisp highlight band that *curves with
  the skull*, ignoring individual clumps. A straight band flattens the head.

**Where we are.** A smooth cap with a regular zigzag fringe and plain side
locks. No parting, no clumps, no shadows, no shine. This is most of why
the hair looks like a helmet.

**Change.** Rebuild hair as clumps: a parting point, clumps fanning from
it with varied widths and lengths, each a tapered shape; shadow under the
fringe and at clump ends; darker back layer; a curved angel ring.

Sources: [AnimeOutline — female hair](https://www.animeoutline.com/how-to-draw-anime-and-manga-hair-female/),
[AnimeOutline — long hair](https://www.animeoutline.com/how-to-draw-long-anime-hair-step-by-step/),
[AnimeOutline — shade anime hair](https://www.animeoutline.com/how-to-shade-anime-hair-step-by-step/),
[Skyrye — 15 hair styles](https://skyryedesign.com/art/drawing/body/anime-hair-drawing-techniques/),
[Skyrye — mass and value](https://skyryedesign.com/art/drawing/how-to-draw-hair/),
[Lavaritte — anime hair](https://lavaritte.com/blogs/anime-hair-tutorial/),
[Jerwood — male hair](https://jerwoodvisualarts.org/blog/how-to-draw-anime-male-hair/),
[3dxdev — anime hair material](https://3dxdev.com/how-to-make-anime-hair-material-in-blender-the-right-order/),
[MediBang — anime glossing](https://medibangpaint.com/en/use/2019/12/create-glossy-hair-with-anime-glossing/).

## 5. Body

**What the references say.**
- Adults are **6–7 heads (women) to 6–8 (men)** in common anime and manga;
  some manga guides go to 8.5. Our 6.2–7 at the halfway blend is inside
  the common range.
- Elbows at the waist; legs about half the height. (We have both.)
- **Women**: rounded lines on shoulders, chest, hips, thighs and calves, a
  defined waist. **Men**: angles, wider shoulders and chest, little waist.
  Broad shoulders on a woman read as powerful; narrow on a man as slender.
- A dead-symmetrical front pose looks stiff; a little asymmetry in stance
  says more than extra detail.

**Where we are.** Proportions are in range. The silhouette is made of
straight segments (polygons), so *curvy* is a wider shape rather than a
rounder one; the pose is perfectly symmetrical.

**Change.** Round the body outlines (curves through the landmarks, not
straight segments), let build control rounded vs angular, and later a
slight weight shift.

Sources: [Anime Art Magazine — head-to-body ratio](https://animeartmagazine.com/using-head-to-body-ratio-to-adjust-a-characters-height-and-age-part-1/),
[Anime Art Academy — proportions](https://animeartacademy.com/p/how-to-draw-anime-body-proportions),
[Skyrye — anime body](https://skyryedesign.com/art/how-to-drawing-anime-body/),
[Canson — manga body](https://en.canson.com/expert-advice/manga-drawing-characters-body),
[Procreate Store — proportions](https://www.procreatestore.com/post/how-to-draw-anime-body-proportions-the-complete-procreate-guide),
[the-pixel.art — character design](https://the-pixel.art/articles/pixel-art-character-design/).

## 6. Palette

Two or three shades per material plus a line colour; a whole character in
roughly 8–12 colours; shadows hue-shifted cooler or warmer rather than
darkened grey. Very dark pupils, small white highlights, strong value
contrast in the eyes. We already hue-shift; the change is fewer, more
deliberate tones.

Sources: [sprite-ai — anime pixel art](https://www.sprite-ai.art/blog/anime-pixel-art),
[pixel-editor — outlines](https://www.pixel-editor.com/articles/pixel-art-outlines).

## Order of work

1. **Shading and line together** — flat fill, a one-pixel outline in a dark
   tint of each material with hand-style anti-aliasing at curve steps, and
   shadows as meaningful shapes for one light (under the jaw on the neck,
   under the bangs, under the arms and chest, the body's far side) instead
   of edge bands. Interior anatomy as a few marks. Affects every part, so
   it goes first.
2. **Face** — the measured Slynyrd proportions: narrower tapered jaw and
   pointed chin, eyes raised to the midline and set further apart, neck
   leaving the jaw.
3. **Body** — limbs roughly twice as thick, thighs that touch and taper,
   real hands and feet, rounded outlines.
4. **Hair** — flow from a cowlick, clumps split by strand lines, jagged
   tips, shine patches on the dome, standing well off the skull, a cast
   shadow on the face.
