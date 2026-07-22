"""Stable domain errors shared by chemistry and API layers."""


class FormulaParseError(ValueError):
    """Base class for formula validation failures."""

    code = "INVALID_FORMULA"

    def __init__(self, message: str = "Invalid chemical formula.") -> None:
        super().__init__(message)
        self.message = message


class UnsupportedElementError(FormulaParseError):
    """Raised when a valid element token is outside the current scope."""

    code = "UNSUPPORTED_ELEMENT"

    def __init__(self, element: str) -> None:
        super().__init__(f"Element '{element}' is not currently supported.")


class UnsupportedFormulaSyntaxError(FormulaParseError):
    """Raised when the complete input does not match the supported grammar."""

    code = "UNSUPPORTED_FORMULA_SYNTAX"

    def __init__(self) -> None:
        super().__init__(
            "Formula syntax not supported. Use only flat formulas and charges "
            "in the form NH4+, NO3- or SO4^2-."
        )


class ChemistryDomainError(ValueError):
    """Base error for deterministic chemistry resolution and validation."""

    code = "CHEMISTRY_ERROR"
    status_code = 422

    def __init__(
        self,
        message: str,
        *,
        candidates: list[dict[str, object]] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.candidates = candidates


class UnknownElementError(ChemistryDomainError):
    code = "UNSUPPORTED_ELEMENT"

    def __init__(self, symbol: str) -> None:
        super().__init__(f"Element '{symbol}' is not within the supported scope.")


class InvalidAtomCountError(ChemistryDomainError):
    code = "INVALID_ATOM_COUNT"

    def __init__(self, symbol: str, count: object) -> None:
        super().__init__(
            f"The atom count of {symbol} must be a positive integer; got {count!r}."
        )


class UnsupportedMoleculeError(ChemistryDomainError):
    code = "UNSUPPORTED_MOLECULE"

    def __init__(self, query: str) -> None:
        super().__init__(
            f"There is no verified structure for '{query}'. "
            "The app does not infer bonding from elemental composition alone."
        )


class AmbiguousMoleculeError(ChemistryDomainError):
    code = "AMBIGUOUS_MOLECULE"
    status_code = 409

    def __init__(self, candidates: list[dict[str, object]]) -> None:
        super().__init__(
            "The formula may represent several structures. Please pick a specific substance.",
            candidates=candidates,
        )


class ChemistryValidationError(ChemistryDomainError):
    code = "CHEMISTRY_VALIDATION_ERROR"
