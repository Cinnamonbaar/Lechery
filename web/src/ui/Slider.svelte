<script lang="ts">
  /**
   * A labelled slider.
   *
   * One component for every trait in creation, so the row's spacing, hit area
   * and readout are defined once. Adding a trait later is a markup line, not a
   * layout decision.
   */
  interface Props {
    label: string;
    value: number;
    min: number;
    max: number;
    step?: number;
    /** How the current value reads to the player: "C cup", "172cm (tall)". */
    readout?: string;
    oninput: (value: number) => void;
  }

  let { label, value, min, max, step = 1, readout, oninput }: Props = $props();
</script>

<label class="row">
  <span class="label">{label}</span>
  <span class="readout">{readout ?? value}</span>
  <input
    type="range"
    {min}
    {max}
    {step}
    {value}
    oninput={(event) => oninput(Number(event.currentTarget.value))}
  />
</label>

<style>
  .row {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: baseline;
    column-gap: var(--gap-tight);
    margin-bottom: var(--gap-tight);
  }

  .label {
    font-family: var(--font-ui);
    font-size: var(--font-size-small);
    color: var(--ink-dim);
  }

  .readout {
    font-family: var(--font-ui);
    font-size: var(--font-size-small);
    color: var(--accent);
    text-align: right;
  }

  input {
    grid-column: 1 / -1;
    margin: 0;
  }
</style>
