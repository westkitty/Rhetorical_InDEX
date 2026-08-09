import importlib.util
import json
import pathlib
import sys
import unittest

# F-002: prove the Python detector_contract vocabulary cannot silently drift
# from the canonical vocabulary in packages/schema/schema.json (the same
# source tests/vocabulary-parity.test.mjs checks TypeScript against).

ROOT = pathlib.Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("detector_contract", ROOT / "services" / "api" / "detector_contract.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

SCHEMA = json.loads((ROOT / "packages" / "schema" / "schema.json").read_text())
TAXONOMY = json.loads((ROOT / "packages" / "taxonomy" / "taxonomy.json").read_text())


class VocabularyParityTests(unittest.TestCase):
    def test_pressure_confidence_voice_match_canonical_schema(self):
        self.assertEqual(MODULE.PRESSURE, set(SCHEMA["properties"]["pressureLevel"]["enum"]))
        self.assertEqual(MODULE.CONFIDENCE, set(SCHEMA["properties"]["confidenceLevel"]["enum"]))
        self.assertEqual(MODULE.VOICE, set(SCHEMA["properties"]["voiceClass"]["enum"]))

    def test_intrinsic_alpha_slice_matches_canonical_schema(self):
        self.assertEqual(MODULE.INTRINSIC_ALPHA_SLICE, set(SCHEMA["properties"]["intrinsicAlphaSlice"]["enum"]))

    def test_intrinsic_alpha_slice_is_subset_of_taxonomy(self):
        taxonomy_ids = {mechanism["id"] for mechanism in TAXONOMY["mechanisms"]}
        self.assertTrue(MODULE.INTRINSIC_ALPHA_SLICE.issubset(taxonomy_ids))


if __name__ == "__main__":
    unittest.main()
