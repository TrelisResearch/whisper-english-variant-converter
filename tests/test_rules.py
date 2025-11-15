from english_variant_converter import rules
from english_variant_converter import exception_policies as exception_module


def test_convert_token_preserves_case():
    assert rules.convert_token("Color", "en_US", "en_GB") == "Colour"
    assert rules.convert_token("COLOR", "en_US", "en_GB") == "COLOUR"
    assert rules.convert_token("colour", "en_GB", "en_US") == "color"


def test_convert_token_noop_when_missing():
    assert rules.convert_token("Python", "en_US", "en_GB") == "Python"


def test_exception_policies_handle_missing_file(tmp_path, monkeypatch):
    def fake_files(_package):
        return tmp_path

    monkeypatch.setattr(exception_module.resources, "files", fake_files)
    policies = exception_module.ExceptionPolicies()
    assert policies.classify("check", "cheque").action == ""
