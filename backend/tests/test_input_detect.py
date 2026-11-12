from app.utils.input_detect import detect_input


def test_coordinates_comma() -> None:
    d = detect_input("40.7128, -74.0060")
    assert d.kind == "coordinates"
    assert d.lat == 40.7128
    assert d.lon == -74.0060


def test_coordinates_space() -> None:
    d = detect_input("51.5 -0.12")
    assert d.kind == "coordinates"


def test_coordinates_out_of_range_falls_back() -> None:
    d = detect_input("100, 200")
    assert d.kind == "free_text"


def test_us_zip() -> None:
    d = detect_input("10001")
    assert d.kind == "postal_code"
    assert d.postal_code == "10001"
    assert d.country_hint == "us"


def test_uk_postcode() -> None:
    d = detect_input("SW1A 1AA")
    assert d.kind == "postal_code"
    assert d.country_hint == "gb"


def test_canada_postcode() -> None:
    d = detect_input("K1A 0B1")
    assert d.kind == "postal_code"
    assert d.country_hint == "ca"


def test_free_text() -> None:
    d = detect_input("Eiffel Tower")
    assert d.kind == "free_text"
    assert d.raw == "Eiffel Tower"


def test_empty_is_free_text() -> None:
    d = detect_input("   ")
    assert d.kind == "free_text"
    assert d.raw == ""
