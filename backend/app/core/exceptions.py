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
            "Cú pháp công thức chưa được hỗ trợ. Chỉ dùng công thức phẳng và "
            "điện tích dạng NH4+, NO3- hoặc SO4^2-."
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
        super().__init__(f"Nguyên tố '{symbol}' chưa nằm trong phạm vi hỗ trợ.")


class InvalidAtomCountError(ChemistryDomainError):
    code = "INVALID_ATOM_COUNT"

    def __init__(self, symbol: str, count: object) -> None:
        super().__init__(
            f"Số nguyên tử của {symbol} phải là số nguyên dương; nhận {count!r}."
        )


class UnsupportedMoleculeError(ChemistryDomainError):
    code = "UNSUPPORTED_MOLECULE"

    def __init__(self, query: str) -> None:
        super().__init__(
            f"Chưa có cấu trúc đã kiểm chứng cho '{query}'. "
            "Ứng dụng không suy đoán liên kết chỉ từ thành phần nguyên tố."
        )


class AmbiguousMoleculeError(ChemistryDomainError):
    code = "AMBIGUOUS_MOLECULE"
    status_code = 409

    def __init__(self, candidates: list[dict[str, object]]) -> None:
        super().__init__(
            "Công thức có thể biểu diễn nhiều cấu tạo. Hãy chọn một chất cụ thể.",
            candidates=candidates,
        )


class ChemistryValidationError(ChemistryDomainError):
    code = "CHEMISTRY_VALIDATION_ERROR"
