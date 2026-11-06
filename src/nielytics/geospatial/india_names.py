"""Official Indian State, Union Territory, and District Name Normalization."""

from __future__ import annotations

import re

# 28 States and 8 Union Territories recognized by the Government of India
INDIAN_STATES_AND_UTS: tuple[str, ...] = (
    # 28 States
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    # 8 Union Territories
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry",
)

# Canonical mapping for historical, abbreviated, and phonetic variants
STATE_ALIASES: dict[str, str] = {
    # Odisha / Orissa
    "orissa": "Odisha",
    "odisha": "Odisha",
    # Uttarakhand / Uttaranchal
    "uttaranchal": "Uttarakhand",
    "uttarakhand": "Uttarakhand",
    # Puducherry / Pondicherry
    "pondicherry": "Puducherry",
    "puducherry": "Puducherry",
    # Karnataka / Mysore
    "mysore": "Karnataka",
    "karnataka": "Karnataka",
    # Tamil Nadu / Madras
    "madras": "Tamil Nadu",
    "tamil nadu": "Tamil Nadu",
    "tamilnadu": "Tamil Nadu",
    # Uttar Pradesh / United Provinces
    "united provinces": "Uttar Pradesh",
    "uttar pradesh": "Uttar Pradesh",
    "up": "Uttar Pradesh",
    # Andhra Pradesh
    "andhra pradesh": "Andhra Pradesh",
    "ap": "Andhra Pradesh",
    # Arunachal Pradesh
    "arunachal pradesh": "Arunachal Pradesh",
    "arunachal": "Arunachal Pradesh",
    # Assam
    "assam": "Assam",
    "asom": "Assam",
    # Bihar
    "bihar": "Bihar",
    # Chhattisgarh
    "chhattisgarh": "Chhattisgarh",
    "chattisgarh": "Chhattisgarh",
    # Goa
    "goa": "Goa",
    # Gujarat
    "gujarat": "Gujarat",
    # Haryana
    "haryana": "Haryana",
    # Himachal Pradesh
    "himachal pradesh": "Himachal Pradesh",
    "himachal": "Himachal Pradesh",
    "hp": "Himachal Pradesh",
    # Jharkhand
    "jharkhand": "Jharkhand",
    # Kerala
    "kerala": "Kerala",
    # Madhya Pradesh
    "madhya pradesh": "Madhya Pradesh",
    "mp": "Madhya Pradesh",
    # Maharashtra
    "maharashtra": "Maharashtra",
    "bombay": "Maharashtra",
    # Manipur
    "manipur": "Manipur",
    # Meghalaya
    "meghalaya": "Meghalaya",
    # Mizoram
    "mizoram": "Mizoram",
    # Nagaland
    "nagaland": "Nagaland",
    # Punjab
    "punjab": "Punjab",
    # Rajasthan
    "rajasthan": "Rajasthan",
    # Sikkim
    "sikkim": "Sikkim",
    # Telangana
    "telangana": "Telangana",
    # Tripura
    "tripura": "Tripura",
    # West Bengal
    "west bengal": "West Bengal",
    "wb": "West Bengal",
    "bengal": "West Bengal",
    # Delhi
    "delhi": "Delhi",
    "nct of delhi": "Delhi",
    "nct delhi": "Delhi",
    "national capital territory of delhi": "Delhi",
    "new delhi": "Delhi",
    # Jammu and Kashmir
    "jammu and kashmir": "Jammu and Kashmir",
    "jammu & kashmir": "Jammu and Kashmir",
    "j&k": "Jammu and Kashmir",
    "j and k": "Jammu and Kashmir",
    # Ladakh
    "ladakh": "Ladakh",
    # Andaman and Nicobar
    "andaman and nicobar islands": "Andaman and Nicobar Islands",
    "andaman & nicobar islands": "Andaman and Nicobar Islands",
    "andaman and nicobar": "Andaman and Nicobar Islands",
    "andaman & nicobar": "Andaman and Nicobar Islands",
    "a&n islands": "Andaman and Nicobar Islands",
    # Chandigarh
    "chandigarh": "Chandigarh",
    # Dadra and Nagar Haveli and Daman and Diu
    "dadra and nagar haveli and daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "dadra & nagar haveli and daman & diu": "Dadra and Nagar Haveli and Daman and Diu",
    "daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "dadra and nagar haveli": "Dadra and Nagar Haveli and Daman and Diu",
    # Lakshadweep
    "lakshadweep": "Lakshadweep",
    "laccadive": "Lakshadweep",
}

DISTRICT_ALIASES: dict[str, str] = {
    # Major city renames
    "bangalore": "Bengaluru Urban",
    "bangalore urban": "Bengaluru Urban",
    "bangalore rural": "Bengaluru Rural",
    "bengaluru": "Bengaluru Urban",
    "gurgaon": "Gurugram",
    "gurugram": "Gurugram",
    "calcutta": "Kolkata",
    "kolkata": "Kolkata",
    "bombay": "Mumbai",
    "mumbai city": "Mumbai",
    "mumbai suburban": "Mumbai Suburban",
    "madras": "Chennai",
    "chennai": "Chennai",
    "allahabad": "Prayagraj",
    "prayagraj": "Prayagraj",
    "banaras": "Varanasi",
    "benares": "Varanasi",
    "varanasi": "Varanasi",
    "faizabad": "Ayodhya",
    "ayodhya": "Ayodhya",
    "ahmedabad": "Ahmedabad",
    "ahmadabad": "Ahmedabad",
    "baroda": "Vadodara",
    "vadodara": "Vadodara",
    "cochin": "Ernakulam",
    "kochi": "Ernakulam",
    "ernakulam": "Ernakulam",
    "trivandrum": "Thiruvananthapuram",
    "thiruvananthapuram": "Thiruvananthapuram",
    "calicut": "Kozhikode",
    "kozhikode": "Kozhikode",
    "mangalore": "Dakshina Kannada",
    "shimoga": "Shivamogga",
    "shivamogga": "Shivamogga",
    "belgaum": "Belagavi",
    "belagavi": "Belagavi",
    "gulbarga": "Kalaburagi",
    "kalaburagi": "Kalaburagi",
    "bellary": "Ballari",
    "ballari": "Ballari",
    "bijapur": "Vijayapura",
    "vijayapura": "Vijayapura",
    "mysore": "Mysuru",
    "mysuru": "Mysuru",
    "pondicherry": "Puducherry",
    "puducherry": "Puducherry",
    "waltair": "Visakhapatnam",
    "vizag": "Visakhapatnam",
    "visakhapatnam": "Visakhapatnam",
    "gauhati": "Kamrup Metropolitan",
    "guwahati": "Kamrup Metropolitan",
    "poona": "Pune",
    "pune": "Pune",
}


def _clean_str(val: str) -> str:
    cleaned = re.sub(r"[^\w\s&]", " ", str(val).lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_state_name(name: str | None) -> str | None:
    """Normalize Indian State or Union Territory name to official Government of India form.

    Returns the canonical title-cased name, or None if unrecognized.
    """
    if name is None or not isinstance(name, str):
        return None
    cleaned = _clean_str(name)
    if not cleaned:
        return None
    return STATE_ALIASES.get(cleaned)


def normalize_district_name(district: str | None, state: str | None = None) -> str | None:
    """Normalize Indian District name, resolving historical and phonetic aliases.

    Optionally context-aware using the state name if provided.
    """
    if district is None or not isinstance(district, str):
        return None
    cleaned = _clean_str(district)
    if not cleaned:
        return None
    if cleaned in DISTRICT_ALIASES:
        return DISTRICT_ALIASES[cleaned]
    # Return Title Case of cleaned name if not specifically aliased
    return " ".join(word.capitalize() for word in cleaned.split())
