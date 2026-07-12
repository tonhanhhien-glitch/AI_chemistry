# API specification

The implemented API is served by `backend/app/main.py` under `/api/v1`.
Malformed domain input returns HTTP 422; the API does not encode failures in an
HTTP 200 response.

## Health

`GET /api/v1/health`

Success response (200):

```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

## Parse a formula

`GET /api/v1/formula?formula=SO4%5E2-`

The required `formula` query parameter should be URL encoded by the client.

Success response (200):

```json
{
  "formula": "SO4^2-",
  "atoms": {
    "S": 1,
    "O": 4
  },
  "charge": -2
}
```

Validation response (422):

```json
{
  "detail": {
    "code": "UNSUPPORTED_FORMULA_SYNTAX",
    "message": "Invalid chemical formula."
  }
}
```

Stable domain error codes are `INVALID_FORMULA`,
`UNSUPPORTED_FORMULA_SYNTAX`, and `UNSUPPORTED_ELEMENT`. FastAPI may return
its standard 422 validation shape when the query parameter itself is missing.

## Supported grammar

The parser supports flat formulas made of canonical element symbols followed by
an optional positive count without a leading zero. A missing count means one.
It preserves element capitalization and accumulates repeated elements, so
`CH3COOH` becomes `C: 2, H: 4, O: 2`.

Supported charge suffixes are:

- `+` or `-` for magnitude one, such as `NH4+` and `NO3-`
- `^` followed by a positive magnitude and sign, such as `SO4^2-` and
  `PO4^3-`

Parentheses, hydrates/dot notation, isotopes, leading-zero counts, misplaced
coefficients, and multiple charge suffixes are unsupported. Incorrectly
capitalized input such as `nacl` is rejected rather than repaired.

## Parser scope and chemistry scope

Parsing answers only whether the string has valid supported syntax and returns
its atom inventory and net charge. It does not decide whether a molecule is
appropriate for later Lewis or VSEPR teaching. For example, `CH3COOH` parses
correctly because repeated-element counting is parser behavior. Transition-metal
symbols and elements outside the current main-group allowlist, including `Fe`,
are rejected at this stage.
