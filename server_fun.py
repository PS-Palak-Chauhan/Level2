# server_fun.py

import logging
logging.disable(logging.CRITICAL)

from mcp.server.fastmcp import FastMCP
from typing import Dict, Any
import requests

mcp = FastMCP("FunTools")


@mcp.tool()
def city_to_coords(city: str) -> Dict[str, Any]:
    """Convert a city name to latitude/longitude using Open-Meteo geocoding."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1, "language": "en"}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        if not results:
            return {"error": f"City '{city}' not found"}
        loc = results[0]
        return {
            "city": loc["name"],
            "country": loc.get("country"),
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "timezone": loc.get("timezone")
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    """Current weather at coordinates via Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,weather_code,wind_speed_10m",
        "timezone": "auto",
        "temperature_unit": "fahrenheit"
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json().get("current", {})


@mcp.tool()
def weather_summary(latitude: float, longitude: float) -> Dict[str, Any]:
    """Returns current weather with a cheerful human-readable description."""
    data = get_weather(latitude, longitude)

    temp_f = data.get("temperature_2m")
    if temp_f is None:
        return {"error": "Could not retrieve weather"}

    wind_kmh = data.get("wind_speed_10m", 0)
    code = data.get("weather_code", 0)

    descriptions = {
        0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
        45: "foggy", 51: "light drizzle", 61: "light rain", 63: "rain",
        65: "heavy rain", 71: "light snow", 73: "snow", 80: "rain showers",
        95: "thunderstorm"
    }
    condition = descriptions.get(code, "unknown weather")

    if temp_f < 32:
        feel = "Freezing cold — perfect for hot cocoa indoors!"
    elif temp_f < 50:
        feel = "Chilly — grab a cozy sweater."
    elif temp_f < 70:
        feel = "Pleasant and mild."
    elif temp_f < 85:
        feel = "Warm and lovely."
    else:
        feel = "Hot — stay hydrated!"

    return {
        "temperature_f": round(temp_f, 1),
        "condition": condition,
        "wind_kmh": round(wind_kmh, 1),
        "summary": f"It's currently {temp_f}°F and {condition} with winds around {wind_kmh} km/h. {feel}"
    }


@mcp.tool()
def book_recs(topic: str = "mystery", limit: int = 3) -> str:
    """Return book recommendations for a given topic."""
    try:
        r = requests.get(
            "https://openlibrary.org/search.json",
            params={"q": topic, "limit": limit},
            timeout=20
        )
        r.raise_for_status()
        docs = r.json().get("docs", [])[:limit]
        if not docs:
            return f"Sorry, no books found for '{topic}'."
        titles = [d.get("title", "Unknown Title") for d in docs]
        return f"Here are some {topic} books:\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))
    except Exception as e:
        return f"Error fetching books: {e}"


@mcp.tool()
def random_joke() -> Dict[str, Any]:
    """Return a safe, single-line joke."""
    r = requests.get("https://v2.jokeapi.dev/joke/Any?type=single&safe-mode", timeout=20)
    r.raise_for_status()
    data = r.json()
    return {"joke": data.get("joke", "No joke found")}


# @mcp.tool()
# def random_dog() -> str:
#     """Return a random dog image URL."""
#     try:
#         r = requests.get("https://dog.ceo/api/breeds/image/random", timeout=20)
#         r.raise_for_status()
#         url = r.json().get("message", "")
#         if not url.startswith("http"):
#             return "https://via.placeholder.com/500?text=No+Dog+Image"
#         return url
#     except Exception:
#         return "https://via.placeholder.com/500?text=No+Dog+Image"


# ---- Dog pic (Dog CEO) ----
@mcp.tool()
def random_dog() -> str:
    """Return a raw random dog image URL."""
    try:
        r = requests.get("https://dog.ceo/api/breeds/image/random", timeout=20)
        r.raise_for_status()
        data = r.json()
        url = data.get("message")
        if not url or not url.startswith("http"):
            return "https://via.placeholder.com/500?text=No+Dog+Image"
        return url  # Only the URL, no text
    except Exception:
        return "https://via.placeholder.com/500?text=No+Dog+Image"


@mcp.tool()
def trivia() -> str:
    """Return one formatted multiple-choice trivia question with answer."""
    import html
    import random

    r = requests.get("https://opentdb.com/api.php?amount=1&type=multiple", timeout=20)
    r.raise_for_status()
    data = r.json().get("results", [])
    if not data:
        return "No trivia available."

    q = data[0]
    question = html.unescape(q["question"])
    correct = html.unescape(q["correct_answer"])
    incorrect = [html.unescape(x) for x in q["incorrect_answers"]]

    options = incorrect + [correct]
    random.shuffle(options)
    labels = ["A", "B", "C", "D"]
    labeled = dict(zip(labels, options))
    correct_label = next(k for k, v in labeled.items() if v == correct)

    lines = [f"Question: {question}", ""]
    for label in labels:
        lines.append(f"  {label}) {labeled[label]}")
    lines.append(f"\nAnswer: {correct_label}) {correct}")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()