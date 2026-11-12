from app.services.tips import WeatherSnapshot, generate_tips


def _codes(tips: list[dict]) -> set[str]:
    return {t["code"] for t in tips}


def test_umbrella_triggers_on_high_probability() -> None:
    tips = generate_tips(WeatherSnapshot(precipitation_probability=70))
    assert "umbrella" in _codes(tips)


def test_umbrella_triggers_on_precip_mm() -> None:
    tips = generate_tips(WeatherSnapshot(precipitation_mm=2.5))
    assert "umbrella" in _codes(tips)


def test_sunscreen_triggers_on_high_uv() -> None:
    tips = generate_tips(WeatherSnapshot(uv_index=7))
    assert "sunscreen" in _codes(tips)


def test_layers_when_swing_exceeds_10c() -> None:
    tips = generate_tips(WeatherSnapshot(temp_min_c=5, temp_max_c=17))
    assert "layers" in _codes(tips)


def test_ice_tip_when_freezing() -> None:
    tips = generate_tips(WeatherSnapshot(temp_min_c=-1))
    assert "ice" in _codes(tips)


def test_heat_tip_when_hot() -> None:
    tips = generate_tips(WeatherSnapshot(temp_max_c=34))
    assert "heat" in _codes(tips)


def test_wind_tip_when_strong_wind() -> None:
    tips = generate_tips(WeatherSnapshot(wind_speed_ms=12))
    assert "wind" in _codes(tips)


def test_aqi_tip_when_poor_air() -> None:
    tips = generate_tips(WeatherSnapshot(air_quality_pm25=40))
    assert "air_quality" in _codes(tips)


def test_no_tips_for_mild_conditions() -> None:
    tips = generate_tips(
        WeatherSnapshot(
            temp_max_c=22, temp_min_c=18, uv_index=3, wind_speed_ms=4, precipitation_probability=10
        )
    )
    assert tips == []


def test_travel_packing_suggestion_combines_signals() -> None:
    tips = generate_tips(
        WeatherSnapshot(
            temp_max_c=28, temp_min_c=8, uv_index=7, precipitation_probability=40, is_travel=True
        )
    )
    travel = next(t for t in tips if t["code"] == "travel_pack")
    assert "light clothing" in travel["message"]
    assert "a warm layer" in travel["message"]
    assert "a rain jacket" in travel["message"]
    assert "sunscreen" in travel["message"]


def test_warnings_sort_before_info() -> None:
    tips = generate_tips(
        WeatherSnapshot(temp_min_c=5, temp_max_c=17, uv_index=8)  # layers=info, sunscreen=warning
    )
    assert tips[0]["severity"] == "warning"
