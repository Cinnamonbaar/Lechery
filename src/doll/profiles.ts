/**
 * Body silhouettes measured from the owner's chosen anime body references:
 * a four-figure sheet on a measuring grid, three female and one male. Each
 * profile is sampled every 2% of height from the chin (0.14) down to the
 * soles (0.98), as thousandths of total height, averaged left and right:
 *
 * - torso: half-width of the body, arms included above the armpit
 * - armOut / armIn: outer and inner edge of the arm, once it separates
 * - legOut / legIn: outer and inner edge of each leg, below the crotch
 *
 * The build slider blends between them in order. Measured by a script from
 * the reference image; see docs/art.md. Zero means "not present here".
 */
export interface Profile {
  /** Sample index where the arms separate from the torso. */
  armpit: number;
  /** Sample index where the legs separate. */
  crotch: number;
  torso: number[];
  armOut: number[];
  armIn: number[];
  legOut: number[];
  legIn: number[];
}

/** Height fraction of sample i. */
export const sampleT = (i: number) => 0.14 + i * 0.02;
export const SAMPLES = 43;

export const PROFILES: Profile[] = [
  // male, the straight end
  {
    armpit: 8, crotch: 19,
    torso: [21,21,61,98,102,104,106,110,64,60,60,62,65,74,80,83,85,86,86,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    armOut: [0,0,0,0,0,0,0,0,115,120,125,131,137,140,143,144,146,149,153,156,151,139,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    armIn: [0,0,0,0,0,0,0,0,76,82,90,97,101,107,114,120,126,128,123,140,128,133,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    legOut: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,85,85,83,82,80,78,75,73,74,76,81,87,90,91,90,87,84,82,79,77,77,78,81,87],
    legIn: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,7,9,11,12,14,16,18,21,22,27,26,28,30,33,36,39,41,44,45,44,44,43,38],
  },
  // female
  {
    armpit: 7, crotch: 18,
    torso: [21,21,58,96,101,102,105,64,59,55,54,58,69,79,82,87,89,90,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    armOut: [0,0,0,0,0,0,0,109,112,115,120,126,131,132,133,133,134,136,140,144,138,126,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    armIn: [0,0,0,0,0,0,0,70,74,80,86,90,92,98,104,110,114,115,110,126,115,120,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    legOut: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,89,88,86,84,81,80,78,76,75,76,80,86,89,90,88,85,81,77,73,71,69,69,71,72,75],
    legIn: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,6,10,12,14,17,20,23,27,29,29,33,36,38,39,39,40,40,41,40,40,39,37,34,27],
  },
  // female, the curviest
  {
    armpit: 8, crotch: 19,
    torso: [22,22,53,86,91,92,94,97,56,52,51,54,64,71,78,83,87,90,91,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    armOut: [0,0,0,0,0,0,0,0,99,103,109,115,122,126,129,132,135,137,140,144,139,127,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    armIn: [0,0,0,0,0,0,0,0,62,67,73,80,82,88,96,106,112,115,110,118,116,121,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    legOut: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,91,90,88,86,84,83,81,80,78,81,86,92,95,95,94,91,88,84,80,77,74,74,77,80],
    legIn: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,8,11,13,15,18,21,24,28,29,27,32,35,37,38,39,41,42,44,45,46,44,43,41,38],
  },
];
