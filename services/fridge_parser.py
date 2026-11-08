
"""Recognize ingredients from a fridge photo using Gemini AI."""

import json
import os

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

from data.ingredients import INGREDIENTS

load_dotenv()


def get_api_key():
    """Get Gemini API key locally or from Streamlit Cloud."""
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except (KeyError, FileNotFoundError):
            raise ValueError("GEMINI_API_KEY not found.") from None

    return api_key


def scan_fridge(image_bytes, mime_type):
    """Return catalog ingredient keys detected in a fridge photo."""

    if not image_bytes:
        raise ValueError("Please upload a fridge photo.")

    if mime_type not in ("image/jpeg", "image/png"):
        raise ValueError("Only JPG and PNG images are supported.")

    client = genai.Client(api_key=get_api_key())

    catalog = [
        {
            "key": name,
            "display_name": details["display_name"],
            "aliases": details.get("aliases", []),
        }
        for name, details in INGREDIENTS.items()
    ]

    prompt = f"""
    You are an AI fridge ingredient scanner.

    Identify food ingredients visibly present in this fridge photo.

    Return ONLY a JSON object in this format:
    {{
        "ingredients": ["egg", "milk", "tomato"]
    }}

    Rules:
    - Identify only ingredients visible in the photo.
    - Do not invent ingredients.
    - Use only ingredient keys from the catalog below.
    - Consider common packaging, brands, and food appearance.
    - If an item cannot be identified confidently, omit it.
    - Do not assume the fridge contains ingredients not visible.
    - Do not return duplicate ingredients.
    - Do not include quantities, prices, or expiration dates.
    - Return an empty list if no ingredients can be identified.
    - Return valid JSON only.

    Ingredient catalog:
    {json.dumps(catalog, ensure_ascii=False)}
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=[
            prompt,
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type,
            ),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0,
        ),
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    data = json.loads(response.text)

    detected = data.get("ingredients", [])

    if not isinstance(detected, list):
        raise ValueError("Invalid ingredient list returned by Gemini.")

    # Keep only valid catalog keys and remove duplicates.
    ingredients = []
    for name in detected:
        if isinstance(name, str) and name in INGREDIENTS:
            if name not in ingredients:
                ingredients.append(name)

    return ingredients
