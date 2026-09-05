<script lang="ts">
  /**
   * Character creation.
   *
   * The draft is plain values rather than a Character, and a Character is
   * derived from it. That is what makes the whole screen reactive without the
   * trait model having to know Svelte exists -- Traits keeps its values in a
   * Map, which no framework can observe, and it should stay that way.
   *
   * Layout: on a phone the doll sits at the top with the controls under it, on
   * a wide screen it sits beside them. Same markup either way.
   */
  import { BACKSTORIES, applyBackstory } from "$lib/content/backstories";
  import { Character } from "$lib/traits/character";
  import { GENDERS } from "$lib/traits/identity";
  import { EYE_COLOURS, HAIR_COLOURS, rgbCss } from "$lib/traits/palette";
  import { AGE, BUST, cupSize, HEIGHT, PHALLUS } from "$lib/traits/scale";
  import { Traits } from "$lib/traits/traits";
  import Paperdoll from "../Paperdoll.svelte";
  import Slider from "../Slider.svelte";

  interface Props {
    wide: boolean;
    onbegin: (character: Character) => void;
    onback: () => void;
  }

  let { wide, onbegin, onback }: Props = $props();

  let draft = $state({
    name: "",
    gender: "woman",
    age: 24,
    height: 170,
    hair: 4,
    eye: 3,
    bust: 3,
    phallus: 0,
    backstory: BACKSTORIES[0]!.id,
  });

  const character = $derived.by(() => {
    const built = new Character(
      new Traits({
        name: draft.name.trim() || "Wanderer",
        age: draft.age,
        height: draft.height,
        hair_colour: HAIR_COLOURS[draft.hair]!,
        eye_colour: EYE_COLOURS[draft.eye]!,
        bust: draft.bust,
        phallus: draft.phallus,
      }),
      GENDERS[draft.gender] ?? GENDERS.nonbinary!,
    );
    return built;
  });

  const read = $derived(character.presentation().label);
  const backstory = $derived(
    BACKSTORIES.find((entry) => entry.id === draft.backstory) ?? BACKSTORIES[0]!,
  );

  function begin() {
    const built = character;
    built.backstoryId = backstory.id;
    applyBackstory(backstory, built.stats, built.skills);
    onbegin(built);
  }
</script>

<div class="creation" class:wide class:stacked={!wide}>
  <div class="doll">
    <!-- Never dropped on a phone: what you are building is the point of the
         screen, and a form of sliders with no figure is a settings page. -->
    <Paperdoll {character} revision={draft.bust + draft.phallus + draft.height} />
  </div>

  <div class="form">
    <h2>Who you were</h2>

    <label class="field">
      <span>Name</span>
      <input
        type="text"
        bind:value={draft.name}
        placeholder="Wanderer"
        autocomplete="off"
        spellcheck="false"
      />
    </label>

    <fieldset class="field">
      <legend>Gender</legend>
      <div class="chips">
        {#each Object.entries(GENDERS) as [key, gender] (key)}
          <button
            type="button"
            class="chip"
            class:selected={draft.gender === key}
            onclick={() => (draft.gender = key)}>{gender.label}</button
          >
        {/each}
      </div>
      <p class="note">
        <!-- The whole reason identity and perception are separate axes. -->
        Strangers will read you as <strong>{read}</strong>, whatever you call
        yourself.
      </p>
    </fieldset>

    <h2>The body you woke in</h2>

    <Slider
      label="Age"
      value={draft.age}
      min={AGE.minimum}
      max={AGE.maximum}
      readout={AGE.format(draft.age)}
      oninput={(value) => (draft.age = value)}
    />
    <Slider
      label="Height"
      value={draft.height}
      min={HEIGHT.minimum}
      max={HEIGHT.maximum}
      readout={HEIGHT.format(draft.height)}
      oninput={(value) => (draft.height = value)}
    />
    <Slider
      label="Bust"
      value={draft.bust}
      min={BUST.minimum}
      max={BUST.maximum}
      readout={cupSize(draft.bust)}
      oninput={(value) => (draft.bust = value)}
    />
    <Slider
      label="Endowment"
      value={draft.phallus}
      min={PHALLUS.minimum}
      max={PHALLUS.maximum}
      readout={draft.phallus < 1 ? "none" : PHALLUS.format(draft.phallus)}
      oninput={(value) => (draft.phallus = value)}
    />

    <fieldset class="field">
      <legend>Hair</legend>
      <div class="swatches">
        {#each HAIR_COLOURS as colour, index (colour.name)}
          <button
            type="button"
            class="swatch"
            class:selected={draft.hair === index}
            style:background={rgbCss(colour)}
            aria-label={colour.name}
            title={colour.name}
            onclick={() => (draft.hair = index)}
          ></button>
        {/each}
      </div>
    </fieldset>

    <fieldset class="field">
      <legend>Eyes</legend>
      <div class="swatches">
        {#each EYE_COLOURS as colour, index (colour.name)}
          <button
            type="button"
            class="swatch"
            class:selected={draft.eye === index}
            style:background={rgbCss(colour)}
            aria-label={colour.name}
            title={colour.name}
            onclick={() => (draft.eye = index)}
          ></button>
        {/each}
      </div>
    </fieldset>

    <h2>Before</h2>
    <div class="backstories">
      {#each BACKSTORIES as entry (entry.id)}
        <button
          type="button"
          class="backstory"
          class:selected={draft.backstory === entry.id}
          onclick={() => (draft.backstory = entry.id)}
        >
          <strong>{entry.name}</strong>
          <span>{entry.tagline}</span>
        </button>
      {/each}
    </div>
    <p class="description">{backstory.description}</p>

    <div class="actions">
      <button type="button" onclick={onback}>Back</button>
      <button type="button" class="primary" onclick={begin}>Begin</button>
    </div>
  </div>
</div>

<style>
  .creation {
    height: 100%;
    display: grid;
    gap: var(--gap);
    padding: var(--gap);
    padding-top: max(var(--gap), env(safe-area-inset-top));
    min-height: 0;
  }

  .creation.wide {
    grid-template-columns: minmax(240px, 34%) 1fr;
  }

  .creation.stacked {
    /* Doll on top, controls below: the figure is what the sliders are for,
     * and a phone that hides it turns creation into paperwork. */
    grid-template-rows: minmax(180px, 34%) 1fr;
  }

  .doll {
    background: var(--panel);
    border: 1px solid var(--panel-edge);
    border-radius: var(--radius);
    min-height: 0;
    overflow: hidden;
  }

  .form {
    min-height: 0;
    overflow-y: auto;
    padding-right: var(--gap-tight);
    padding-bottom: max(var(--gap), env(safe-area-inset-bottom));
    -webkit-overflow-scrolling: touch;
  }

  h2 {
    font-size: var(--font-size-title);
    margin: var(--gap) 0 var(--gap-tight);
    color: var(--ink);
  }

  h2:first-child {
    margin-top: 0;
  }

  .field {
    display: block;
    border: none;
    margin: 0 0 var(--gap);
    padding: 0;
  }

  .field > span,
  legend {
    display: block;
    font-family: var(--font-ui);
    font-size: var(--font-size-small);
    color: var(--ink-dim);
    padding: 0 0 4px;
  }

  .chips,
  .swatches {
    display: flex;
    flex-wrap: wrap;
    gap: var(--gap-tight);
  }

  .chip {
    font-size: var(--font-size-small);
  }

  .chip.selected {
    border-color: var(--accent);
    color: var(--accent);
  }

  .swatch {
    width: 40px;
    height: 40px;
    min-height: 40px;
    padding: 0;
    border-radius: 50%;
  }

  .swatch.selected {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
  }

  .note {
    font-size: var(--font-size-small);
    color: var(--ink-faint);
    margin: var(--gap-tight) 0 0;
  }

  .backstories {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: var(--gap-tight);
  }

  .backstory {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
    text-align: left;
    padding: var(--gap-tight);
    min-height: 0;
  }

  .backstory span {
    font-size: var(--font-size-small);
    color: var(--ink-faint);
  }

  .backstory.selected {
    border-color: var(--accent);
  }

  .description {
    color: var(--ink-dim);
    font-size: var(--font-size-small);
  }

  .actions {
    display: flex;
    gap: var(--gap);
    justify-content: flex-end;
    padding: var(--gap) 0;
  }
</style>
