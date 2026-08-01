# Chemistry validation protocol

Automated consistency is necessary but is not expert sign-off.

1. Freeze the commit hash and export all records from curated_molecules.json.
2. Assign two qualified chemistry reviewers independently; record names, dates, affiliations, and conflicts outside the repository.
3. For every record verify atom inventory/charge, total valence electrons, skeleton/bond orders, lone pairs, every formal charge, charge sum, resonance equivalence, octet exception, domain counts, AXnEm, both geometries, angle wording, distortion, polarity, and terminology.
4. Verify each external identifier/property against its primary record with retrieval date. Keep unverified values null.
5. Validate every experimental snapshot against formula, charge, atom inventory, identifiers, units, provenance, retrieval date, and the angle recalculated from its Cartesian coordinates. Review other 2D coordinates for legibility and 3D fallback only as idealized illustration.
6. Run backend tests and frontend test/lint/build with all external flags disabled.
7. Resolve disagreements in a signed adjudication log; do not silently average judgments.
8. Change review_status only after both reviewers approve and tests pass.

Regression invariants: local experimental identity matching requires InChIKey plus charge, curated ID plus charge, or a unique explicitly unambiguous formula/charge/inventory match; distinct asymmetric coordinate angles are not merged; PubChem and RDKit remain computed, never experimental; represented electrons equal total valence electrons; formal-charge sum equals molecular charge; steric number is at most 6; AXnEm and geometries match the rule table; resonance/exception flags have notes; AI text cannot contradict immutable fields.

Open external items: broader curated-set expert sign-off, primary-source verification of future CID/measured properties beyond the two explicitly sourced NIST entries, and classroom-language review. They are not claimed complete.
