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


def test_exception_skip_applies_in_both_directions():
    us_sentence = "Please practice the piano each day."
    assert convert(us_sentence, source="en_US", target="en_GB") == us_sentence

    gb_sentence = "Please practise the piano each day."
    assert convert(gb_sentence, source="en_GB", target="en_US") == gb_sentence


def test_exception_conditional_applies_in_both_directions():
    noun_us = "The check arrived today."
    assert convert(noun_us, source="en_US", target="en_GB") == "The cheque arrived today."

    noun_gb = "The cheque arrived today."
    assert convert(noun_gb, source="en_GB", target="en_US") == "The check arrived today."

    noun_upper = "THE check arrived today."
    assert convert(noun_upper, source="en_US", target="en_GB") == "THE cheque arrived today."

    verb_us = "He will check the invoices."
    assert convert(verb_us, source="en_US", target="en_GB") == verb_us

    verb_gb = "He will cheque the invoices."
    assert convert(verb_gb, source="en_GB", target="en_US") == verb_gb
