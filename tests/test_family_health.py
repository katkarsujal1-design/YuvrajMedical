import unittest

from family_health import (
    COMMON_FAMILY_RELATIONS,
    build_family_member_options,
    format_family_member_label,
    normalize_family_member_selection,
)


class FamilyHealthTests(unittest.TestCase):
    def test_common_profiles_are_available(self):
        self.assertEqual(COMMON_FAMILY_RELATIONS[0], "Father")
        self.assertIn("Elderly", COMMON_FAMILY_RELATIONS)

    def test_normalize_family_member_selection_accepts_self_and_member_ids(self):
        family_members = [{"id": 12, "name": "Ravi", "relation": "Father"}]

        self.assertIsNone(normalize_family_member_selection("", family_members))
        self.assertIsNone(normalize_family_member_selection("self", family_members))
        self.assertEqual(normalize_family_member_selection("12", family_members), 12)
        self.assertIsNone(normalize_family_member_selection("99", family_members))

    def test_build_family_member_options_include_self_and_member_labels(self):
        family_members = [{"id": 7, "name": "Priya", "relation": "Mother"}]
        options = build_family_member_options(family_members)

        self.assertEqual(options[0]["label"], "For Myself")
        self.assertEqual(options[1]["label"], "Priya (Mother)")

    def test_format_family_member_label_uses_self_fallback(self):
        self.assertEqual(format_family_member_label(None, None), "For Myself")
        self.assertEqual(format_family_member_label("Asha", "Mother"), "Asha (Mother)")


if __name__ == "__main__":
    unittest.main()
