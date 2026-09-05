<script lang="ts">
  /** The title screen. */
  interface Props {
    onstart: () => void;
    version?: string;
  }

  let { onstart, version = "" }: Props = $props();
</script>

<div class="menu">
  <header>
    <h1>Lechery</h1>
    <p class="tagline">You were somewhere else this morning.</p>
  </header>

  <div class="actions">
    <button class="primary" onclick={onstart}>New game</button>
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
    height: 100%;
    display: grid;
    grid-template-rows: 1fr auto 1fr;
    place-items: center;
    padding: var(--gap);
    text-align: center;
  }

  h1 {
    font-size: clamp(48px, 14vw, 96px);
    letter-spacing: 0.04em;
    margin: 0;
    align-self: end;
  }

  .tagline {
    color: var(--ink-dim);
    margin: var(--gap-tight) 0 0;
  }

  .actions {
    display: flex;
    flex-direction: column;
    gap: var(--gap);
    width: min(320px, 100%);
    padding: var(--gap) 0;
  }

  footer {
    align-self: end;
    font-family: var(--font-ui);
    font-size: var(--font-size-small);
    color: var(--ink-faint);
  }

  footer p {
    margin: 0 0 4px;
  }

  a {
    color: var(--ink-dim);
  }

  .version {
    color: var(--ink-faint);
  }
</style>
