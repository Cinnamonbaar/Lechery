/**
 * World model: geography, and the rules for moving through it.
 *
 * This package imports nothing from the renderer and knows nothing about
 * drawing. It is the authority on where things are; the presentation layer
 * only reads it.
 */

export * from "./direction";
export * from "./roles";
export * from "./exits";
export * from "./room";
export * from "./area";
export * from "./world";
