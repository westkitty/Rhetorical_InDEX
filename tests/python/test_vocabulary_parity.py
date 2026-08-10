import importlib.util
import json
import pathlib
import sys
import unittest

# Review finding N-01: this module is a SCHEMA-LOAD INTEGRITY check, not an
# independent cross-language parity proof. `detector_contract.py` READS
# schema.json, so comparing its values back to schema.json is tautological with
# respect to a schema edit — mutating schema.json leaves these assertions green.
#
# The load-bearing TS<->Python drift detector is
# tests/vocabulary-parity.test.mjs ("TypeScript and Python agree with each
# other"), which compares TypeScript literal unions against Python's RUNTIME
# values and does fail on a schema mutation.
#
# What these tests genuinely establish: the loader works, the enums are
# non-empty and well-formed, the intrinsic slice is a real taxonomy subset, and
# Python's independent behavioral expectations hold.

ROOT = pathlib.Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("detector_contract", ROOT / "services" / "api" / "detector_contract.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

SCHEMA = json.loads((ROOT / "packages" / "schema" / "schema.json").read_text())
TAXONOMY = json.loads((ROOT / "packages" / "taxonomy" / "taxonomy.json").read_text())


class SchemaLoadIntegrityTests(unittest.TestCase):
    """Schema-load integrity. NOT an independent cross-language parity proof."""

    def test_pressure_confidence_voice_match_canonical_schema(self):
        self.assertEqual(MODULE.PRESSURE, set(SCHEMA["properties"]["pressureLevel"]["enum"]))
        self.assertEqual(MODULE.CONFIDENCE, set(SCHEMA["properties"]["confidenceLevel"]["enum"]))
        self.assertEqual(MODULE.VOICE, set(SCHEMA["properties"]["voiceClass"]["enum"]))

    def test_intrinsic_alpha_slice_matches_canonical_schema(self):
        self.assertEqual(MODULE.INTRINSIC_ALPHA_SLICE, set(SCHEMA["properties"]["intrinsicAlphaSlice"]["enum"]))

    def test_intrinsic_alpha_slice_is_subset_of_taxonomy(self):
        taxonomy_ids = {mechanism["id"] for mechanism in TAXONOMY["mechanisms"]}
        self.assertTrue(MODULE.INTRINSIC_ALPHA_SLICE.issubset(taxonomy_ids))

    def test_loader_produces_nonempty_wellformed_enums(self):
        """Independent expectation: a broken loader yields empty/degenerate sets."""
        for name in ("PRESSURE", "CONFIDENCE", "VOICE", "INTRINSIC_ALPHA_SLICE"):
            values = getattr(MODULE, name)
            self.assertIsInstance(values, set, name)
            self.assertTrue(values, f"{name} loaded empty — schema load is broken")
            for value in values:
                self.assertIsInstance(value, str, name)
                self.assertTrue(value.strip(), f"{name} contains a blank value")

    def test_python_behavioral_expectations_independent_of_the_schema_file(self):
        """Values Python's own logic depends on, asserted as literals here.

        Deliberately hard-coded rather than read from schema.json: if the schema
        were edited to drop or rename one of these, Python code that branches on
        them would break, and this test is what catches that — independently of
        whatever the schema currently says.
        """
        self.assertEqual(MODULE.PRESSURE, {"P1", "P2", "P3", "P4"})
        self.assertEqual(MODULE.CONFIDENCE, {"Low", "Medium", "High"})
        self.assertEqual(
            MODULE.INTRINSIC_ALPHA_SLICE,
            {"loaded_language", "presupposition", "agent_suppression", "false_dilemma"},
        )
        for required in ("reporter", "quoted_speaker", "headline", "uncertain"):
            self.assertIn(required, MODULE.VOICE, f"voice class {required!r} is relied on by voice.py")


if __name__ == "__main__":
    unittest.main()
