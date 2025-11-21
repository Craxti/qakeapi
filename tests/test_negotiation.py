import pytest

from qakeapi.core.negotiation import ContentNegotiator, MediaType


def test_media_type_parse_basic():
    media_type = MediaType.parse("application/json")
    assert media_type.type == "application"
    assert media_type.subtype == "json"
    assert media_type.parameters == {}
    assert media_type.q == 1.0


def test_media_type_parse_with_parameters():
    media_type = MediaType.parse('application/json; charset="utf-8"; q=0.8')
    assert media_type.type == "application"
    assert media_type.subtype == "json"
    assert media_type.parameters == {"charset": "utf-8"}
    assert media_type.q == 0.8


def test_media_type_parse_wildcard():
    media_type = MediaType.parse("*/*")
    assert media_type.type == "*"
    assert media_type.subtype == "*"


def test_media_type_matches():
    type1 = MediaType.parse("application/json")
    type2 = MediaType.parse("application/json")
    assert type1.matches(type2)

    type3 = MediaType.parse("application/*")
    assert type3.matches(type1)

    type4 = MediaType.parse("text/html")
    assert not type4.matches(type1)


def test_media_type_matches_with_parameters():
    type1 = MediaType.parse('application/json; charset="utf-8"')
    type2 = MediaType.parse('application/json; charset="utf-8"')
    assert type1.matches(type2)

    type3 = MediaType.parse('application/json; charset="ascii"')
    assert not type1.matches(type3)


def test_media_type_str():
    media_type = MediaType.parse('application/json; charset="utf-8"; q=0.8')
    assert str(media_type) == 'application/json; charset="utf-8"; q=0.8'


def test_content_negotiator_type():
    negotiator = ContentNegotiator()
    negotiator.add_type("application/json")
    negotiator.add_type("text/html")

    # Test with exact match
    result = negotiator.negotiate_type("application/json")
    assert result is not None
    assert str(result) == "application/json"

    # Test with q-value preference
    result = negotiator.negotiate_type(
        "application/xml; q=0.5, application/json; q=0.8"
    )
    assert result is not None
    assert str(result) == "application/json"

    # Test with wildcard
    result = negotiator.negotiate_type("*/*")
    assert result is not None
    assert str(result) == "application/json"

    # Test with no match
    result = negotiator.negotiate_type("application/xml")
    assert result is None


def test_content_negotiator_language():
    negotiator = ContentNegotiator()
    negotiator.add_language("en-US")
    negotiator.add_language("fr")

    # Test exact match
    assert negotiator.negotiate_language("en-US") == "en-US"

    # Test base language match
    assert negotiator.negotiate_language("en") == "en-US"

    # Test with q-values
    assert negotiator.negotiate_language("fr; q=0.8, en-US; q=0.9") == "en-US"

    # Test wildcard
    assert negotiator.negotiate_language("*") == "en-US"

    # Test no match
    assert negotiator.negotiate_language("de") is None

    # Test empty header
    assert negotiator.negotiate_language("") == "en-US"


def test_content_negotiator_encoding():
    negotiator = ContentNegotiator()
    negotiator.add_encoding("gzip")
    negotiator.add_encoding("deflate")

    # Test exact match
    assert negotiator.negotiate_encoding("gzip") == "gzip"

    # Test with q-values
    assert negotiator.negotiate_encoding("deflate; q=0.5, gzip; q=0.8") == "gzip"

    # Test with wildcard
    assert negotiator.negotiate_encoding("*") == "gzip"

    # Test with explicitly forbidden encoding (q=0)
    assert negotiator.negotiate_encoding("gzip; q=0, deflate") == "deflate"

    # Test no match
    assert negotiator.negotiate_encoding("br") is None

    # Test empty header
    assert negotiator.negotiate_encoding("") == "gzip"


def test_content_negotiator_empty():
    negotiator = ContentNegotiator()

    assert negotiator.negotiate_type("") is None
    assert negotiator.negotiate_language("") is None
    assert negotiator.negotiate_encoding("") is None


def test_media_type_parse_invalid():
    # Test parsing invalid media type strings
    media_type = MediaType.parse("invalid")
    assert media_type.type == "invalid"
    assert media_type.subtype == "*"

    media_type = MediaType.parse("")
    assert media_type.type == ""
    assert media_type.subtype == "*"


def test_media_type_parse_with_invalid_q():
    # Test parsing with invalid q value - should default to 1.0
    try:
        media_type = MediaType.parse("application/json; q=invalid")
        assert media_type.q == 1.0
    except ValueError:
        # If implementation throws exception for invalid q, that's also acceptable
        pass
