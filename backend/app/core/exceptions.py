"""Domain exceptions raised by the formula parser."""


class FormulaParseError(ValueError):
    """Base class for formula validation failures."""

    code = "INVALID_FORMULA"

    def __init__(self, message: str = "Công thức hóa học không hợp lệ.") -> None:
        super().__init__(message)
        self.message = message


class UnsupportedElementError(FormulaParseError):
    """Raised when a valid element token is outside the current scope."""

    code = "UNSUPPORTED_ELEMENT"

    def __init__(self, element: str) -> None:
        super().__init__(f"Nguyên tố '{element}' hiện chưa được hỗ trợ.")


class UnsupportedFormulaSyntaxError(FormulaParseError):
    """Raised when the complete input does not match the supported grammar."""

    code = "UNSUPPORTED_FORMULA_SYNTAX"
