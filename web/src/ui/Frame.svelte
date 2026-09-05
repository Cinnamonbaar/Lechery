<script lang="ts">
  /**
   * The three-pane frame: paperdoll, world, log.
   *
   * Wide screens show all three side by side. A phone stacks the world over
   * the log instead of hiding the log in a drawer -- a room is 19 by 13 and a
   * phone is nearly three times taller than it is wide, so a full-height
   * world pane is mostly dead space, and this game's text is worth reading
   * anyway. The paperdoll stays a drawer, because it is a thing you consult.
   *
   * That is one layout with a class on it rather than two component trees, so
   * a change to a bar cannot land in one view and not the other.
   *
   * The panes are snippets, so the frame owns arrangement and nothing else.
   */
  import type { Snippet } from "svelte";

  interface Props {
    left?: Snippet;
    centre: Snippet;
    right?: Snippet;
    /** Whether the layout should behave as wide, decided by the caller. */
    wide: boolean;
    leftOpen: boolean;
    rightOpen: boolean;
    leftLabel?: string;
    rightLabel?: string;
    onToggleLeft?: () => void;
    onToggleRight?: () => void;
    onSettings?: () => void;
  }

  let {
    left,
    centre,
    right,
    wide,
    leftOpen,
    rightOpen,
    leftLabel = "Body",
    rightLabel = "Log",
    onToggleLeft,
    onToggleRight,
    onSettings,
  }: Props = $props();

  const showLeft = $derived(Boolean(left) && leftOpen);
  // Wide: the log is a column beside the world. Compact: it is the strip
  // under it, and the tab collapses the strip rather than opening a drawer.
  const showRight = $derived(Boolean(right) && rightOpen);
</script>

<div class="frame" class:wide class:compact={!wide}>
  {#if showLeft}
    <aside class="bar left panel">
      <div class="panel-fill">
        {@render left?.()}
      </div>
    </aside>
  {/if}

  <main class="centre">
    {@render centre()}

    <div class="tabs">
      {#if left}
        <button
          class="tab"
          class:active={leftOpen}
          aria-pressed={leftOpen}
          onclick={onToggleLeft}
        >
          {#if leftOpen}<span class="diamond"></span>{/if}{leftLabel}</button
        >
      {/if}
      {#if right}
        <button
          class="tab"
          class:active={rightOpen}
          aria-pressed={rightOpen}
          onclick={onToggleRight}
        >
          {#if rightOpen}<span class="diamond"></span>{/if}{rightLabel}</button
        >
      {/if}
      {#if onSettings}
        <button class="tab" aria-label="Settings" onclick={onSettings}>⚙</button>
      {/if}
    </div>
  </main>

  {#if showRight}
    <aside class="bar right panel">
      <div class="panel-fill">
        {@render right?.()}
      </div>
    </aside>
  {/if}
</div>

<style>
  .frame {
    height: 100%;
    display: grid;
    gap: var(--gap);
    padding: var(--gap);
    /* Notches and home indicators: the bars must not sit under either. */
    padding-top: max(var(--gap), env(safe-area-inset-top));
    padding-bottom: max(var(--gap), env(safe-area-inset-bottom));
    background: var(--ground);
  }

  .frame.wide {
    grid-auto-flow: column;
    /* Only the bars that are open take a column, so closing one gives its
     * width to the world rather than leaving a gap. */
    grid-auto-columns: min-content 1fr min-content;
    grid-template-columns: auto 1fr auto;
  }

  .frame.compact {
    grid-template-columns: 1fr;
    /* The world takes what it needs to frame a room and the log takes the
     * rest; with the log closed the world has the screen to itself. */
    grid-template-rows: minmax(0, 46fr) minmax(0, 54fr);
    position: relative;
  }

  .frame.compact:not(:has(.bar.right)) {
    grid-template-rows: 1fr;
  }

  .bar {
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .wide .bar.left {
    width: var(--bar-left);
  }

  .wide .bar.right {
    width: var(--bar-right);
  }

  /* The paperdoll covers the world on a phone: it is consulted, not read
   * alongside. The log does not -- it sits in its own row, below. */
  .compact .bar.left {
    position: absolute;
    inset: 0;
    z-index: 5;
    box-shadow: var(--shadow);
  }

  .compact .bar.right {
    min-height: 0;
  }

  .centre {
    position: relative;
    min-width: 0;
    min-height: 0;
    display: flex;
    flex-direction: column;
  }

  .tabs {
    position: absolute;
    right: var(--gap-tight);
    top: var(--gap-tight);
    z-index: 10;
    display: flex;
    gap: var(--gap-tight);
  }

  /* Over the world, so translucent and blurred rather than solid: the map
   * should read as continuing underneath the chrome. */
  .tab {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: var(--font-size-small);
    letter-spacing: var(--tracking);
    min-height: 38px;
    padding: 0 var(--gap);
    background: color-mix(in srgb, var(--panel) 78%, transparent);
    backdrop-filter: blur(8px);
  }

  .tab.active {
    border-color: var(--gold);
    color: var(--gold-bright);
  }
</style>
