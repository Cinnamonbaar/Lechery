<script lang="ts">
  /**
   * A heading on a tapered rule with a diamond at its centre -- the ornament
   * that game puts under anything it wants read as a title.
   */
  interface Props {
    children?: import("svelte").Snippet;
  }

  let { children }: Props = $props();
</script>

<div class="rule">
  {#if children}
    <span class="diamond"></span>
    <span class="text">{@render children()}</span>
    <span class="diamond"></span>
  {:else}
    <span class="diamond"></span>
  {/if}
</div>

<style>
  .text {
    font-family: var(--font-display);
    font-size: var(--font-size-small);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--gold);
    /* Wraps rather than pushing the rule off the screen: a long heading on
     * a narrow phone is the common case, not the exception. */
    text-align: center;
    min-width: 0;
  }
</style>
