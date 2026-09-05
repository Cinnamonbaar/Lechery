<script lang="ts">
  /** The game proper: the frame, filled in. */
  import type { Session } from "$lib/session";
  import type { Entry } from "$lib/log";
  import Frame from "../Frame.svelte";
  import LogView from "../LogView.svelte";
  import Paperdoll from "../Paperdoll.svelte";
  import Toasts from "../Toasts.svelte";
  import WorldView from "../WorldView.svelte";

  interface Props {
    session: Session;
    wide: boolean;
    leftOpen: boolean;
    rightOpen: boolean;
    showStick: boolean;
    onToggleLeft: () => void;
    onToggleRight: () => void;
    onSettings: () => void;
  }

  let {
    session,
    wide,
    leftOpen,
    rightOpen,
    showStick,
    onToggleLeft,
    onToggleRight,
    onSettings,
  }: Props = $props();

  // The log is appended to from inside the frame loop, which Svelte cannot
  // see; copying the array on append is what makes the panel update.
  let entries = $state<Entry[]>([]);
  let revision = $state(0);

  $effect(() => {
    const log = session.log;
    entries = [...log.entries];
    log.onAppend = () => {
      entries = [...log.entries];
      // A transformation is logged and drawn in the same moment, so one
      // signal serves both.
      revision += 1;
    };
    return () => {
      log.onAppend = null;
    };
  });
</script>

<Frame
  {wide}
  {leftOpen}
  {rightOpen}
  {onToggleLeft}
  {onToggleRight}
  {onSettings}
  leftLabel="Body"
  rightLabel="Log"
>
  {#snippet left()}
    <Paperdoll character={session.player.character} {revision} />
  {/snippet}

  {#snippet centre()}
    <WorldView {session} {showStick} />
    <Toasts {entries} />
  {/snippet}

  {#snippet right()}
    <LogView {entries} />
  {/snippet}
</Frame>
