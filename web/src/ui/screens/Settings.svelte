<script lang="ts">
  /**
   * Settings.
   *
   * Small on purpose. Everything here is a choice the automatic answer can
   * get wrong -- a tablet measured as a phone, a laptop with a touchscreen,
   * a room too bright for the dark theme -- and nothing here is a preference
   * the game should be asking about before it has been played.
   */
  import { LayoutMode, type Settings } from "$lib/settings";

  interface Props {
    settings: Settings;
    theme: "dark" | "light";
    onTheme: (theme: "dark" | "light") => void;
    onchange: () => void;
    onclose: () => void;
  }

  let { settings, theme, onTheme, onchange, onclose }: Props = $props();

  const LAYOUTS: [LayoutMode, string, string][] = [
    [LayoutMode.AUTO, "Automatic", "Decide from the size of the window."],
    [LayoutMode.WIDE, "Three panes", "Doll, world and log side by side."],
    [LayoutMode.COMPACT, "One pane", "World filling the screen, bars as drawers."],
  ];

  const TOUCH: [boolean | null, string][] = [
    [null, "Automatic"],
    [true, "Always"],
    [false, "Never"],
  ];
</script>

<div class="settings">
  <header>
    <h2>Settings</h2>
    <button onclick={onclose}>Done</button>
  </header>

  <fieldset>
    <legend>Layout</legend>
    {#each LAYOUTS as [mode, label, note] (mode)}
      <button
        class="option"
        class:selected={settings.layoutMode === mode}
        onclick={() => {
          settings.set("layoutMode", mode);
          onchange();
        }}
      >
        <strong>{label}</strong>
        <span>{note}</span>
      </button>
    {/each}
  </fieldset>

  <fieldset>
    <legend>On-screen stick</legend>
    <div class="row">
      {#each TOUCH as [value, label] (label)}
        <button
          class="chip"
          class:selected={settings.touchControls === value}
          onclick={() => {
            settings.set("touchControls", value);
            onchange();
          }}>{label}</button
        >
      {/each}
    </div>
  </fieldset>

  <fieldset>
    <legend>Theme</legend>
    <div class="row">
      <button
        class="chip"
        class:selected={theme === "dark"}
        onclick={() => onTheme("dark")}>Dark</button
      >
      <button
        class="chip"
        class:selected={theme === "light"}
        onclick={() => onTheme("light")}>Light</button
      >
    </div>
  </fieldset>
</div>

<style>
  .settings {
    height: 100%;
    overflow-y: auto;
    padding: var(--gap);
    padding-top: max(var(--gap), env(safe-area-inset-top));
    max-width: 640px;
    margin: 0 auto;
  }

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: var(--gap);
  }

  h2 {
    font-size: var(--font-size-title);
  }

  fieldset {
    border: none;
    margin: 0 0 var(--gap);
    padding: 0;
  }

  legend {
    font-family: var(--font-ui);
    font-size: var(--font-size-small);
    color: var(--ink-dim);
    padding-bottom: 4px;
  }

  .option {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
    text-align: left;
    padding: var(--gap-tight);
    margin-bottom: var(--gap-tight);
  }

  .option span {
    font-size: var(--font-size-small);
    color: var(--ink-faint);
  }

  .row {
    display: flex;
    gap: var(--gap-tight);
    flex-wrap: wrap;
  }

  .chip {
    font-size: var(--font-size-small);
  }

  .chip.selected,
  .option.selected {
    border-color: var(--accent);
    color: var(--accent);
  }
</style>
