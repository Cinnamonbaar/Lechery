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
    {#if entry.kind === "title"}
      <h3 class="entry title">
        <span class="diamond"></span>
        {entry.text}
      </h3>
    {:else}
      <p class="entry {entry.kind}">{entry.text}</p>
    {/if}
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
    display: flex;
    align-items: center;
    gap: var(--gap-tight);
    font-size: var(--font-size-title);
    letter-spacing: var(--tracking);
    margin-top: var(--gap);
    color: var(--gold-bright);
    /* A hairline under the room name, so scrollback reads as a route with
     * stops rather than one column of prose. */
    padding-bottom: 4px;
    border-bottom: var(--hairline) solid var(--panel-edge);
  }

  .entry.prose {
    color: var(--ink-dim);
  }

  /* An event is something that happened to the body: worth being the
   * brightest thing in the column. */
  .entry.event {
    color: var(--ink);
    padding-left: var(--gap-tight);
    border-left: 2px solid var(--gold-dim);
  }

  .entry.system {
    font-family: var(--font-ui);
    font-size: var(--font-size-small);
    color: var(--ink-faint);
    letter-spacing: 0.02em;
  }
</style>
