from english_variant_converter import convert


def test_urls_and_handles_are_not_modified():
    text = "Visit https://example.com or email support@example.com for color info."
    converted = convert(text, source="en_US", target="en_GB")
    assert converted.startswith("Visit https://example.com or email support@example.com")
    assert converted.endswith("colour info.")


def test_protected_tokens_remain():
    text = "Color #channel output in CODE mode."
    converted = convert(text, source="en_US", target="en_GB")
    assert "Colour" in converted
    assert "#channel" in converted
    assert "CODE" in converted
