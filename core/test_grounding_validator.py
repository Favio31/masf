from core.grounding_validator import verify_quote, determine_status

def test_verify_quote_exact_match():
    source = "El plazo es el 15 de marzo de 2027."
    quote = "15 de marzo de 2027"
    assert verify_quote(source, quote) is True

def test_verify_quote_missing():
    source = "El plazo es el 15 de marzo."
    quote = "15 de abril"
    assert verify_quote(source, quote) is False

def test_determine_status_verified():
    assert determine_status(True, "dato") == "verified"

def test_determine_status_unverified():
    assert determine_status(False, "dato") == "unverified"

def test_determine_status_missing():
    assert determine_status(False, None) == "missing"