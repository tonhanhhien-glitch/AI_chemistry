class FormulaParseError(ValueError):
    code = "INVALID_FORMULA"

    def __init__(self, message="Invalid chemical formula."):
        super().__init__(message)
        self.message = message


class UnsupportedElementError(FormulaParseError):
    code = "UNSUPPORTED_ELEMENT"

    def __init__(self, element):
        super().__init__(f"Element '{element}' is not currently supported.")


class UnsupportedFormulaSyntaxError(FormulaParseError):
    code = "UNSUPPORTED_FORMULA_SYNTAX"