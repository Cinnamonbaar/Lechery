/** The whole "framework": make an element, give it properties and children. */
export function h<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  props: Partial<HTMLElementTagNameMap[K]> | string = {},
  ...kids: (Node | string | false | null)[]
): HTMLElementTagNameMap[K] {
  const el = document.createElement(tag);
  Object.assign(el, typeof props === "string" ? { className: props } : props);
  for (const kid of kids) if (kid) el.append(kid);
  return el;
}
