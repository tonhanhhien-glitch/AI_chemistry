// Localizes a backend English geometry name (e.g. "trigonal planar") through
// the i18n layer, falling back to the raw English name if no translation exists.
import type { useI18n } from "../i18n";

type TranslateFn = ReturnType<typeof useI18n>["t"];

export function geometryLabel(t: TranslateFn, geometry: string): string {
  const key = `geometry.${geometry}`;
  const label = t(key);
  return label === key ? geometry : label;
}
