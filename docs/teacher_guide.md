# Teacher guide

## Before class

1. Complete the chemistry validation protocol for any record used in assessed teaching.
2. Start locally with Docker Compose or the two development servers. Confirm GET /api/v1/health and analyze H2O with external flags off.
3. Set a long random TEACHER_EXPORT_TOKEN and a writable DATA_DIR. Never expose the token in the frontend or slides.
4. Explain that participation in the survey is voluntary and anonymous. Do not ask students to type names, emails, or student numbers.

## Suggested activity

Ask students to predict Lewis structure and geometry before opening an example. In Analysis, compare electron geometry to molecular geometry, rotate the 3D model, and inspect resonance/exception notices. Treat sp3d/sp3d2 only as historical pedagogical labels. The yellow 3D notice means idealized illustration, not measured or quantum-optimized geometry.

Claude can be disabled without losing chemistry functionality. If enabled, its text is explanatory; use the displayed source/fallback notice and report suspicious chemistry through feedback.

## Export

    curl -H "X-Teacher-Token: YOUR_TOKEN" \
      "http://localhost:8000/api/v1/teacher/export?kind=survey" -o survey.csv

Use kind=feedback for feedback. Store exports according to institutional privacy rules. Spreadsheet-formula cells are sanitized, but keep files access-controlled.

## Troubleshooting

- Unsupported syntax: rewrite without parentheses, coefficients, hydrates, or isotopes.
- Unsupported molecule: choose the curated examples; the app will not invent connectivity.
- 3D fallback: Lewis/VSEPR remain valid; check WebGL/browser policy.
- AI fallback: expected when no key/network exists.
- Empty export: no accepted rows or a different DATA_DIR is mounted.
