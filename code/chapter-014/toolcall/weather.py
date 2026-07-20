"""Mock weather backend and tool handlers."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GetWeatherArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    city: str = Field(min_length=1, max_length=64)
    units: str = Field(default="metric", pattern="^(metric|imperial)$")


class ListCitiesArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


_WEATHER = {
    "berlin": {"temp_c": 12.0, "condition": "cloudy"},
    "paris": {"temp_c": 15.5, "condition": "partly cloudy"},
    "tokyo": {"temp_c": 22.0, "condition": "clear"},
    "new york": {"temp_c": 8.0, "condition": "rain"},
}


def list_supported_cities() -> list[str]:
    return sorted(_WEATHER)


def get_weather(city: str, units: str = "metric") -> dict[str, object]:
    key = city.strip().lower()
    if key not in _WEATHER:
        supported = ", ".join(list_supported_cities())
        raise ValueError(f"unsupported city '{city}'. supported: {supported}")
    row = _WEATHER[key]
    temp_c = float(row["temp_c"])
    if units == "imperial":
        temp = round(temp_c * 9 / 5 + 32, 1)
        unit = "F"
    else:
        temp = temp_c
        unit = "C"
    return {
        "city": city.strip(),
        "temperature": temp,
        "units": unit,
        "condition": row["condition"],
        "source": "mock-weather-db",
    }
