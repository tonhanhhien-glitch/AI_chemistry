import { createViewer, type GLViewer } from "3dmol";
import { useEffect, useMemo, useRef, useState } from "react";
import { useI18n } from "../../i18n";
import type { BondAngleAnnotation, Structure3D, Vector3D } from "../../types/structure3d";
import ViewerFallback from "./ViewerFallback";
import ViewerToolbar from "./ViewerToolbar";
import type { ViewerStyle } from "./StyleSelector";
import { atomVisualRadius, disposeLonePairObjects, renderLonePairDomains, type LonePairDomainInput } from "./lonePairRenderer";

type ShapeHandle = ReturnType<GLViewer["addLine"]>;
type LabelHandle = ReturnType<GLViewer["addLabel"]>;

function xyzData(structure: Structure3D): string {
  return [String(structure.atoms.length), structure.source_label, ...structure.atoms.map((atom) => `${atom.element} ${atom.x} ${atom.y} ${atom.z}`)].join("\n");
}

function modelData(structure: Structure3D): { data: string; format: "xyz" | "mol" | "sdf" | "pdb" } {
  if (structure.format === "coordinates") return { data: xyzData(structure), format: "xyz" };
  if (!structure.data) throw new Error(`Missing ${structure.format} structure data`);
  return { data: structure.data, format: structure.format === "molblock" ? "mol" : structure.format };
}

function normalize(vector: Vector3D): Vector3D {
  const norm = Math.hypot(vector.x, vector.y, vector.z);
  if (norm === 0) throw new Error("Zero-length overlay vector");
  return { x: vector.x / norm, y: vector.y / norm, z: vector.z / norm };
}

function subtract(left: Vector3D, right: Vector3D): Vector3D {
  return { x: left.x - right.x, y: left.y - right.y, z: left.z - right.z };
}

function angleArc(structure: Structure3D, annotation: BondAngleAnnotation): Vector3D[] {
  const atoms = new Map(structure.atoms.map((atom) => [atom.id, atom]));
  const center = atoms.get(annotation.center_atom_id); const atom1 = atoms.get(annotation.atom1_id); const atom2 = atoms.get(annotation.atom2_id);
  if (!center || !atom1 || !atom2) return [];
  const first = normalize(subtract(atom1, center)); const second = normalize(subtract(atom2, center));
  const cosine = Math.max(-1, Math.min(1, first.x * second.x + first.y * second.y + first.z * second.z));
  const theta = Math.acos(cosine); let perpendicular = subtract(second, { x: first.x * cosine, y: first.y * cosine, z: first.z * cosine });
  if (Math.hypot(perpendicular.x, perpendicular.y, perpendicular.z) < 1e-8) perpendicular = Math.abs(first.x) < 0.9 ? { x: 0, y: -first.z, z: first.y } : { x: -first.y, y: first.x, z: 0 };
  perpendicular = normalize(perpendicular); const radius = 0.75;
  return Array.from({ length: 25 }, (_, index) => {
    const angle = theta * index / 24;
    return { x: center.x + radius * (first.x * Math.cos(angle) + perpendicular.x * Math.sin(angle)), y: center.y + radius * (first.y * Math.cos(angle) + perpendicular.y * Math.sin(angle)), z: center.z + radius * (first.z * Math.cos(angle) + perpendicular.z * Math.sin(angle)) };
  });
}

/** Sphere scale 3Dmol draws atoms at, used as the base scale for the lone-pair lobes. */
function atomSphereScale(style: ViewerStyle): number {
  return style === "space-filling" ? 0.95 : 0.28;
}

/**
 * Turns the engine-supplied non-bonding electron domains into renderer inputs.
 * Directions and domain distances come straight from `structure.electron_domains`; no chemistry
 * is derived here, so the lobes follow whatever VSEPR orientation the backend produced.
 */
function lonePairInputs(structure: Structure3D, style: ViewerStyle): LonePairDomainInput[] {
  const atoms = new Map(structure.atoms.map((atom) => [atom.id, atom]));
  return structure.electron_domains.flatMap((domain) => {
    if (domain.kind !== "lone_pair") return [];
    const atom = atoms.get(domain.center_atom_id);
    if (!atom || Math.hypot(domain.direction.x, domain.direction.y, domain.direction.z) < 1e-9) return [];
    const atomPosition = { x: atom.x, y: atom.y, z: atom.z };
    const distance = Math.hypot(domain.position.x - atom.x, domain.position.y - atom.y, domain.position.z - atom.z);
    return [{
      atomPosition, direction: domain.direction, electronCount: domain.occupancy || 2, domainType: "lonePair" as const,
      atomRadius: atomVisualRadius(atom.element, atomSphereScale(style)),
      domainDistance: distance > 1e-6 ? distance : 1.15,
    }];
  });
}

export default function Molecule3DViewer({ structure }: { structure: Structure3D }) {
  const { t, lang } = useI18n();
  const containerRef = useRef<HTMLDivElement>(null); const viewerRef = useRef<GLViewer | null>(null);
  const atomLabelsRef = useRef<LabelHandle[]>([]); const angleLabelRef = useRef<LabelHandle | null>(null);
  const angleShapesRef = useRef<ShapeHandle[]>([]); const lonePairShapesRef = useRef<ShapeHandle[]>([]);
  const [style, setStyle] = useState<ViewerStyle>("ball-and-stick"); const [labels, setLabels] = useState(true);
  const [angles, setAngles] = useState(true); const [lonePairs, setLonePairs] = useState(true); const [selectedAngleId, setSelectedAngleId] = useState(structure.angle_annotations[0]?.id ?? ""); const [failed, setFailed] = useState(false);
  const selectedAngle = useMemo(() => structure.angle_annotations.find((item) => item.id === selectedAngleId) ?? structure.angle_annotations[0], [selectedAngleId, structure.angle_annotations]);

  useEffect(() => {
    if (!containerRef.current || typeof window.WebGLRenderingContext === "undefined") { setFailed(true); return; }
    try {
      const viewer = createViewer(containerRef.current, { backgroundColor: "#f8fbfa" }); viewerRef.current = viewer;
      const model = modelData(structure); viewer.addModel(model.data, model.format); viewer.zoomTo(); viewer.render();
      return () => { viewer.clear(); viewerRef.current = null; };
    } catch { setFailed(true); }
  }, [structure]);

  useEffect(() => {
    const viewer = viewerRef.current; if (!viewer) return;
    const styles = style === "stick" ? { stick: { radius: 0.18 } } : style === "space-filling" ? { sphere: { scale: 0.95 } } : { stick: { radius: 0.14 }, sphere: { scale: 0.28 } };
    viewer.setStyle({}, styles);
    atomLabelsRef.current.forEach((label) => viewer.removeLabel(label)); atomLabelsRef.current = [];
    if (labels) atomLabelsRef.current = structure.atoms.map((atom) => viewer.addLabel(atom.element, { position: atom, backgroundOpacity: 0.75, fontColor: "white", backgroundColor: "#173f35" }));
    viewer.render();
  }, [labels, structure, style]);

  useEffect(() => {
    const viewer = viewerRef.current; if (!viewer) return;
    angleShapesRef.current.forEach((shape) => viewer.removeShape(shape)); angleShapesRef.current = [];
    if (angleLabelRef.current) viewer.removeLabel(angleLabelRef.current); angleLabelRef.current = null;
    if (angles && selectedAngle) {
      const atoms = new Map(structure.atoms.map((atom) => [atom.id, atom])); const center = atoms.get(selectedAngle.center_atom_id); const atom1 = atoms.get(selectedAngle.atom1_id); const atom2 = atoms.get(selectedAngle.atom2_id);
      const points = angleArc(structure, selectedAngle);
      if (center && atom1 && atom2 && points.length) {
        angleShapesRef.current = [viewer.addLine({ start: center, end: atom1, color: "#d0604c", linewidth: 2 }), viewer.addLine({ start: center, end: atom2, color: "#d0604c", linewidth: 2 }), viewer.addCurve({ points, color: "#d0604c", radius: 0.035 })];
        angleLabelRef.current = viewer.addLabel(selectedAngle.display_label, { position: points[Math.floor(points.length / 2)], backgroundColor: "#8d3528", fontColor: "white", backgroundOpacity: 0.88 });
      }
    }
    viewer.render();
  }, [angles, selectedAngle, structure]);

  useEffect(() => {
    const viewer = viewerRef.current; if (!viewer) return;
    disposeLonePairObjects(viewer, lonePairShapesRef.current); lonePairShapesRef.current = [];
    if (lonePairs) lonePairShapesRef.current = renderLonePairDomains(viewer, lonePairInputs(structure, style));
    viewer.render();
  }, [lonePairs, structure, style]);

  if (failed) return <ViewerFallback />;
  const lonePairCount = structure.electron_domains.filter((domain) => domain.kind === "lone_pair").length;
  return <div className="viewer-wrap">
    <ViewerToolbar style={style} labels={labels} angles={angles} lonePairs={lonePairs} hasAngles={structure.angle_annotations.length > 0} hasLonePairs={lonePairCount > 0} onStyle={setStyle} onLabels={setLabels} onAngles={setAngles} onLonePairs={setLonePairs} />
    {structure.angle_annotations.length > 1 && <label className="angle-selector">{t("viewer3d.angleSelect")}<select value={selectedAngle?.id} onChange={(event) => setSelectedAngleId(event.target.value)}>{structure.angle_annotations.map((annotation) => <option key={annotation.id} value={annotation.id}>{annotation.display_label} · {annotation.atom1_id}–{annotation.center_atom_id}–{annotation.atom2_id}</option>)}</select></label>}
    <div className="mol-viewer" ref={containerRef} aria-label={t("viewer3d.viewerAria")} />
    <div className="viewer-legend" aria-label={t("viewer3d.legend")}><span>● {t("viewer3d.legendAtom")}</span><span>━ {t("viewer3d.legendBond")}</span><span className="legend-lone-pair"><i className="legend-domain-bubble" aria-hidden="true" />●● {t("viewer3d.legendLonePair")}</span></div>
    <p className="viewer-help">{t("viewer3d.help")} {lonePairCount > 0 && (lang === "en" ? "Lone-pair lobes are illustrative regions, not calculated electron-density surfaces." : "Các thùy cặp electron tự do là vùng minh họa, không phải bề mặt mật độ electron được tính toán.")}</p>
  </div>;
}
