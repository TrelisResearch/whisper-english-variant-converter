from english_variant_converter import convert


def test_convert_round_trip():
    sentence = "Color and organize the theater program."
    uk = convert(sentence, source="en_US", target="en_GB")
    assert uk == "Colour and organise the theatre programme."
    us = convert(uk, source="en_GB", target="en_US")
    assert us == "Color and organize the theater program."


def test_convert_with_stats():
    sentence = "The truck parked near the apartment."
    converted, stats = convert(
        sentence, source="en_US", target="en_GB", mode="spelling_and_lexical", return_stats=True
    )
    assert converted == "The lorry parked near the flat."
    assert stats.converted_tokens == 2
    assert any(swap.source == "truck" and swap.target == "lorry" for swap in stats.swaps)
    assert stats.total_tokens == 6
