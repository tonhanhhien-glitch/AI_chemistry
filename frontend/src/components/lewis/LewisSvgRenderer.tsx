import { useMemo } from "react";
import { useI18n } from "../../i18n";
import type { LewisStructure } from "../../types/lewis";
import { VIEW_BOX, layoutLonePairs } from "../../utils/lewisLonePairLayout";

export default function LewisSvgRenderer({ structure }: { structure: LewisStructure }) {
  const { t } = useI18n();
  const byId = Object.fromEntries(structure.atoms.map((atom) => [atom.id, atom]));
  // Lone-pair directions are searched for, not fixed: see utils/lewisLonePairLayout.
  const lonePairs = useMemo(() => layoutLonePairs(structure), [structure]);

  return (
    <svg
      className="lewis-svg"
      viewBox={`${VIEW_BOX.minX} ${VIEW_BOX.minY} ${VIEW_BOX.width} ${VIEW_BOX.height}`}
      role="img"
      aria-label={t("lewis.svgAria")}
    >
      <g className="bonds">
        {structure.bonds.flatMap((bond) => {
          const a = byId[bond.atom1_id];
          const b = byId[bond.atom2_id];
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const length = Math.hypot(dx, dy) || 1;
          const ox = (-dy / length) * 5;
          const oy = (dx / length) * 5;
          const offsets = bond.order === 1 ? [0] : bond.order === 2 ? [-0.7, 0.7] : [-1, 0, 1];
          return offsets.map((offset, index) => (
            <line key={`${bond.id}-${index}`} x1={a.x + ox * offset} y1={a.y + oy * offset} x2={b.x + ox * offset} y2={b.y + oy * offset} />
          ));
        })}
      </g>
      {structure.atoms.map((atom) => (
        <g key={atom.id} className="lewis-atom">
          <circle cx={atom.x} cy={atom.y} r="20" />
          <text x={atom.x} y={atom.y + 6}>
            {atom.element}
          </text>
          {(lonePairs[atom.id] ?? []).flatMap((pair, index) =>
            pair.dots.map((dot, dotIndex) => (
              <circle className="electron" key={`${atom.id}-${index}-${dotIndex}`} cx={dot.x} cy={dot.y} r="2.2" />
            )),
          )}
        </g>
      ))}
    </svg>
  );
}
