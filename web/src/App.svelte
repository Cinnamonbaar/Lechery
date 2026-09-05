<script lang="ts">
  /**
   * The shell: which screen is up, and how wide the window thinks it is.
   *
   * Layout is decided here and passed down, so no component measures the
   * window for itself -- one measurement, one answer, and the settings
   * override applies everywhere at once.
   */
  import { backstory } from "$lib/content/backstories";
  import { Session } from "$lib/session";
  import { LayoutMode, Settings } from "$lib/settings";
  import type { Character } from "$lib/traits/character";
  import Creation from "$ui/screens/Creation.svelte";
  import Menu from "$ui/screens/Menu.svelte";
  import Play from "$ui/screens/Play.svelte";

  /** Below this many CSS pixels the three-pane view has nowhere to go. */
  const WIDE_AT = 900;

  type Screen = "menu" | "creation" | "play";

  const settings = Settings.load();

  let screen = $state<Screen>("menu");
  let session = $state<Session | null>(null);
  let width = $state(typeof window === "undefined" ? 1024 : window.innerWidth);
  let leftOpen = $state(settings.wideLeftOpen);
  let rightOpen = $state(settings.wideRightOpen);

  const measuredWide = $derived(width >= WIDE_AT);
  const wide = $derived(
    settings.layoutMode === LayoutMode.AUTO
      ? measuredWide
      : settings.layoutMode === LayoutMode.WIDE,
  );

  // Coarse pointer means a thumb: draw the stick unless the player said no.
  const showStick = $derived(
    settings.touchControls ??
      (typeof matchMedia === "function"
        ? matchMedia("(pointer: coarse)").matches
        : false),
  );

  $effect(() => {
    const resize = () => (width = window.innerWidth);
    window.addEventListener("resize", resize);
    window.addEventListener("orientationchange", resize);
    return () => {
      window.removeEventListener("resize", resize);
      window.removeEventListener("orientationchange", resize);
    };
  });

  // A narrow screen shows one bar at a time, so opening one closes the other;
  // a wide screen shows both, and remembers which the player had open.
  function toggleLeft() {
    leftOpen = !leftOpen;
    if (!wide && leftOpen) rightOpen = false;
    if (wide) settings.set("wideLeftOpen", leftOpen);
  }

  function toggleRight() {
    rightOpen = !rightOpen;
    if (!wide && rightOpen) leftOpen = false;
    if (wide) settings.set("wideRightOpen", rightOpen);
  }

  function startCreation() {
    screen = "creation";
    // A phone has no room for a bar over creation; start the game with the
    // world in view and let the player open what they want.
    if (!wide) {
      leftOpen = false;
      rightOpen = false;
    }
  }

  function begin(character: Character) {
    const started = Session.newGame(null, character);
    const backstoryId = character.backstoryId;
    // The one piece of prose the player has before the world says anything.
    if (backstoryId) started.log.prose(backstory(backstoryId).opening);
    session = started;
    screen = "play";
  }
</script>

{#if screen === "menu"}
  <Menu onstart={startCreation} />
{:else if screen === "creation"}
  <Creation {wide} onbegin={begin} onback={() => (screen = "menu")} />
{:else if session}
  <Play
    {session}
    {wide}
    {leftOpen}
    {rightOpen}
    {showStick}
    onToggleLeft={toggleLeft}
    onToggleRight={toggleRight}
  />
{/if}
