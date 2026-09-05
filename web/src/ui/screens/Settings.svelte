<script lang="ts">
  /**
   * Settings.
   *
   * Small on purpose. Everything here is a choice the automatic answer can
   * get wrong -- a tablet measured as a phone, a laptop with a touchscreen,
   * a room too bright for the dark palette -- and nothing here is a
   * preference the game should be asking about before it has been played.
   *
   * Shaped like that game's own: a list of sections down the left, the rows
   * for one section on the right. On a phone the sections become a row of
   * tabs above the rows instead.
   */
  import Choice from "../Choice.svelte";
  import Panel from "../Panel.svelte";
  import { LayoutMode, type Settings } from "$lib/settings";

  interface Props {
    settings: Settings;
    theme: "dark" | "light";
    onTheme: (theme: "dark" | "light") => void;
    onchange: () => void;
    onclose: () => void;
  }

  let { settings, theme, onTheme, onchange, onclose }: Props = $props();

  const SECTIONS = ["Display", "Controls", "About"] as const;
  let section = $state<(typeof SECTIONS)[number]>("Display");

  function set<K extends "layoutMode" | "touchControls">(
    key: K,
    value: Settings[K],
  ) {
    settings.set(key, value);
    onchange();
  }
</script>

<div class="screen">
  <Panel title="Settings" icon="⚙" {onclose} padded={false}>
    <div class="split">
      <nav>
        {#each SECTIONS as name (name)}
          <button
            class="nav ghost"
            class:selected={section === name}
            onclick={() => (section = name)}
          >
            <span class="diamond" class:hollow={section !== name}></span>
            {name}
          </button>
        {/each}
      </nav>

      <div class="rows">
        {#if section === "Display"}
          <Choice
            label="Layout"
            note="How the screen is divided."
            value={settings.layoutMode}
            options={[
              { value: LayoutMode.AUTO, label: "Auto" },
              { value: LayoutMode.WIDE, label: "Three panes" },
              { value: LayoutMode.COMPACT, label: "One pane" },
            ]}
            onselect={(value) => set("layoutMode", value as LayoutMode)}
          />
          <Choice
            label="Theme"
            note="Dusk, or daylight parchment."
            value={theme}
            options={[
              { value: "dark", label: "Dusk" },
              { value: "light", label: "Parchment" },
            ]}
            onselect={(value) => onTheme(value as "dark" | "light")}
          />
        {:else if section === "Controls"}
          <Choice
            label="On-screen stick"
            note="Drag anywhere on the world to move."
            value={settings.touchControls}
            options={[
              { value: null, label: "Auto" },
              { value: true, label: "Always" },
              { value: false, label: "Never" },
            ]}
            onselect={(value) => set("touchControls", value as boolean | null)}
          />
          <p class="prose">
            A keyboard works at any time: WASD or the arrow keys.
          </p>
        {:else}
          <p class="prose">
            Lechery is a transformation RPG. The figure is drawn by
            <a
              href="https://gitlab.com/PerplexedPeach/dynamic-avatar-drawer"
              target="_blank"
              rel="noreferrer">dynamic-avatar-drawer</a
            >, by Johnson Zhong, used under the LGPL v3 and shipped
            unmodified.
          </p>
        {/if}
      </div>
    </div>
  </Panel>
</div>

<style>
  .screen {
    height: 100%;
    display: grid;
    padding: var(--gap);
    padding-top: max(var(--gap), env(safe-area-inset-top));
    padding-bottom: max(var(--gap), env(safe-area-inset-bottom));
  }

  .split {
    flex: 1;
    min-height: 0;
    display: grid;
    grid-template-columns: 180px 1fr;
  }

  nav {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: var(--gap) var(--gap-tight);
    border-right: var(--hairline) solid var(--panel-edge);
    overflow: auto;
  }

  .nav {
    display: flex;
    align-items: center;
    gap: var(--gap-tight);
    justify-content: flex-start;
    font-family: var(--font-display);
    border-radius: 999px;
  }

  .nav.selected {
    color: var(--gold-bright);
    background: color-mix(in srgb, var(--gold) 12%, transparent);
  }

  .rows {
    min-height: 0;
    overflow-y: auto;
    padding: var(--gap);
  }

  .prose {
    color: var(--ink-dim);
    font-size: var(--font-size-small);
    margin: 0 0 var(--gap);
  }

  a {
    color: var(--gold);
  }

  /* A phone has no room for a column of sections beside the rows, so they
   * become a strip of tabs above them. */
  @media (max-width: 640px) {
    .split {
      grid-template-columns: 1fr;
      grid-template-rows: auto 1fr;
    }

    nav {
      flex-direction: row;
      border-right: none;
      border-bottom: var(--hairline) solid var(--panel-edge);
      padding: var(--gap-tight);
    }

    .nav {
      flex: 1;
      justify-content: center;
    }
  }
</style>
