<script lang="ts">
  /**
   * Event pills over the world.
   *
   * The log is the record; this is the moment. That game puts what just
   * happened in a translucent pill at the edge of the screen and lets it
   * fade, so the player is never asked to read a panel to find out that
   * something changed -- which matters here, because on a phone the log is
   * a drawer that is usually closed.
   */
  import { Kind, type Entry } from "$lib/log";

  interface Props {
    entries: readonly Entry[];
    /** How long a pill stays up, in milliseconds. */
    life?: number;
  }

  let { entries, life = 5200 }: Props = $props();

  interface Toast {
    id: number;
    text: string;
    kind: Kind;
  }

  let shown = $state<Toast[]>([]);
  let seen = 0;

  $effect(() => {
    const latest = entries;
    // Only what has arrived since the last pass, and only the beats worth
    // interrupting for: a room's name and its prose belong in the log.
    for (const entry of latest.slice(seen)) {
      if (entry.kind !== Kind.EVENT) continue;
      const toast: Toast = { id: entry.id, text: entry.text, kind: entry.kind };
      shown = [...shown, toast];
      setTimeout(() => {
        shown = shown.filter((candidate) => candidate.id !== toast.id);
      }, life);
    }
    seen = latest.length;
  });
</script>

<div class="toasts">
  {#each shown as toast (toast.id)}
    <div class="toast">
      <span class="diamond"></span>
      <span class="text">{toast.text}</span>
    </div>
  {/each}
</div>

<style>
  .toasts {
    position: absolute;
    left: var(--gap);
    top: var(--gap);
    /* Wide enough for a sentence, narrow enough to leave the world visible. */
    width: min(340px, 68%);
    display: flex;
    flex-direction: column;
    gap: 6px;
    pointer-events: none;
    z-index: 6;
  }

  .toast {
    display: flex;
    align-items: baseline;
    gap: var(--gap-tight);
    padding: var(--gap-tight) var(--gap);
    background: color-mix(in srgb, var(--panel) 80%, transparent);
    backdrop-filter: blur(8px);
    border: var(--hairline) solid var(--panel-edge);
    border-radius: 999px;
    box-shadow: var(--shadow);
    animation: rise 260ms ease both;
  }

  .text {
    font-size: var(--font-size-small);
    color: var(--ink);
  }

  @keyframes rise {
    from {
      opacity: 0;
      translate: 0 -8px;
    }
  }

  /* A player who asked for less motion still gets the pill, just not the
   * slide. */
  @media (prefers-reduced-motion: reduce) {
    .toast {
      animation: none;
    }
  }
</style>
