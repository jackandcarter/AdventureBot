const mulberry32 = (seed: number) => {
  return () => {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};

const stringToSeed = (value: string) => {
  let hash = 0;
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash << 5) - hash + value.charCodeAt(i);
    hash |= 0; // Convert to 32bit integer
  }
  return hash >>> 0;
};

export const createSeededRng = (seedString: string) => mulberry32(stringToSeed(seedString) || 1);

export const pickFrom = <T>(rng: () => number, values: T[]): T => {
  const index = Math.floor(rng() * values.length);
  return values[index];
};

export const randomInt = (rng: () => number, min: number, max: number) => {
  return Math.floor(rng() * (max - min + 1)) + min;
};

