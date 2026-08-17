"""Turn internal-coordinate geometry evidence into validated Cartesian coordinates.

NIST CCCBDB and most structural literature publish *internal* coordinates -- a set
of bond lengths, bond angles and dihedrals -- rather than a Cartesian block. This
module solves for coordinates that satisfy every published constraint at once, then
recomputes each constraint back from those coordinates and rejects the fit if any
of them drifts beyond tolerance.

The solver is a Levenberg-Marquardt least-squares fit over a gauge-fixed
parameterisation (atom 0 pinned at the origin, atom 1 on +x, atom 2 in the xy
plane), which removes the six rigid-body degrees of freedom exactly instead of
leaving them to wander. It is deliberately dependency-free: the molecules in
scope have at most eight atoms, so a dense 24x24 normal-equation solve in pure
Python is far cheaper than adding numpy to the deployment image.

Nothing in here knows about any particular molecule.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.schemas.geometry_evidence_schema import (
    GeometryCoordinate,
    MolecularGeometryEvidence,
)

Vector = tuple[float, float, float]

#: Defaults chosen well inside the 0.05 deg reproduction budget the viewer needs.
DEFAULT_LENGTH_TOLERANCE_ANGSTROM = 5e-3
DEFAULT_ANGLE_TOLERANCE_DEG = 2e-2
DEFAULT_DIHEDRAL_TOLERANCE_DEG = 5e-2


@dataclass(frozen=True, slots=True)
class ConstraintCheck:
    """One source constraint recomputed from the fitted coordinates."""

    kind: str
    observation_id: str
    expected: float
    actual: float
    unit: str

    @property
    def deviation(self) -> float:
        if self.unit == "deg":
            return abs(_wrap_degrees(self.actual - self.expected))
        return abs(self.actual - self.expected)


@dataclass(frozen=True, slots=True)
class GeometryFitResult:
    """Outcome of a fit: either accepted coordinates, or an explicit rejection."""

    coordinates: tuple[GeometryCoordinate, ...] | None
    checks: tuple[ConstraintCheck, ...] = ()
    accepted: bool = False
    rejection_reason: str | None = None
    iterations: int = 0
    residual_norm: float = field(default=math.inf)

    @property
    def max_length_deviation(self) -> float:
        return max((check.deviation for check in self.checks if check.kind == "bond_length"), default=0.0)

    @property
    def max_angle_deviation(self) -> float:
        return max((check.deviation for check in self.checks if check.kind == "bond_angle"), default=0.0)

    @property
    def max_dihedral_deviation(self) -> float:
        return max((check.deviation for check in self.checks if check.kind == "dihedral"), default=0.0)


def _wrap_degrees(value: float) -> float:
    """Map an angular difference into (-180, 180]."""

    wrapped = (value + 180.0) % 360.0 - 180.0
    return 180.0 if wrapped == -180.0 else wrapped


def _subtract(left: Vector, right: Vector) -> Vector:
    return (left[0] - right[0], left[1] - right[1], left[2] - right[2])


def _dot(left: Vector, right: Vector) -> float:
    return left[0] * right[0] + left[1] * right[1] + left[2] * right[2]


def _cross(left: Vector, right: Vector) -> Vector:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _norm(vector: Vector) -> float:
    return math.sqrt(_dot(vector, vector))


def distance(first: Vector, second: Vector) -> float:
    return _norm(_subtract(first, second))


def angle_degrees(first: Vector, center: Vector, second: Vector) -> float:
    """A-center-B in degrees. Raises on a zero-length bond vector."""

    left = _subtract(first, center)
    right = _subtract(second, center)
    scale = _norm(left) * _norm(right)
    if scale <= 1e-12:
        raise ValueError("Bond-angle vectors must have non-zero length.")
    return math.degrees(math.acos(max(-1.0, min(1.0, _dot(left, right) / scale))))


def dihedral_degrees(first: Vector, second: Vector, third: Vector, fourth: Vector) -> float:
    """Signed A-B-C-D torsion in degrees using the standard IUPAC convention."""

    b1 = _subtract(second, first)
    b2 = _subtract(third, second)
    b3 = _subtract(fourth, third)
    b2_norm = _norm(b2)
    if b2_norm <= 1e-12:
        raise ValueError("A dihedral needs a non-degenerate central bond.")
    n1 = _cross(b1, b2)
    n2 = _cross(b2, b3)
    m1 = _cross(n1, (b2[0] / b2_norm, b2[1] / b2_norm, b2[2] / b2_norm))
    x = _dot(n1, n2)
    y = _dot(m1, n2)
    return math.degrees(math.atan2(y, x))


# --------------------------------------------------------------------------- #
# Gauge-fixed parameterisation
# --------------------------------------------------------------------------- #


def _variable_slots(atom_count: int) -> list[tuple[int, int]]:
    """(atom index, axis) pairs that are free to move.

    Atom 0 stays at the origin, atom 1 slides along +x and atom 2 stays in the xy
    plane. That pins translation and rotation without adding penalty terms whose
    weights would have to be tuned.
    """

    slots: list[tuple[int, int]] = []
    if atom_count > 1:
        slots.append((1, 0))
    if atom_count > 2:
        slots.extend([(2, 0), (2, 1)])
    for index in range(3, atom_count):
        slots.extend([(index, 0), (index, 1), (index, 2)])
    return slots


def _to_coordinates(values: list[float], slots: list[tuple[int, int]], atom_count: int) -> list[list[float]]:
    coordinates = [[0.0, 0.0, 0.0] for _ in range(atom_count)]
    for value, (atom_index, axis) in zip(values, slots, strict=True):
        coordinates[atom_index][axis] = value
    return coordinates


def _to_variables(coordinates: list[list[float]], slots: list[tuple[int, int]]) -> list[float]:
    return [coordinates[atom_index][axis] for atom_index, axis in slots]


def _gauge_align(points: list[Vector]) -> list[list[float]]:
    """Rotate/translate a point cloud into the gauge: atom0 origin, atom1 on +x, atom2 in xy."""

    origin = points[0]
    shifted = [list(_subtract(point, origin)) for point in points]
    if len(shifted) < 2:
        return shifted
    axis_x = tuple(shifted[1])
    length = _norm(axis_x)
    if length <= 1e-12:
        return shifted
    unit_x: Vector = (axis_x[0] / length, axis_x[1] / length, axis_x[2] / length)
    reference: Vector = tuple(shifted[2]) if len(shifted) > 2 else (0.0, 0.0, 1.0)
    projection = _dot(reference, unit_x)
    residual = (
        reference[0] - projection * unit_x[0],
        reference[1] - projection * unit_x[1],
        reference[2] - projection * unit_x[2],
    )
    residual_norm = _norm(residual)
    if residual_norm <= 1e-9:
        # Collinear reference: any perpendicular direction fixes the remaining spin.
        fallback: Vector = (0.0, 0.0, 1.0) if abs(unit_x[2]) < 0.9 else (0.0, 1.0, 0.0)
        projection = _dot(fallback, unit_x)
        residual = (
            fallback[0] - projection * unit_x[0],
            fallback[1] - projection * unit_x[1],
            fallback[2] - projection * unit_x[2],
        )
        residual_norm = _norm(residual)
    unit_y: Vector = (residual[0] / residual_norm, residual[1] / residual_norm, residual[2] / residual_norm)
    unit_z = _cross(unit_x, unit_y)
    return [[_dot(tuple(point), unit_x), _dot(tuple(point), unit_y), _dot(tuple(point), unit_z)] for point in shifted]


def _fibonacci_directions(count: int, offset: float) -> list[Vector]:
    """Evenly spread unit vectors; a molecule-agnostic starting shape."""

    if count == 1:
        return [(1.0, 0.0, 0.0)]
    golden = math.pi * (3.0 - math.sqrt(5.0))
    directions: list[Vector] = []
    for index in range(count):
        z = 1.0 - 2.0 * (index + 0.5) / count
        radius = math.sqrt(max(0.0, 1.0 - z * z))
        theta = golden * index + offset
        directions.append((radius * math.cos(theta), radius * math.sin(theta), z))
    return directions


# --------------------------------------------------------------------------- #
# Dense linear algebra (small systems only)
# --------------------------------------------------------------------------- #


def _solve(matrix: list[list[float]], rhs: list[float]) -> list[float] | None:
    """Gaussian elimination with partial pivoting; ``None`` when singular."""

    size = len(rhs)
    augmented = [row[:] + [rhs[index]] for index, row in enumerate(matrix)]
    for column in range(size):
        pivot_row = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot_row][column]) < 1e-14:
            return None
        augmented[column], augmented[pivot_row] = augmented[pivot_row], augmented[column]
        pivot = augmented[column][column]
        for row in range(column + 1, size):
            factor = augmented[row][column] / pivot
            if factor:
                for col in range(column, size + 1):
                    augmented[row][col] -= factor * augmented[column][col]
    solution = [0.0] * size
    for row in range(size - 1, -1, -1):
        total = augmented[row][size] - sum(augmented[row][col] * solution[col] for col in range(row + 1, size))
        solution[row] = total / augmented[row][row]
    return solution


# --------------------------------------------------------------------------- #
# Fitting
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class _Constraint:
    kind: str
    observation_id: str
    indexes: tuple[int, ...]
    target: float
    unit: str


def _constraints(evidence: MolecularGeometryEvidence) -> list[_Constraint]:
    index_of = {atom.id: index for index, atom in enumerate(evidence.atoms)}
    constraints: list[_Constraint] = []
    for observation in evidence.bond_lengths:
        constraints.append(_Constraint(
            "bond_length", observation.id,
            (index_of[observation.atom1_id], index_of[observation.atom2_id]),
            observation.value_angstrom, "angstrom",
        ))
    for observation in evidence.bond_angles:
        constraints.append(_Constraint(
            "bond_angle", observation.id,
            (index_of[observation.atom1_id], index_of[observation.center_atom_id], index_of[observation.atom2_id]),
            observation.value_deg, "deg",
        ))
    for observation in evidence.dihedrals:
        constraints.append(_Constraint(
            "dihedral", observation.id,
            (
                index_of[observation.atom1_id], index_of[observation.atom2_id],
                index_of[observation.atom3_id], index_of[observation.atom4_id],
            ),
            observation.value_deg, "deg",
        ))
    return constraints


def _measure(constraint: _Constraint, coordinates: list[list[float]]) -> float:
    points = [tuple(coordinates[index]) for index in constraint.indexes]
    if constraint.kind == "bond_length":
        return distance(points[0], points[1])
    if constraint.kind == "bond_angle":
        return angle_degrees(points[0], points[1], points[2])
    return dihedral_degrees(points[0], points[1], points[2], points[3])


def _residuals(constraints: list[_Constraint], coordinates: list[list[float]]) -> list[float]:
    """Residuals in a common scale: angstroms for lengths, radians for angles."""

    values: list[float] = []
    for constraint in constraints:
        try:
            actual = _measure(constraint, coordinates)
        except ValueError:
            values.append(1e3)
            continue
        if constraint.unit == "deg":
            values.append(math.radians(_wrap_degrees(actual - constraint.target)))
        else:
            values.append(actual - constraint.target)
    return values


def _residual_norm(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values))


def _levenberg_marquardt(
    constraints: list[_Constraint],
    start: list[list[float]],
    slots: list[tuple[int, int]],
    atom_count: int,
    *,
    max_iterations: int,
) -> tuple[list[list[float]], float, int]:
    variables = _to_variables(start, slots)
    size = len(variables)
    coordinates = _to_coordinates(variables, slots, atom_count)
    residuals = _residuals(constraints, coordinates)
    norm = _residual_norm(residuals)
    damping = 1e-3
    step = 1e-6
    iterations = 0
    for iterations in range(1, max_iterations + 1):
        if norm < 1e-12 or size == 0:
            break
        jacobian: list[list[float]] = []
        for column in range(size):
            shifted = variables[:]
            shifted[column] += step
            forward = _residuals(constraints, _to_coordinates(shifted, slots, atom_count))
            shifted[column] -= 2 * step
            backward = _residuals(constraints, _to_coordinates(shifted, slots, atom_count))
            jacobian.append([(high - low) / (2 * step) for high, low in zip(forward, backward, strict=True)])
        normal = [[sum(jacobian[row][k] * jacobian[col][k] for k in range(len(residuals))) for col in range(size)] for row in range(size)]
        gradient = [-sum(jacobian[row][k] * residuals[k] for k in range(len(residuals))) for row in range(size)]
        improved = False
        for _attempt in range(12):
            damped = [row[:] for row in normal]
            for index in range(size):
                damped[index][index] += damping * max(normal[index][index], 1e-9)
            delta = _solve(damped, gradient)
            if delta is None:
                damping *= 10.0
                continue
            candidate = [value + change for value, change in zip(variables, delta, strict=True)]
            candidate_coordinates = _to_coordinates(candidate, slots, atom_count)
            candidate_residuals = _residuals(constraints, candidate_coordinates)
            candidate_norm = _residual_norm(candidate_residuals)
            if candidate_norm < norm:
                variables, residuals, norm = candidate, candidate_residuals, candidate_norm
                damping = max(damping / 10.0, 1e-12)
                improved = True
                break
            damping *= 10.0
        if not improved:
            break
    return _to_coordinates(variables, slots, atom_count), norm, iterations


def _initial_guesses(evidence: MolecularGeometryEvidence, constraints: list[_Constraint]) -> list[list[list[float]]]:
    """Deterministic starting shapes: the source's own coordinates, then spread ligands."""

    guesses: list[list[list[float]]] = []
    if evidence.coordinates is not None:
        order = {atom.id: index for index, atom in enumerate(evidence.atoms)}
        points = [(0.0, 0.0, 0.0)] * len(evidence.atoms)
        for item in evidence.coordinates:
            points[order[item.id]] = (item.x, item.y, item.z)
        guesses.append(_gauge_align(list(points)))
    lengths = [constraint.target for constraint in constraints if constraint.kind == "bond_length"]
    radius = sum(lengths) / len(lengths) if lengths else 1.5
    for offset in (0.0, 0.7, 1.4, 2.1, 2.8):
        directions = _fibonacci_directions(len(evidence.atoms) - 1, offset)
        points = [(0.0, 0.0, 0.0)] + [
            (radius * direction[0], radius * direction[1], radius * direction[2]) for direction in directions
        ]
        guesses.append(_gauge_align(points))
    return guesses


def _check(constraints: list[_Constraint], coordinates: list[list[float]]) -> list[ConstraintCheck]:
    checks: list[ConstraintCheck] = []
    for constraint in constraints:
        try:
            actual = _measure(constraint, coordinates)
        except ValueError:
            actual = math.nan
        checks.append(ConstraintCheck(constraint.kind, constraint.observation_id, constraint.target, actual, constraint.unit))
    return checks


def fit_cartesian_coordinates(
    evidence: MolecularGeometryEvidence,
    *,
    length_tolerance: float = DEFAULT_LENGTH_TOLERANCE_ANGSTROM,
    angle_tolerance_deg: float = DEFAULT_ANGLE_TOLERANCE_DEG,
    dihedral_tolerance_deg: float = DEFAULT_DIHEDRAL_TOLERANCE_DEG,
    max_iterations: int = 200,
) -> GeometryFitResult:
    """Fit coordinates satisfying every observation in ``evidence``, or reject the record.

    A record that already carries Cartesian coordinates is still validated against
    its own observations, so an inconsistent published block is rejected rather
    than silently drawn.
    """

    constraints = _constraints(evidence)
    atom_count = len(evidence.atoms)
    if atom_count < 2:
        return GeometryFitResult(None, rejection_reason="A geometry needs at least two atoms.")
    if not constraints:
        if evidence.coordinates is None:
            return GeometryFitResult(None, rejection_reason="No coordinates and no geometric observations to fit.")
        order = {atom.id: index for index, atom in enumerate(evidence.atoms)}
        points = sorted(evidence.coordinates, key=lambda item: order[item.id])
        return GeometryFitResult(tuple(points), (), True, None, 0, 0.0)

    slots = _variable_slots(atom_count)
    best: tuple[list[list[float]], float, int] | None = None
    for guess in _initial_guesses(evidence, constraints):
        coordinates, norm, iterations = _levenberg_marquardt(
            constraints, guess, slots, atom_count, max_iterations=max_iterations,
        )
        if best is None or norm < best[1]:
            best = (coordinates, norm, iterations)
        if norm < 1e-10:
            break
    assert best is not None
    coordinates, norm, iterations = best
    checks = tuple(_check(constraints, coordinates))
    tolerances = {
        "bond_length": length_tolerance,
        "bond_angle": angle_tolerance_deg,
        "dihedral": dihedral_tolerance_deg,
    }
    violations = [
        f"{check.kind} {check.observation_id}: expected {check.expected:.4f}, fitted {check.actual:.4f}"
        for check in checks
        if math.isnan(check.actual) or check.deviation > tolerances[check.kind]
    ]
    if violations:
        return GeometryFitResult(
            None, checks, False,
            "Fitted coordinates do not reproduce the source constraints: " + "; ".join(violations),
            iterations, norm,
        )
    fitted = tuple(
        GeometryCoordinate(id=atom.id, element=atom.element, x=point[0], y=point[1], z=point[2])
        for atom, point in zip(evidence.atoms, coordinates, strict=True)
    )
    return GeometryFitResult(fitted, checks, True, None, iterations, norm)
