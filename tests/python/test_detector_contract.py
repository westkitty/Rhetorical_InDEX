import importlib.util
import pathlib
import unittest
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("detector_contract", ROOT / "services" / "api" / "detector_contract.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class DetectorContractTests(unittest.TestCase):
    def setUp(self):
        self.paragraphs = ["Officials refused to explain why the safeguards failed. Either accept monitoring or leave the network."]
        self.valid = {
            "paragraphIndex": 0,
            "exactText": "Either accept monitoring or leave the network",
            "mechanism": "false_dilemma",
            "pressure": "P3",
            "confidence": "Medium",
            "voiceClass": "reporter",
            "triggeredCriteria": ["Binary framing narrows a more complex option space."],
        }

    def test_valid_candidate_resolves_exact_span(self):
        item = MODULE.validate_intrinsic_candidate(self.paragraphs, self.valid)
        self.assertEqual(self.paragraphs[0][item.start_char:item.end_char], self.valid["exactText"])

    def test_rejects_malformed_semantics(self):
        for key, value in [("pressure", "P9"), ("confidence", "Certain"), ("voiceClass", "alien")]:
            bad = dict(self.valid); bad[key] = value
            with self.assertRaises(ValueError): MODULE.validate_intrinsic_candidate(self.paragraphs, bad)

    def test_rejects_missing_criteria_instead_of_fabricating_them(self):
        for value in (None, [], "not-a-list"):
            bad = dict(self.valid); bad["triggeredCriteria"] = value
            with self.assertRaises(ValueError): MODULE.validate_intrinsic_candidate(self.paragraphs, bad)

    def test_rejects_cross_document_mechanism(self):
        bad = dict(self.valid); bad["mechanism"] = "material_omission"
        with self.assertRaises(ValueError): MODULE.validate_intrinsic_candidate(self.paragraphs, bad)

    def test_repeated_excerpt_requires_occurrence(self):
        paragraphs = ["reckless plan, reckless plan"]
        bad = dict(self.valid); bad.update({"exactText": "reckless plan", "mechanism": "loaded_language", "triggeredCriteria": ["Evaluative term."]})
        with self.assertRaises(ValueError): MODULE.validate_intrinsic_candidate(paragraphs, bad)
        good = dict(bad); good["occurrenceIndex"] = 1
        item = MODULE.validate_intrinsic_candidate(paragraphs, good)
        self.assertEqual(item.start_char, 15)


if __name__ == "__main__":
    unittest.main()
