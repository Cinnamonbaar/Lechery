<script lang="ts">
  /**
   * A panel: cut corners, gold hairline, optional titled header.
   *
   * The hairline is the outer element's background showing through a
   * one-pixel pad, because a border cannot follow a clip-path. That is why
   * this is a component rather than a class -- the shape needs two elements,
   * and every screen wanting a panel should not have to remember that.
   */
  import type { Snippet } from "svelte";

  interface Props {
    title?: string;
    /** A glyph before the title, the way that game marks a section. */
    icon?: string;
    onclose?: () => void;
    /** Panels that hold their own scroller manage padding themselves. */
    padded?: boolean;
    children: Snippet;
  }

  let { title, icon, onclose, padded = true, children }: Props = $props();
</script>

<div class="panel">
  <div class="panel-fill">
    {#if title || onclose}
      <header>
        {#if icon}<span class="icon">{icon}</span>{/if}
        {#if title}<h2>{title}</h2>{/if}
        <span class="spacer"></span>
        {#if onclose}
          <button class="close" aria-label="Close" onclick={onclose}>✕</button>
        {/if}
      </header>
    {/if}
    <div class="body" class:padded>
      {@render children()}
    </div>
  </div>
</div>

<style>
  .panel {
    min-height: 0;
    display: flex;
  }

  header {
    display: flex;
    align-items: center;
    gap: var(--gap-tight);
    padding: var(--gap-tight) var(--gap-tight) var(--gap-tight) var(--gap);
    /* The header sits on its own hairline rather than a filled bar: heavier
     * than that and a small panel reads as all chrome. */
    border-bottom: var(--hairline) solid var(--panel-edge);
  }

  .icon {
    color: var(--gold);
    font-size: var(--font-size-title);
    line-height: 1;
  }

  h2 {
    font-size: var(--font-size-title);
    color: var(--ink);
  }

  .spacer {
    flex: 1;
  }

  .body {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
  }

  .body.padded {
    padding: var(--gap);
  }
</style>
