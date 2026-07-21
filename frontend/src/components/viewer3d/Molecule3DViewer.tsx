import { createViewer, type GLViewer } from "3dmol";
import { useEffect, useRef, useState } from "react";
import type { Structure3D } from "../../types/structure3d";
import ViewerFallback from "./ViewerFallback";
import ViewerToolbar from "./ViewerToolbar";
import type { ViewerStyle } from "./StyleSelector";

export default function Molecule3DViewer({ structure }: { structure: Structure3D }) {
  const containerRef = useRef<HTMLDivElement>(null); const viewerRef = useRef<GLViewer | null>(null);
  const [style, setStyle] = useState<ViewerStyle>("stick"); const [labels, setLabels] = useState(false); const [failed, setFailed] = useState(false);
  useEffect(() => {
    if (!containerRef.current || typeof window.WebGLRenderingContext === "undefined") { setFailed(true); return; }
    try {
      const viewer = createViewer(containerRef.current, { backgroundColor: "#f8fbfa" }); viewerRef.current = viewer;
      const xyz = [String(structure.atoms.length), "VSEPR illustrative coordinates", ...structure.atoms.map((atom) => `${atom.element} ${atom.x} ${atom.y} ${atom.z}`)].join("\n");
      viewer.addModel(xyz, "xyz"); viewer.zoomTo(); viewer.render();
      return () => { viewer.clear(); viewerRef.current = null; };
    } catch { setFailed(true); }
  }, [structure]);
  useEffect(() => {
    const viewer = viewerRef.current; if (!viewer) return;
    viewer.setStyle({}, style === "stick" ? { stick: { radius: 0.16 }, sphere: { scale: 0.28 } } : { sphere: { scale: 0.95 } });
    viewer.removeAllLabels();
    if (labels) structure.atoms.forEach((atom) => viewer.addLabel(atom.element, { position: { x: atom.x, y: atom.y, z: atom.z }, backgroundOpacity: 0.75, fontColor: "white", backgroundColor: "#173f35" }));
    viewer.render();
  }, [labels, structure, style]);
  if (failed) return <ViewerFallback />;
  return <div className="viewer-wrap"><ViewerToolbar style={style} labels={labels} onStyle={setStyle} onLabels={setLabels} onReset={() => { viewerRef.current?.zoomTo(); viewerRef.current?.render(); }} onFullscreen={() => { void containerRef.current?.parentElement?.requestFullscreen?.(); }} /><div className="mol-viewer" ref={containerRef} aria-label="Mô hình phân tử 3D tương tác" /><p className="viewer-help">Kéo để xoay · cuộn/chụm để thu phóng · hỗ trợ cảm ứng.</p>{structure.warning_vi && <p className="warning-note">{structure.warning_vi}</p>}</div>;
}
