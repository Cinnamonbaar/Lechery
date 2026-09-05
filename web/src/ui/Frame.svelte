<script lang="ts">
  /**
   * The three-pane frame: paperdoll, world, log.
   *
   * Wide screens show all three at once; narrow ones show the centre and turn
   * the bars into drawers over it. That is one layout with a class on it
   * rather than two component trees, so a change to a bar cannot land in one
   * view and not the other.
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

  // On a narrow screen a bar floats over the world, so opening one must not
  // also leave the other open on top of it.
  const showLeft = $derived(Boolean(left) && leftOpen);
  const showRight = $derived(Boolean(right) && rightOpen);
</script>

<div class="frame" class:wide class:compact={!wide}>
  {#if showLeft}
    <aside class="bar left">
      {@render left?.()}
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
          onclick={onToggleLeft}>{leftLabel}</button
        >
      {/if}
      {#if right}
        <button
          class="tab"
          class:active={rightOpen}
          aria-pressed={rightOpen}
          onclick={onToggleRight}>{rightLabel}</button
        >
      {/if}
      {#if onSettings}
        <button class="tab" aria-label="Settings" onclick={onSettings}>⚙</button>
      {/if}
    </div>
  </main>

  {#if showRight}
    <aside class="bar right">
      {@render right?.()}
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
    grid-template-rows: 1fr;
    position: relative;
  }

  .bar {
    background: var(--panel);
    border: 1px solid var(--panel-edge);
    border-radius: var(--radius);
    overflow: hidden;
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

  /* Compact: the bar covers the world instead of squeezing it. A phone has
   * no room to do both, and a squeezed world view is worse than a hidden one. */
  .compact .bar {
    position: absolute;
    inset: 0;
    z-index: 5;
    box-shadow: var(--shadow);
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

  .tab {
    font-family: var(--font-ui);
    font-size: var(--font-size-small);
    min-height: 36px;
    padding: 0 var(--gap-tight);
    background: color-mix(in srgb, var(--panel) 82%, transparent);
    backdrop-filter: blur(6px);
  }

  .tab.active {
    border-color: var(--accent);
    color: var(--accent);
  }
</style>
