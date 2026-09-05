<script lang="ts">
  /**
   * The on-screen movement stick.
   *
   * Appears wherever the thumb lands inside its zone rather than sitting in a
   * fixed spot, because a fixed stick on a phone is a stick you have to look
   * at. Pointer events, so a mouse can drive it too -- useful for testing the
   * touch layout on a desktop.
   */
  import { stickVector, type Vector } from "$lib/ui/input";

  interface Props {
    onmove: (vector: Vector) => void;
  }

  let { onmove }: Props = $props();

  let radius = $state(62);
  let origin: { x: number; y: number } | null = $state(null);
  let knob = $state({ x: 0, y: 0 });
  let pointerId: number | null = null;

  function begin(event: PointerEvent) {
    const zone = event.currentTarget as HTMLElement;
    zone.setPointerCapture(event.pointerId);
    pointerId = event.pointerId;
    radius = Number.parseFloat(
      getComputedStyle(zone).getPropertyValue("--stick-radius"),
    ) || 62;
    origin = { x: event.clientX, y: event.clientY };
    knob = { x: 0, y: 0 };
  }

  function drag(event: PointerEvent) {
    if (origin === null || event.pointerId !== pointerId) return;
    const dx = event.clientX - origin.x;
    const dy = event.clientY - origin.y;
    const distance = Math.hypot(dx, dy) || 1;
    const capped = Math.min(distance, radius);
    knob = { x: (dx / distance) * capped, y: (dy / distance) * capped };
    onmove(stickVector(dx, dy, radius));
  }

  function end(event: PointerEvent) {
    if (event.pointerId !== pointerId) return;
    pointerId = null;
    origin = null;
    knob = { x: 0, y: 0 };
    onmove([0, 0]);
  }
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
  class="zone"
  role="application"
  aria-label="Movement stick"
  onpointerdown={begin}
  onpointermove={drag}
  onpointerup={end}
  onpointercancel={end}
>
  {#if origin}
    <div
      class="base"
      style:left="{origin.x}px"
      style:top="{origin.y}px"
      style:width="{radius * 2}px"
      style:height="{radius * 2}px"
    >
      <div class="knob" style:transform="translate({knob.x}px, {knob.y}px)"></div>
    </div>
  {/if}
</div>

<style>
  .zone {
    position: absolute;
    inset: 0;
    touch-action: none; /* the browser must not steal the drag to scroll */
    z-index: 4;
  }

  .base {
    position: fixed;
    translate: -50% -50%;
    border: 2px solid color-mix(in srgb, var(--ink) 25%, transparent);
    border-radius: 50%;
    display: grid;
    place-items: center;
    pointer-events: none;
  }

  .knob {
    width: 42%;
    height: 42%;
    border-radius: 50%;
    background: color-mix(in srgb, var(--accent) 55%, transparent);
  }
</style>
