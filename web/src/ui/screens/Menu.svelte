<script lang="ts">
  /**
   * The title screen.
   *
   * Laid out the way that game does its own: the title centred high with a
   * tapered rule under it, one obvious way in, the build string in a corner,
   * and nothing else competing.
   */
  import Rule from "../Rule.svelte";

  interface Props {
    onstart: () => void;
    onsettings: () => void;
    version?: string;
  }

  let { onstart, onsettings, version = "" }: Props = $props();
</script>

<div class="menu">
  <div class="sky"></div>

  <header>
    <h1>Lechery</h1>
    <Rule>Somewhere else this morning</Rule>
  </header>

  <div class="actions">
    <button class="primary" onclick={onstart}>New Game</button>
    <button onclick={onsettings}>Settings</button>
  </div>

  <footer>
    <p>
      Figures drawn with
      <a
        href="https://gitlab.com/PerplexedPeach/dynamic-avatar-drawer"
        target="_blank"
        rel="noreferrer">dynamic-avatar-drawer</a
      >, used under the LGPL v3.
    </p>
    {#if version}<p class="version">{version}</p>{/if}
  </footer>
</div>

<style>
  .menu {
    position: relative;
    height: 100%;
    display: grid;
    grid-template-rows: 1fr auto 1fr;
    place-items: center;
    padding: var(--gap);
    padding-top: max(var(--gap), env(safe-area-inset-top));
    padding-bottom: max(var(--gap), env(safe-area-inset-bottom));
    text-align: center;
    overflow: hidden;
  }

  /* Something behind the title, so the screen is not a flat colour. Two
   * radial washes rather than an image: it themes with the palette and
   * costs nothing to download. */
  .sky {
    position: absolute;
    inset: 0;
    background:
      radial-gradient(
        ellipse at 50% 12%,
        color-mix(in srgb, var(--gold) 16%, transparent),
        transparent 62%
      ),
      radial-gradient(
        ellipse at 50% 108%,
        color-mix(in srgb, var(--gold) 10%, transparent),
        transparent 55%
      );
    pointer-events: none;
  }

  header {
    align-self: end;
    z-index: 1;
    width: min(520px, 100%);
  }

  h1 {
    font-size: clamp(52px, 15vw, 104px);
    line-height: 1.05;
    letter-spacing: 0.1em;
    /* Gold leaf rather than flat gold: the title is the one place worth
     * spending a gradient on. */
    background: linear-gradient(
      170deg,
      var(--gold-bright),
      var(--gold) 55%,
      var(--gold-dim)
    );
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    margin-bottom: var(--gap);
  }

  .actions {
    z-index: 1;
    display: flex;
    flex-direction: column;
    gap: var(--gap-tight);
    width: min(300px, 100%);
    padding: calc(var(--gap) * 2) 0;
  }

  footer {
    align-self: end;
    z-index: 1;
    font-family: var(--font-ui);
    font-size: var(--font-size-small);
    color: var(--ink-faint);
  }

  footer p {
    margin: 0 0 4px;
    max-width: min(460px, 92vw);
  }

  a {
    color: var(--ink-dim);
  }
</style>
