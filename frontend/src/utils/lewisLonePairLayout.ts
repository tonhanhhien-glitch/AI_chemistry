// Balanced, chemistry-style placement of lone-pair electron dots in the Lewis SVG.
//
// Angles are degrees in SVG screen space: 0° points right (+x), 90° points *down*
// (+y), 270° points up. Every angle is normalised to [0, 360).
//
// The placement is a search, not a greedy walk: for each atom we build a set of
// candidate directions, drop the ones sitting in a bond corridor, enumerate every
// combination of `lone_pairs` directions, discard the combinations whose dots would
// collide with something, score the survivors and keep the best-scoring one. Scoring
// is what makes the result look like a textbook diagram rather than merely "not
// overlapping": it rewards bond clearance, even angular spacing of *all* electron
// domains (bonds included) and mirror symmetry about the free side of the atom.

import type { LewisBond, LewisStructure } from "../types/lewis";

export interface Point {
  x: number;
  y: number;
}

export interface BondDirection {
  angle: number;
  order: number;
}

export interface LonePairPlacement {
  angle: number;
  dots: [Point, Point];
}

type AtomLike = { id: string; x: number; y: number; lone_pairs: number };
type BondLike = Pick<LewisBond, "atom1_id" | "atom2_id" | "order">;

// --- Drawing geometry (must stay in sync with LewisSvgRenderer) ----------------

/** Radius of the white atom disc, and of its stroke. */
export const ATOM_RADIUS = 20;
const ATOM_STROKE = 2;
/** Distance from the atom centre to the centre of a lone pair. */
export const LONE_PAIR_RADIUS = 31;
/** Radius of one electron dot. */
export const DOT_RADIUS = 2.2;
/** Centre-to-centre distance between the two dots of a pair. */
export const DOT_GAP = 6;
const BOND_STROKE = 3;
/** Perpendicular offset of the outermost line of a multiple bond, per bond order. */
const BOND_SPREAD: Record<number, number> = { 1: 0, 2: 3.5, 3: 5 };
/** The renderer's viewBox, with the padding that keeps outer dots from clipping. */
export const VIEW_BOX = { minX: -10, minY: -10, width: 340, height: 300 };

// --- Search parameters --------------------------------------------------------

/** Candidate directions every 15°: the 8-point and 12-point sets are both subsets. */
const CANDIDATE_STEP = 15;
/** Half-width of the corridor a bond blocks, by bond order. */
const BOND_EXCLUSION: Record<number, number> = { 1: 25, 2: 32, 3: 38 };
/** Two lone pairs closer than this read as one smeared blob of four dots. */
const MIN_PAIR_SEPARATION = 40;
/** Angles closer than this are treated as the same candidate direction. */
const CANDIDATE_MERGE_TOLERANCE = 2;
const MAX_CONFIGURATIONS = 20000;

const WEIGHTS = { bondClearance: 5, spacing: 3, symmetry: 3 };
/** Breaks exact ties towards the upper side of the atom, the conventional choice. */
const UP = 270;
const TIE_BREAK_WEIGHT = 0.001;

// --- Angle helpers ------------------------------------------------------------

export function normalizeAngle(angle: number): number {
  return ((angle % 360) + 360) % 360;
}

/** Shortest angular distance between two directions, in [0, 180]. */
export function angularDistance(a: number, b: number): number {
  const diff = Math.abs(normalizeAngle(a) - normalizeAngle(b));
  return diff > 180 ? 360 - diff : diff;
}

function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value));
}

// --- Step 1: bond directions --------------------------------------------------

/** Directions of every bond leaving `atomId`, pointing away from the atom. */
export function getBondAngles(atomId: string, atoms: AtomLike[], bonds: BondLike[]): BondDirection[] {
  const byId = new Map(atoms.map((atom) => [atom.id, atom]));
  const self = byId.get(atomId);
  if (!self) return [];
  const directions: BondDirection[] = [];
  for (const bond of bonds) {
    const otherId = bond.atom1_id === atomId ? bond.atom2_id : bond.atom2_id === atomId ? bond.atom1_id : null;
    const other = otherId ? byId.get(otherId) : null;
    if (!other) continue;
    const dx = other.x - self.x;
    const dy = other.y - self.y;
    if (Math.hypot(dx, dy) < 1e-6) continue;
    directions.push({ angle: normalizeAngle((Math.atan2(dy, dx) * 180) / Math.PI), order: bond.order });
  }
  return directions;
}

export function isAngleBlockedByBond(angle: number, bonds: BondDirection[], exclusionScale = 1): boolean {
  return bonds.some((bond) => angularDistance(angle, bond.angle) < (BOND_EXCLUSION[bond.order] ?? BOND_EXCLUSION[1]) * exclusionScale);
}

// --- Step 2: the free sector --------------------------------------------------

/**
 * Free angular intervals around the atom, i.e. what is left once every bond
 * corridor is cut out. Returned as `{ start, size }` walking anti-clockwise in
 * screen space; a bond-free atom yields one full 360° interval.
 */
export function getFreeGaps(bonds: BondDirection[], exclusionScale = 1): { start: number; size: number }[] {
  if (bonds.length === 0) return [{ start: 0, size: 360 }];
  const blocked = bonds
    .map((bond) => ({ angle: normalizeAngle(bond.angle), half: (BOND_EXCLUSION[bond.order] ?? BOND_EXCLUSION[1]) * exclusionScale }))
    .sort((a, b) => a.angle - b.angle);
  const gaps: { start: number; size: number }[] = [];
  for (let i = 0; i < blocked.length; i += 1) {
    const current = blocked[i];
    const next = blocked[(i + 1) % blocked.length];
    // A single bond wraps onto itself: the free sector is everything but its corridor.
    const separation = blocked.length === 1 ? 360 : normalizeAngle(next.angle - current.angle);
    const size = separation - current.half - next.half;
    if (size > 1) gaps.push({ start: normalizeAngle(current.angle + current.half), size });
  }
  return gaps;
}

/**
 * The "largest gap" heuristic, generalised: hand each free interval a share of the
 * lone pairs proportional to its width (largest remainder), then space that share
 * evenly inside the interval. This is the analytic ideal the search is seeded with
 * and the fallback used when no combination survives the collision filter.
 */
export function distributeAcrossFreeGaps(bonds: BondDirection[], lonePairCount: number, exclusionScale = 1): number[] {
  if (lonePairCount <= 0) return [];
  const gaps = getFreeGaps(bonds, exclusionScale).filter((gap) => gap.size > 0);
  if (gaps.length === 0) return evenlySpacedFallback(lonePairCount);
  // A full circle has no edges to space away from, so it divides into `count` arcs
  // rather than `count + 1`.
  if (gaps.length === 1 && gaps[0].size > 359) return evenlySpacedFallback(lonePairCount);
  const total = gaps.reduce((sum, gap) => sum + gap.size, 0);
  const shares = gaps.map((gap) => {
    const exact = (gap.size / total) * lonePairCount;
    return { gap, remainder: exact - Math.floor(exact), count: Math.floor(exact) };
  });
  let remaining = lonePairCount - shares.reduce((sum, share) => sum + share.count, 0);
  for (const share of [...shares].sort((a, b) => b.remainder - a.remainder || b.gap.size - a.gap.size)) {
    if (remaining <= 0) break;
    share.count += 1;
    remaining -= 1;
  }
  const angles: number[] = [];
  for (const { gap, count } of shares) {
    for (let i = 0; i < count; i += 1) angles.push(normalizeAngle(gap.start + (gap.size * (i + 1)) / (count + 1)));
  }
  return angles.sort((a, b) => a - b);
}

function evenlySpacedFallback(lonePairCount: number): number[] {
  return Array.from({ length: lonePairCount }, (_, i) => normalizeAngle(UP + (360 * i) / lonePairCount)).sort((a, b) => a - b);
}

// --- Step 3: candidate directions ---------------------------------------------

/**
 * The 15° grid, plus the directions that make *all* electron domains (bonds and
 * lone pairs alike) evenly spaced, plus the gap-distribution ideal. Seeding the
 * exact ideals means the grid resolution never stops the search from finding the
 * perfectly balanced arrangement — the grid only supplies the alternatives.
 */
export function generateCandidateAngles(bonds: BondDirection[] = [], lonePairCount = 0): number[] {
  const angles: number[] = [];
  for (let angle = 0; angle < 360; angle += CANDIDATE_STEP) angles.push(angle);
  const domainCount = bonds.length + lonePairCount;
  if (domainCount > 0) {
    for (const bond of bonds) {
      for (let k = 1; k < domainCount; k += 1) angles.push(normalizeAngle(bond.angle + (360 * k) / domainCount));
    }
  }
  angles.push(...distributeAcrossFreeGaps(bonds, lonePairCount));
  const unique: number[] = [];
  for (const angle of angles.sort((a, b) => a - b)) {
    if (!unique.some((kept) => angularDistance(kept, angle) < CANDIDATE_MERGE_TOLERANCE)) unique.push(angle);
  }
  return unique;
}

// --- Step 4: combinations -----------------------------------------------------

/** Every combination of `count` candidate directions kept `minSeparation` apart. */
export function buildCandidateConfigurations(angles: number[], count: number, minSeparation = MIN_PAIR_SEPARATION): number[][] {
  if (count <= 0) return [[]];
  const configurations: number[][] = [];
  const chosen: number[] = [];
  const walk = (start: number) => {
    if (chosen.length === count) {
      configurations.push([...chosen]);
      return;
    }
    for (let i = start; i < angles.length; i += 1) {
      if (configurations.length >= MAX_CONFIGURATIONS) return;
      const angle = angles[i];
      if (chosen.some((other) => angularDistance(other, angle) < minSeparation)) continue;
      chosen.push(angle);
      walk(i + 1);
      chosen.pop();
    }
  };
  walk(0);
  return configurations;
}

// --- Step 5: scoring ----------------------------------------------------------

export interface ScoringContext {
  bonds: BondDirection[];
  /** Mirror axis: the middle of the free side of the atom. */
  freeAxis: number;
}

/**
 * The atom's open side: opposite the resultant of the bond directions. For a
 * terminal atom that is simply "away from the neighbour"; for a bond set that
 * already cancels out (trigonal, linear, tetrahedral) there is no preferred side
 * and we fall back to up, which only ever acts as a tie-break.
 */
export function getFreeAxis(bonds: BondDirection[]): number {
  const x = bonds.reduce((sum, bond) => sum + Math.cos((bond.angle * Math.PI) / 180), 0);
  const y = bonds.reduce((sum, bond) => sum + Math.sin((bond.angle * Math.PI) / 180), 0);
  if (Math.hypot(x, y) < 1e-6) return UP;
  return normalizeAngle((Math.atan2(-y, -x) * 180) / Math.PI);
}

/** Worst-case clearance between a lone pair and a bond, 1 at the ideal separation. */
export function bondClearanceScore(config: number[], bonds: BondDirection[]): number {
  if (bonds.length === 0 || config.length === 0) return 1;
  const idealGap = 360 / (bonds.length + config.length);
  const worst = Math.min(...config.map((angle) => Math.min(...bonds.map((bond) => angularDistance(angle, bond.angle)))));
  return clamp01(worst / idealGap);
}

/**
 * How evenly the electron domains — bonds *and* lone pairs — are spread around the
 * atom. Measuring the whole domain set rather than the lone pairs alone is what
 * spreads lone pairs across the free sector instead of pushing them 180° apart
 * regardless of where the bonds are.
 */
export function spacingScore(config: number[], bonds: BondDirection[]): number {
  const domains = [...config, ...bonds.map((bond) => bond.angle)].map(normalizeAngle).sort((a, b) => a - b);
  if (domains.length < 2) return 1;
  const idealGap = 360 / domains.length;
  const gaps = domains.map((angle, i) => normalizeAngle(domains[(i + 1) % domains.length] - angle));
  const minGap = Math.min(...gaps);
  const meanDeviation = gaps.reduce((sum, gap) => sum + Math.abs(gap - idealGap), 0) / gaps.length;
  return 0.6 * clamp01(minGap / idealGap) + 0.4 * clamp01(1 - meanDeviation / idealGap);
}

/** How well the lone-pair set maps onto itself when mirrored about the free axis. */
export function symmetryScore(config: number[], freeAxis: number): number {
  if (config.length === 0) return 1;
  const error =
    config.reduce((sum, angle) => {
      const mirrored = normalizeAngle(2 * freeAxis - angle);
      return sum + Math.min(...config.map((other) => angularDistance(mirrored, other)));
    }, 0) / config.length;
  return clamp01(1 - error / 45);
}

export function scoreConfiguration(config: number[], context: ScoringContext): number {
  const upBias = 1 - config.reduce((sum, angle) => sum + angularDistance(angle, UP), 0) / (config.length * 180 || 1);
  return (
    WEIGHTS.bondClearance * bondClearanceScore(config, context.bonds) +
    WEIGHTS.spacing * spacingScore(config, context.bonds) +
    WEIGHTS.symmetry * symmetryScore(config, context.freeAxis) +
    TIE_BREAK_WEIGHT * upBias
  );
}

export function chooseBestConfiguration(configurations: number[][], context: ScoringContext): number[] | null {
  let best: number[] | null = null;
  let bestScore = -Infinity;
  for (const config of configurations) {
    const score = scoreConfiguration(config, context);
    if (score > bestScore) {
      bestScore = score;
      best = config;
    }
  }
  return best;
}

// --- Step 6: collision rejection ----------------------------------------------

export interface CollisionGeometry {
  atomCenters: Point[];
  bondSegments: { a: Point; b: Point; halfWidth: number }[];
  bounds: { minX: number; minY: number; maxX: number; maxY: number };
}

export function buildCollisionGeometry(atoms: AtomLike[], bonds: BondLike[]): CollisionGeometry {
  const byId = new Map(atoms.map((atom) => [atom.id, atom]));
  const segments: CollisionGeometry["bondSegments"] = [];
  for (const bond of bonds) {
    const a = byId.get(bond.atom1_id);
    const b = byId.get(bond.atom2_id);
    if (!a || !b) continue;
    segments.push({
      a: { x: a.x, y: a.y },
      b: { x: b.x, y: b.y },
      halfWidth: BOND_STROKE / 2 + (BOND_SPREAD[bond.order] ?? 0) + DOT_RADIUS + 2.5,
    });
  }
  return {
    atomCenters: atoms.map((atom) => ({ x: atom.x, y: atom.y })),
    bondSegments: segments,
    bounds: { minX: VIEW_BOX.minX + 1, minY: VIEW_BOX.minY + 1, maxX: VIEW_BOX.minX + VIEW_BOX.width - 1, maxY: VIEW_BOX.minY + VIEW_BOX.height - 1 },
  };
}

function distanceToSegment(point: Point, a: Point, b: Point): number {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const lengthSquared = dx * dx + dy * dy;
  if (lengthSquared < 1e-9) return Math.hypot(point.x - a.x, point.y - a.y);
  const t = Math.max(0, Math.min(1, ((point.x - a.x) * dx + (point.y - a.y) * dy) / lengthSquared));
  return Math.hypot(point.x - (a.x + t * dx), point.y - (a.y + t * dy));
}

/** Dots of one lone pair, laid out tangentially so the pair reads at any angle. */
export function lonePairDots(center: Point, angle: number, radius = LONE_PAIR_RADIUS): [Point, Point] {
  const radians = (angle * Math.PI) / 180;
  const px = center.x + Math.cos(radians) * radius;
  const py = center.y + Math.sin(radians) * radius;
  const ux = -Math.sin(radians) * (DOT_GAP / 2);
  const uy = Math.cos(radians) * (DOT_GAP / 2);
  return [
    { x: px + ux, y: py + uy },
    { x: px - ux, y: py - uy },
  ];
}

export function isConfigurationCollisionFree(atom: Point, config: number[], geometry: CollisionGeometry): boolean {
  const atomClearance = ATOM_RADIUS + ATOM_STROKE / 2 + DOT_RADIUS + 2;
  for (const angle of config) {
    for (const dot of lonePairDots(atom, angle)) {
      if (dot.x - DOT_RADIUS < geometry.bounds.minX || dot.x + DOT_RADIUS > geometry.bounds.maxX) return false;
      if (dot.y - DOT_RADIUS < geometry.bounds.minY || dot.y + DOT_RADIUS > geometry.bounds.maxY) return false;
      if (geometry.atomCenters.some((center) => Math.hypot(dot.x - center.x, dot.y - center.y) < atomClearance)) return false;
      if (geometry.bondSegments.some((segment) => distanceToSegment(dot, segment.a, segment.b) < segment.halfWidth)) return false;
    }
  }
  return true;
}

// --- The pipeline -------------------------------------------------------------

/**
 * Relaxation ladder. The first pass that yields any collision-free combination
 * wins; only a hopelessly crowded atom reaches the analytic fallback.
 */
const ATTEMPTS = [
  { exclusionScale: 1, minSeparation: MIN_PAIR_SEPARATION, checkCollisions: true },
  { exclusionScale: 1, minSeparation: 30, checkCollisions: true },
  { exclusionScale: 0.6, minSeparation: 30, checkCollisions: true },
  { exclusionScale: 0.6, minSeparation: 24, checkCollisions: false },
];

/** Chosen lone-pair directions for one atom, best balanced arrangement first. */
export function placeLonePairs(atom: AtomLike, atoms: AtomLike[], bonds: BondLike[], geometry?: CollisionGeometry): number[] {
  if (atom.lone_pairs <= 0) return [];
  const bondAngles = getBondAngles(atom.id, atoms, bonds);
  const context: ScoringContext = { bonds: bondAngles, freeAxis: getFreeAxis(bondAngles) };
  const collisionGeometry = geometry ?? buildCollisionGeometry(atoms, bonds);
  const candidates = generateCandidateAngles(bondAngles, atom.lone_pairs);
  for (const attempt of ATTEMPTS) {
    const valid = candidates.filter((angle) => !isAngleBlockedByBond(angle, bondAngles, attempt.exclusionScale));
    if (valid.length < atom.lone_pairs) continue;
    const configurations = buildCandidateConfigurations(valid, atom.lone_pairs, attempt.minSeparation).filter(
      (config) => !attempt.checkCollisions || isConfigurationCollisionFree(atom, config, collisionGeometry),
    );
    const best = chooseBestConfiguration(configurations, context);
    if (best) return [...best].sort((a, b) => a - b);
  }
  return distributeAcrossFreeGaps(bondAngles, atom.lone_pairs);
}

/** Lone-pair dot positions for every atom of a structure, keyed by atom id. */
export function layoutLonePairs(structure: Pick<LewisStructure, "atoms" | "bonds">): Record<string, LonePairPlacement[]> {
  const geometry = buildCollisionGeometry(structure.atoms, structure.bonds);
  const layout: Record<string, LonePairPlacement[]> = {};
  for (const atom of structure.atoms) {
    layout[atom.id] = placeLonePairs(atom, structure.atoms, structure.bonds, geometry).map((angle) => ({
      angle,
      dots: lonePairDots({ x: atom.x, y: atom.y }, angle),
    }));
  }
  return layout;
}
