from english_variant_converter import rules


def test_convert_token_preserves_case():
    assert rules.convert_token("Color", "en_US", "en_GB") == "Colour"
    assert rules.convert_token("COLOR", "en_US", "en_GB") == "COLOUR"
    assert rules.convert_token("colour", "en_GB", "en_US") == "color"


def test_convert_token_noop_when_missing():
    assert rules.convert_token("Python", "en_US", "en_GB") == "Python"
