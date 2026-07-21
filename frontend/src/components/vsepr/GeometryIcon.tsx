const points: Record<string, Array<[number, number]>> = {
  linear: [[20, 50], [80, 50]], bent: [[20, 25], [80, 25]], tetrahedral: [[50, 10], [15, 75], [85, 75], [50, 88]],
  "trigonal planar": [[50, 8], [12, 78], [88, 78]], "trigonal pyramidal": [[50, 12], [15, 78], [85, 78]],
  "trigonal bipyramidal": [[50, 5], [50, 95], [8, 50], [75, 18], [75, 82]], seesaw: [[50, 5], [50, 95], [12, 50], [82, 50]],
  "T-shaped": [[50, 8], [50, 92], [88, 50]], octahedral: [[50, 4], [50, 96], [4, 50], [96, 50], [22, 22], [78, 78]],
  "square pyramidal": [[50, 5], [12, 25], [88, 25], [12, 82], [88, 82]], "square planar": [[15, 15], [85, 15], [15, 85], [85, 85]],
};

export default function GeometryIcon({ geometry, label }: { geometry: string; label: string }) {
  const atoms = points[geometry] || points.linear;
  return <svg className="geometry-icon" viewBox="0 0 100 100" role="img" aria-label={label}><title>{label}</title>{atoms.map(([x, y], i) => <line key={`l${i}`} x1="50" y1="50" x2={x} y2={y} />)}<circle className="center" cx="50" cy="50" r="9" />{atoms.map(([x, y], i) => <circle key={`a${i}`} cx={x} cy={y} r="7" />)}</svg>;
}
