/**
 * Movement input, from a keyboard or a thumb.
 *
 * Both produce the same thing: a vector the session can be handed each frame.
 * Keeping them behind one type means nothing downstream has to care which
 * device the player is on, and a machine with both works without a mode.
 */

export type Vector = [number, number];

const KEY_VECTORS: Record<string, Vector> = {
  ArrowUp: [0, -1],
  ArrowDown: [0, 1],
  ArrowLeft: [-1, 0],
  ArrowRight: [1, 0],
  KeyW: [0, -1],
  KeyS: [0, 1],
  KeyA: [-1, 0],
  KeyD: [1, 0],
};

/** Holds the current movement vector from every source at once. */
export class MovementInput {
  private readonly held = new Set<string>();
  /** Set by an on-screen stick; added to whatever the keys say. */
  stick: Vector = [0, 0];

  get vector(): Vector {
    let x = this.stick[0];
    let y = this.stick[1];
    for (const code of this.held) {
      const vector = KEY_VECTORS[code];
      if (!vector) continue;
      x += vector[0];
      y += vector[1];
    }
    return [x, y];
  }

  get active(): boolean {
    const [x, y] = this.vector;
    return x !== 0 || y !== 0;
  }

  /** Returns whether the key was one we use, so the caller can preventDefault. */
  keyDown(code: string): boolean {
    if (!KEY_VECTORS[code]) return false;
    this.held.add(code);
    return true;
  }

  keyUp(code: string): boolean {
    return this.held.delete(code);
  }

  /** Drop everything held. Called when the window loses focus, which is
   * otherwise how a player ends up walking into a wall forever. */
  clear(): void {
    this.held.clear();
    this.stick = [0, 0];
  }
}

/**
 * Turn a touch offset from the stick's centre into a vector.
 *
 * Clamped to the unit circle rather than normalised, so a small movement of
 * the thumb is a slow walk -- an analogue stick, not a d-pad with extra steps.
 */
export function stickVector(dx: number, dy: number, radius: number): Vector {
  const distance = Math.hypot(dx, dy);
  if (distance < radius * 0.12) return [0, 0]; // dead zone
  const magnitude = Math.min(1, distance / radius);
  return [(dx / distance) * magnitude, (dy / distance) * magnitude];
}
