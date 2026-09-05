<script lang="ts">
  /**
   * The transcript.
   *
   * Sticks to the bottom while the player is already there, and stops sticking
   * the moment they scroll up -- reading back through what happened is the
   * whole reason the log is a transcript rather than a few lines.
   */
  import type { Entry } from "$lib/log";

  interface Props {
    entries: readonly Entry[];
  }

  let { entries }: Props = $props();

  let scroller: HTMLDivElement | undefined = $state();
  let pinned = $state(true);

  function onScroll() {
    if (!scroller) return;
    const distance =
      scroller.scrollHeight - scroller.scrollTop - scroller.clientHeight;
    pinned = distance < 48;
  }

  $effect(() => {
    entries.length;
    if (pinned && scroller) scroller.scrollTop = scroller.scrollHeight;
  });
</script>

<div class="log" bind:this={scroller} onscroll={onScroll}>
  {#each entries as entry (entry.id)}
    <p class="entry {entry.kind}">{entry.text}</p>
  {/each}
</div>

<style>
  .log {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    padding: var(--gap);
    -webkit-overflow-scrolling: touch;
  }

  .entry {
    margin: 0 0 var(--gap-tight);
  }

  .entry.title {
    font-size: var(--font-size-title);
    font-weight: 600;
    margin-top: var(--gap);
    color: var(--ink);
  }

  .entry.prose {
    color: var(--ink-dim);
  }

  .entry.event {
    color: var(--ink);
  }

  .entry.system {
    font-family: var(--font-ui);
    font-size: var(--font-size-small);
    color: var(--ink-faint);
    letter-spacing: 0.02em;
  }
</style>
