<script lang="ts">
  /**
   * The world: one canvas, one animation frame loop.
   *
   * The loop lives here rather than in the session because it is a rendering
   * concern; the session is handed a direction and a delta and knows nothing
   * about frames. Backing-store size follows devicePixelRatio, so the map is
   * sharp on a phone instead of being upscaled from CSS pixels.
   */
  import { onMount } from "svelte";

  import type { Session } from "$lib/session";
  import { cameraFor, drawRoom } from "$lib/ui/render";
  import { MovementInput, type Vector } from "$lib/ui/input";
  import { worldPalette } from "$lib/ui/theme";
  import Stick from "./Stick.svelte";

  interface Props {
    session: Session;
    showStick: boolean;
    /** Called after each frame that changed something worth redrawing for. */
    onchange?: () => void;
  }

  let { session, showStick, onchange }: Props = $props();

  let canvas: HTMLCanvasElement;
  let host: HTMLDivElement;
  const input = new MovementInput();

  function stickMoved(vector: Vector) {
    input.stick = vector;
  }

  onMount(() => {
    const context = canvas.getContext("2d");
    if (!context) throw new Error("no 2d context");

    let palette = worldPalette(host);
    let width = 0;
    let height = 0;

    const resize = () => {
      const box = host.getBoundingClientRect();
      const ratio = window.devicePixelRatio || 1;
      width = Math.max(1, Math.round(box.width * ratio));
      height = Math.max(1, Math.round(box.height * ratio));
      canvas.width = width;
      canvas.height = height;
      canvas.style.width = `${box.width}px`;
      canvas.style.height = `${box.height}px`;
      // A theme switch changes computed styles, not the size, but resizing is
      // the only moment we are certain the page has settled.
      palette = worldPalette(host);
    };

    const observer = new ResizeObserver(resize);
    observer.observe(host);
    resize();

    const keydown = (event: KeyboardEvent) => {
      if (input.keyDown(event.code)) event.preventDefault();
    };
    const keyup = (event: KeyboardEvent) => input.keyUp(event.code);
    // Losing focus mid-stride otherwise leaves the player walking into a wall
    // until the key is pressed and released again.
    const blur = () => input.clear();
    window.addEventListener("keydown", keydown);
    window.addEventListener("keyup", keyup);
    window.addEventListener("blur", blur);

    let last = performance.now();
    let frame = 0;
    let entries = session.log.length;

    const tick = (now: number) => {
      // Clamped: a backgrounded tab resumes with a huge delta, which would
      // teleport the player straight through a wall.
      const dt = Math.min(0.05, (now - last) / 1000);
      last = now;

      session.update(input.vector, dt);

      const roomMap = session.roomMap;
      const camera = cameraFor(roomMap, width, height, session.player.position);
      drawRoom(context, width, height, {
        roomMap,
        camera,
        palette,
        player: session.player.position,
        playerRadius: session.player.halfExtents[0] * 1.6,
        facing: session.player.facing,
        portals: session.player.roomId
          ? session.level.portalsIn(session.player.roomId)
          : [],
        time: now,
      });

      if (session.log.length !== entries) {
        entries = session.log.length;
        onchange?.();
      }
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      window.removeEventListener("keydown", keydown);
      window.removeEventListener("keyup", keyup);
      window.removeEventListener("blur", blur);
    };
  });
</script>

<div class="world" bind:this={host}>
  <canvas bind:this={canvas}></canvas>
  {#if showStick}
    <Stick onmove={stickMoved} />
  {/if}
</div>

<style>
  .world {
    position: relative;
    flex: 1;
    min-height: 0;
    border-radius: var(--radius);
    overflow: hidden;
    border: 1px solid var(--panel-edge);
    background: var(--world-void);
  }

  canvas {
    display: block;
    /* Crisp at any zoom: the map is drawn in flat blocks, and smoothing them
     * only makes the edges muddy. */
    image-rendering: pixelated;
  }
</style>
