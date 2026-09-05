<script lang="ts">
  /**
   * The paperdoll: the drawn figure, plus the line of text under it.
   *
   * The library draws into a div of its own, so this component's only jobs are
   * mounting it, scaling it to whatever box the layout gives it, and asking
   * for a redraw when the character changes.
   */
  import { onMount } from "svelte";

  import { AvatarView, NATIVE_SIZE } from "$lib/avatar";
  import type { Character } from "$lib/traits/character";
  import Rule from "./Rule.svelte";

  interface Props {
    character: Character;
    /** Bumped by the caller when traits change; the view diffs its own
     * signature, so an extra nudge costs nothing and a missed one is a stale
     * drawing. */
    revision?: number;
    showSummary?: boolean;
  }

  let { character, revision = 0, showSummary = true }: Props = $props();

  let host: HTMLDivElement;
  let stage: HTMLDivElement;
  let view: AvatarView | null = $state(null);
  let status = $state("loading");
  let scale = $state(1);

  function fit() {
    if (!host) return;
    const box = host.getBoundingClientRect();
    if (!box.width || !box.height) return;
    scale = Math.min(box.width / NATIVE_SIZE[0], box.height / NATIVE_SIZE[1]);
  }

  onMount(() => {
    const created = new AvatarView(stage);
    created.onStatus = (next) => (status = next);
    view = created;
    created.mount().then(() => created.update(character, true));

    fit();
    const observer = new ResizeObserver(fit);
    observer.observe(host);
    return () => {
      observer.disconnect();
      created.destroy();
    };
  });

  // Redraw whenever the character or the caller's revision moves.
  $effect(() => {
    revision;
    view?.update(character);
  });
</script>

<div class="paperdoll">
  <div class="host" bind:this={host}>
    <div
      class="fit"
      style:width="{NATIVE_SIZE[0] * scale}px"
      style:height="{NATIVE_SIZE[1] * scale}px"
    >
      <div
        class="stage"
        bind:this={stage}
        style:transform="scale({scale})"
        style:width="{NATIVE_SIZE[0]}px"
        style:height="{NATIVE_SIZE[1]}px"
      ></div>
    </div>
    {#if status !== "ready"}
      <!-- There is no console on a phone, so this line is the only way a
           failure in the library can be seen at all. -->
      <p class="status">{status}</p>
    {/if}
  </div>

  {#if showSummary}
    <!-- The name plate. Read is on its own line because it is the thing the
         game is about: what you are called, then what strangers see. -->
    <div class="plate">
      <Rule />
      <p class="name">{character.name}</p>
      <p class="read">
        {character.traits.label("height")} &middot; read as {character
          .presentation()
          .label}
      </p>
    </div>
  {/if}
</div>

<style>
  .paperdoll {
    display: flex;
    flex-direction: column;
    min-height: 0;
    height: 100%;
  }

  .host {
    position: relative;
    flex: 1;
    min-height: 0;
    display: grid;
    place-items: center;
    overflow: hidden;
  }

  /* The library's canvases are absolutely positioned, so the stage has to be
   * their containing block -- otherwise they escape it and are laid out
   * against the panel at full size, which draws the figure nowhere useful.
   * Scaled from the top left, inside a box of the scaled size, so the flex
   * centring still sees the right dimensions. */
  .fit {
    position: relative;
  }

  .stage {
    position: absolute;
    inset: 0;
    transform-origin: top left;
    pointer-events: none;
  }

  .status {
    position: absolute;
    inset-inline: var(--gap-tight);
    bottom: var(--gap-tight);
    margin: 0;
    text-align: center;
    font-family: var(--font-ui);
    font-size: var(--font-size-small);
    color: var(--ink-faint);
  }

  .plate {
    padding: var(--gap-tight) var(--gap) var(--gap);
    text-align: center;
  }

  .name {
    font-family: var(--font-display);
    font-size: var(--font-size-title);
    letter-spacing: var(--tracking);
    color: var(--ink);
    margin: var(--gap-tight) 0 2px;
  }

  .read {
    margin: 0;
    font-family: var(--font-ui);
    font-size: var(--font-size-small);
    color: var(--ink-faint);
  }
</style>
