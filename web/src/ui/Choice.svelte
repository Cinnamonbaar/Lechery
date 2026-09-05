<script lang="ts">
  /**
   * One setting: a label on the left, its options on the right.
   *
   * A segmented row rather than that game's dropdowns -- with two or three
   * options a dropdown hides the choice behind a tap for no gain, and on a
   * phone the segments are the bigger target.
   */
  interface Props<T> {
    label: string;
    note?: string;
    value: T;
    options: readonly { value: T; label: string }[];
    onselect: (value: T) => void;
  }

  let { label, note, value, options, onselect }: Props<unknown> = $props();
</script>

<div class="choice">
  <div class="text">
    <span class="name">{label}</span>
    {#if note}<span class="note">{note}</span>{/if}
  </div>
  <div class="options">
    {#each options as option (option.label)}
      <button
        class="segment"
        class:selected={option.value === value}
        onclick={() => onselect(option.value)}
      >
        {#if option.value === value}<span class="diamond"></span>{/if}
        {option.label}
      </button>
    {/each}
  </div>
</div>

<style>
  .choice {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: var(--gap-tight);
    padding: var(--gap-tight) var(--gap);
    background: var(--panel-raised);
    background-image: var(--panel-sheen);
    border: var(--hairline) solid var(--panel-edge);
    /* A card, not a pill: these rows wrap to two lines on a phone, and a
     * 999px radius on a two-line box reads as a lozenge. */
    border-radius: var(--cut-small);
    margin-bottom: var(--gap-tight);
  }

  .text {
    display: flex;
    flex-direction: column;
  }

  .name {
    font-family: var(--font-display);
    color: var(--ink);
  }

  .note {
    font-family: var(--font-ui);
    font-size: var(--font-size-small);
    color: var(--ink-faint);
  }

  .options {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    justify-content: flex-end;
    flex: 1;
  }

  /* Narrow: the options get their own line under the label and share it
   * evenly, rather than each wrapping onto a line of its own. */
  @media (max-width: 560px) {
    .choice {
      flex-direction: column;
      align-items: stretch;
      gap: var(--gap-tight);
      padding: var(--gap);
    }

    .options {
      justify-content: stretch;
    }

    .segment {
      flex: 1;
      justify-content: center;
    }
  }

  .segment {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: var(--font-size-small);
    min-height: 36px;
    padding: 0 var(--gap-tight);
    background: none;
  }
</style>
