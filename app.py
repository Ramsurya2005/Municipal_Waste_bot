"""
Municipal Issue Reporting Chatbot
Main Streamlit Application
"""

import streamlit as st
from datetime import datetime
import config
import json
import requests
from pathlib import Path
from classifier import IssueClassifier
from auth import UserAuth
from smart_chatbot import SmartChatbot
from PIL import Image, ExifTags
import io
import urllib.request
import urllib.parse
import re
import html
try:
    import exifread
except Exception:
    exifread = None

# Using MySQL Database
from mysql_database import MunicipalDatabase

try:
    from satellite_integration import SatelliteIntegration
    SATELLITE_ENABLED = True
except Exception:
    SATELLITE_ENABLED = False

# Page configuration
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    /* Global Styles */
    :root {
        --primary: #667eea;
        --secondary: #764ba2;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
    }
    
    * {
        transition: all 0.3s ease;
    }
    
    /* Main Header */
    .main-header {
        text-align: center;
        padding: 2.5rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        animation: slideDown 0.6s ease;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    .main-header p {
        margin: 0.5rem 0 0;
        font-size: 1.1rem;
        opacity: 0.95;
        font-weight: 300;
    }
    
    /* Chat Messages */
    .chat-message {
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        border-left: 5px solid;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        animation: fadeIn 0.4s ease;
    }

    .chat-message .message-content {
        line-height: 1.6;
        color: #1e293b;
        white-space: pre-wrap;
        word-break: break-word;
    }
    
    .user-message {
        background: linear-gradient(135deg, #e0e7ff 0%, #dbeafe 100%);
        border-left-color: #667eea;
        margin-left: 2rem;
        border-radius: 15px 15px 5px 15px;
    }
    
    .bot-message {
        background: linear-gradient(135deg, #f3e8ff 0%, #f0fdf4 100%);
        border-left-color: #10b981;
        margin-right: 2rem;
        border-radius: 15px 15px 15px 5px;
    }
    
    /* Stat Boxes */
    .stat-box {
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 2px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .stat-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
        border-color: #667eea;
    }
    
    .stat-box h3 {
        margin: 0;
        color: #667eea;
        font-size: 2rem;
        font-weight: 700;
    }
    
    .stat-box p {
        margin: 0.5rem 0 0;
        color: #64748b;
        font-size: 0.95rem;
    }
    
    /* Welcome Info Box */
    .welcome-box {
        background: linear-gradient(135deg, #fef3c7 0%, #fcd34d 100%);
        border-left: 5px solid #f59e0b;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.2);
    }
    
    /* Department Cards */
    .dept-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        border: 2px solid #e2e8f0;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .dept-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.2);
        border-color: #667eea;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5) !important;
    }
    
    /* Forms */
    .stForm {
        border: 2px solid #e2e8f0 !important;
        border-radius: 15px !important;
        padding: 2rem !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        border-radius: 10px !important;
        border: 2px solid #e2e8f0 !important;
        padding: 0.75rem !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Success/Error Messages */
    .stSuccess {
        background-color: #ecfdf5 !important;
        border: 2px solid #10b981 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }
    
    .stError {
        background-color: #fef2f2 !important;
        border: 2px solid #ef4444 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }
    
    .stWarning {
        background-color: #fffbeb !important;
        border: 2px solid #f59e0b !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }
    
    .stInfo {
        background-color: #eff6ff !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }
    
    /* Animations */
    @keyframes slideDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Spinner Animation */
    .stSpinner {
        color: #667eea !important;
    }
    
    /* Dividers */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
        margin: 2rem 0 !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #1e293b !important;
    }
    
    h1 {
        font-size: 2rem !important;
    }
    
    h2 {
        font-size: 1.5rem !important;
    }
    
    /* Subheaders */
    .stSubheader {
        color: #334155 !important;
        font-weight: 600 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'auth' not in st.session_state:
    st.session_state.auth = UserAuth()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'auth_page' not in st.session_state:
    st.session_state.auth_page = 'login'
if 'classifier' not in st.session_state:
    try:
        st.session_state.classifier = IssueClassifier()
    except Exception:
        class _FallbackClassifier:
            def classify_message(self, text):
                text_lower = text.lower()
                category = "other"
                for cat, info in config.DEPARTMENT_MAPPING.items():
                    if any(keyword in text_lower for keyword in info.get("keywords", [])):
                        category = cat
                        break
                return {
                    "is_valid_issue": True,
                    "category": category,
                    "confidence": 0.85,
                    "summary": text[:200],
                    "location": "Not specified",
                    "urgency": "medium"
                }

            def generate_acknowledgment(self, classification, department_info):
                return (
                    f"Your issue has been registered with {department_info['icon']} "
                    f"{department_info['name']}."
                )
        st.session_state.classifier = _FallbackClassifier()
if 'smart_chatbot' not in st.session_state:
    try:
        st.session_state.smart_chatbot = SmartChatbot()
        print(f"DEBUG: SmartChatbot initialized. ai_available={st.session_state.smart_chatbot.ai_available}")
    except Exception as e:
        print(f"ERROR: Failed to initialize SmartChatbot: {e}")
        st.session_state.smart_chatbot = None
if 'database' not in st.session_state:
    try:
        st.session_state.database = MunicipalDatabase()
    except Exception:
        st.session_state.database = None
if 'satellite' not in st.session_state:
    if SATELLITE_ENABLED:
        try:
            st.session_state.satellite = SatelliteIntegration()
        except Exception:
            st.session_state.satellite = None
    else:
        st.session_state.satellite = None
if 'show_ai_followup' not in st.session_state:
    st.session_state.show_ai_followup = False
if 'pending_complaint_id' not in st.session_state:
    st.session_state.pending_complaint_id = None
if 'pending_issue_text' not in st.session_state:
    st.session_state.pending_issue_text = ""
if 'pending_category' not in st.session_state:
    st.session_state.pending_category = "other"
if 'last_ai_result' not in st.session_state:
    st.session_state.last_ai_result = {}
if 'last_route_info' not in st.session_state:
    st.session_state.last_route_info = {}


def get_google_api_key():
    try:
        with open('satellite_config.json', 'r') as f:
            cfg = json.load(f)
        key = cfg.get('google_maps_api_key', '')
        if key and key != 'YOUR_GOOGLE_MAPS_API_KEY_HERE':
            return key
    except Exception:
        pass
    return ""


def get_coordinates_from_address(address, api_key):
    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": api_key},
            timeout=10
        )
        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}"}
        data = response.json()
        if data.get("status") != "OK" or not data.get("results"):
            return {"success": False, "error": data.get("status", "Location not found")}
        location = data["results"][0]["geometry"]["location"]
        return {
            "success": True,
            "latitude": location["lat"],
            "longitude": location["lng"],
            "formatted_address": data["results"][0]["formatted_address"]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_address_from_coordinates(latitude, longitude, api_key=""):
    try:
        if latitude is None or longitude is None:
            return {"success": False, "error": "Coordinates not provided"}

        lat_lng = f"{latitude},{longitude}"

        if api_key:
            response = requests.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"latlng": lat_lng, "key": api_key},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK" and data.get("results"):
                    return {
                        "success": True,
                        "formatted_address": data["results"][0].get("formatted_address", "")
                    }

        # Fallback without API key (OpenStreetMap Nominatim)
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": latitude,
                "lon": longitude,
                "format": "jsonv2",
                "zoom": 18,
                "addressdetails": 1
            },
            headers={"User-Agent": "municipal-chatbot/1.0"},
            timeout=10
        )
        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}"}
        data = response.json()
        display_name = data.get("display_name")
        if display_name:
            return {"success": True, "formatted_address": display_name}
        return {"success": False, "error": "Address not found"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def geocode_text_location(query_text, api_key=""):
    try:
        if not query_text or not str(query_text).strip():
            return {"success": False, "error": "Empty location text"}

        query_text = str(query_text).strip()

        if api_key:
            response = requests.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": query_text, "key": api_key},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK" and data.get("results"):
                    location = data["results"][0]["geometry"]["location"]
                    return {
                        "success": True,
                        "latitude": location.get("lat"),
                        "longitude": location.get("lng"),
                        "formatted_address": data["results"][0].get("formatted_address", query_text)
                    }

        parts = [part.strip() for part in query_text.split(',') if part.strip()]
        candidates = [query_text]

        if len(parts) > 1:
            candidates.append(', '.join(parts[1:]))
        if len(parts) > 3:
            candidates.append(', '.join(parts[-4:]))
        if len(parts) > 2:
            candidates.append(', '.join(parts[-3:]))

        normalized_candidates = []
        seen = set()
        for candidate in candidates:
            cleaned = re.sub(r'\s+', ' ', candidate).strip(' ,')
            if cleaned and cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                normalized_candidates.append(cleaned)

        last_error = "Location not found"
        for candidate in normalized_candidates:
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": candidate, "format": "jsonv2", "limit": 1},
                headers={"User-Agent": "municipal-chatbot/1.0"},
                timeout=10
            )
            if response.status_code != 200:
                last_error = f"HTTP {response.status_code}"
                continue

            data = response.json()
            if not data:
                continue

            best = data[0]
            return {
                "success": True,
                "latitude": float(best.get("lat")),
                "longitude": float(best.get("lon")),
                "formatted_address": best.get("display_name", candidate)
            }

        return {"success": False, "error": last_error}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_live_traffic_insight(latitude, longitude, api_key):
    try:
        origin = f"{latitude},{longitude}"
        destination = f"{latitude + 0.02},{longitude + 0.02}"
        response = requests.get(
            "https://maps.googleapis.com/maps/api/distancematrix/json",
            params={
                "origins": origin,
                "destinations": destination,
                "departure_time": "now",
                "traffic_model": "best_guess",
                "key": api_key
            },
            timeout=10
        )
        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}"}
        data = response.json()
        if data.get("status") != "OK":
            return {"success": False, "error": data.get("status", "API error")}
        element = data["rows"][0]["elements"][0]
        if element.get("status") != "OK":
            return {"success": False, "error": element.get("status", "No route")}

        normal = element.get("duration", {}).get("value")
        traffic = element.get("duration_in_traffic", {}).get("value")
        if not normal or not traffic:
            return {"success": False, "error": "Missing traffic metrics"}

        multiplier = traffic / normal
        delay_minutes = max((traffic - normal) / 60, 0)
        high_traffic = multiplier >= 1.4 or delay_minutes >= 10
        level = "high" if high_traffic else ("moderate" if multiplier >= 1.2 else "normal")
        return {
            "success": True,
            "traffic_level": level,
            "traffic_multiplier": round(multiplier, 2),
            "delay_minutes": round(delay_minutes, 1),
            "high_traffic": high_traffic
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def analyze_municipal_traffic_cause(latitude, longitude, api_key, issue_text=""):
    """Use Google Maps APIs to estimate whether congestion is likely caused by municipal factors."""
    try:
        if not api_key:
            return {"success": False, "error": "Missing API key"}

        signals = []
        evidence = []
        issue_text_l = (issue_text or "").lower()

        municipal_terms = [
            "roadwork", "road work", "construction", "closure", "road closed",
            "diversion", "detour", "maintenance", "repair", "utility work",
            "pipeline", "excavation", "drainage work", "sewer work"
        ]

        # Step 1: Check directions warnings/instructions for closure/diversion hints
        origin = f"{latitude},{longitude}"
        destination = f"{latitude + 0.025},{longitude + 0.025}"
        directions_resp = requests.get(
            "https://maps.googleapis.com/maps/api/directions/json",
            params={
                "origin": origin,
                "destination": destination,
                "departure_time": "now",
                "traffic_model": "best_guess",
                "alternatives": "true",
                "key": api_key
            },
            timeout=10
        )

        if directions_resp.status_code == 200:
            directions_data = directions_resp.json()
            if directions_data.get("status") == "OK":
                for route in directions_data.get("routes", [])[:3]:
                    for warning in route.get("warnings", []):
                        warning_l = str(warning).lower()
                        if any(term in warning_l for term in municipal_terms):
                            signals.append("route_warning")
                            evidence.append(f"Route warning: {warning}")

                    for leg in route.get("legs", []):
                        for step in leg.get("steps", []):
                            inst_text = re.sub(r"<[^>]+>", " ", step.get("html_instructions", ""))
                            inst_l = inst_text.lower()
                            matched = [term for term in municipal_terms if term in inst_l]
                            if matched:
                                signals.append("step_instruction")
                                evidence.append(f"Route instruction mentions {', '.join(sorted(set(matched)))}")

        # Step 2: Nearby place search for roadwork/construction indicators
        places_resp = requests.get(
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
            params={
                "location": f"{latitude},{longitude}",
                "radius": 1500,
                "keyword": "road construction",
                "key": api_key
            },
            timeout=10
        )

        if places_resp.status_code == 200:
            places_data = places_resp.json()
            if places_data.get("status") in ["OK", "ZERO_RESULTS"]:
                for place in places_data.get("results", [])[:5]:
                    name = str(place.get("name", ""))
                    name_l = name.lower()
                    if any(term in name_l for term in ["construction", "road work", "roadwork", "metro", "flyover"]):
                        signals.append("nearby_place")
                        evidence.append(f"Nearby place: {name}")

        # Step 3: Include citizen text signal
        user_text_match = [term for term in municipal_terms if term in issue_text_l]
        if user_text_match:
            signals.append("citizen_text")
            evidence.append(f"Citizen text mentions {', '.join(sorted(set(user_text_match)))}")

        signal_score = len(signals)
        municipal_likely = signal_score >= 2 or ("citizen_text" in signals and signal_score >= 1)
        confidence = min(0.35 + (0.15 * signal_score), 0.9) if signal_score else 0.2
        classification = "likely_municipal" if municipal_likely else "not_clear_municipal"

        return {
            "success": True,
            "classification": classification,
            "municipal_likely": municipal_likely,
            "confidence": round(confidence, 2),
            "signal_count": signal_score,
            "evidence": evidence[:3]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def extract_gps_from_image(image_file):
    stream_pos = None
    try:
        if hasattr(image_file, "tell"):
            stream_pos = image_file.tell()
        img = Image.open(image_file)
        exif = None
        try:
            exif = img.getexif()
        except Exception:
            exif = img._getexif() if hasattr(img, "_getexif") else None

        def _to_float(value):
            try:
                return float(value)
            except Exception:
                pass

            try:
                if isinstance(value, tuple) and len(value) == 2 and value[1] not in (0, 0.0):
                    return float(value[0]) / float(value[1])
            except Exception:
                pass

            try:
                numerator = getattr(value, "numerator", None)
                denominator = getattr(value, "denominator", None)
                if denominator not in (None, 0):
                    return float(numerator) / float(denominator)
            except Exception:
                pass

            raise ValueError("Unsupported GPS numeric format")

        def convert_to_degrees(value):
            if not isinstance(value, (list, tuple)) or len(value) < 3:
                raise ValueError("GPS DMS value missing")
            d, m, s = value[:3]
            return _to_float(d) + (_to_float(m) / 60.0) + (_to_float(s) / 3600.0)

        def _normalize_ref(ref, positive):
            if isinstance(ref, bytes):
                ref = ref.decode("utf-8", errors="ignore")
            ref = str(ref).strip().upper()
            if not ref:
                return positive
            return ref in positive

        def _parse_lat_lon_from_text(text):
            if not text:
                return None
            text_l = str(text)

            # Pattern like: Lat 12.817497 Long 80.038368
            m1 = re.search(r'(?i)lat(?:itude)?\s*[:=]?\s*(-?\d{1,2}(?:\.\d+)?)\D+lon(?:gitude)?\s*[:=]?\s*(-?\d{1,3}(?:\.\d+)?)', text_l)
            if m1:
                return float(m1.group(1)), float(m1.group(2))

            # Generic coordinate pair
            m2 = re.search(r'(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)', text_l)
            if m2:
                return float(m2.group(1)), float(m2.group(2))
            return None

        gps_info = {}
        if exif:
            exif_items = exif.items() if hasattr(exif, "items") else []
            for tag, value in exif_items:
                decoded = ExifTags.TAGS.get(tag, tag)
                if decoded == "GPSInfo" and isinstance(value, dict):
                    for t in value:
                        sub_decoded = ExifTags.GPSTAGS.get(t, t)
                        gps_info[sub_decoded] = value[t]
                    break

            if gps_info and 'GPSLatitude' in gps_info and 'GPSLongitude' in gps_info:
                lat = convert_to_degrees(gps_info['GPSLatitude'])
                lon = convert_to_degrees(gps_info['GPSLongitude'])

                if not _normalize_ref(gps_info.get('GPSLatitudeRef', 'N'), {'N'}):
                    lat = -abs(lat)
                if not _normalize_ref(gps_info.get('GPSLongitudeRef', 'E'), {'E'}):
                    lon = -abs(lon)

                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon

            # Fallback: try text-bearing EXIF fields
            for _, value in exif_items:
                parsed = _parse_lat_lon_from_text(value)
                if parsed:
                    lat, lon = parsed
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        return lat, lon

        # Fallback: XMP blocks often used by mobile camera apps
        xmp_text = ""
        for key, value in (img.info or {}).items():
            key_s = str(key).lower()
            if "xmp" in key_s:
                if isinstance(value, bytes):
                    xmp_text += value.decode("utf-8", errors="ignore")
                else:
                    xmp_text += str(value)

        if xmp_text:
            lat_match = re.search(r'(?i)gpslatitude\s*[=:]\s*["\']?(-?\d{1,2}(?:\.\d+)?)', xmp_text)
            lon_match = re.search(r'(?i)gpslongitude\s*[=:]\s*["\']?(-?\d{1,3}(?:\.\d+)?)', xmp_text)
            if lat_match and lon_match:
                lat = float(lat_match.group(1))
                lon = float(lon_match.group(1))
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon

        if exifread is not None and hasattr(image_file, "seek"):
            try:
                image_file.seek(0)
                tags = exifread.process_file(image_file, details=False)

                lat_tag = tags.get("GPS GPSLatitude")
                lat_ref_tag = tags.get("GPS GPSLatitudeRef")
                lon_tag = tags.get("GPS GPSLongitude")
                lon_ref_tag = tags.get("GPS GPSLongitudeRef")

                if lat_tag and lon_tag:
                    def _ratio_to_float(value):
                        num = getattr(value, "num", None)
                        den = getattr(value, "den", None)
                        if den in (None, 0):
                            return float(value)
                        return float(num) / float(den)

                    lat_values = getattr(lat_tag, "values", [])
                    lon_values = getattr(lon_tag, "values", [])
                    if len(lat_values) >= 3 and len(lon_values) >= 3:
                        lat = _ratio_to_float(lat_values[0]) + _ratio_to_float(lat_values[1]) / 60.0 + _ratio_to_float(lat_values[2]) / 3600.0
                        lon = _ratio_to_float(lon_values[0]) + _ratio_to_float(lon_values[1]) / 60.0 + _ratio_to_float(lon_values[2]) / 3600.0

                        lat_ref = str(lat_ref_tag.values[0]).upper() if lat_ref_tag and getattr(lat_ref_tag, "values", None) else "N"
                        lon_ref = str(lon_ref_tag.values[0]).upper() if lon_ref_tag and getattr(lon_ref_tag, "values", None) else "E"

                        if lat_ref == "S":
                            lat = -abs(lat)
                        if lon_ref == "W":
                            lon = -abs(lon)

                        if -90 <= lat <= 90 and -180 <= lon <= 180:
                            return lat, lon
            except Exception:
                pass

        return None, None
    except Exception as e:
        print(f"Error extracting GPS from EXIF: {e}")
        return None, None
    finally:
        try:
            if stream_pos is not None and hasattr(image_file, "seek"):
                image_file.seek(stream_pos)
        except Exception:
            pass

def resolve_gmaps_link(url, api_key=""):
    try:
        if not url or not isinstance(url, str):
            return None, None

        url = url.strip()
        resolved_page_text = ""

        if "goo.gl" in url or "maps.app.goo.gl" in url:
            try:
                response = requests.get(url, allow_redirects=True, timeout=8)
                url = response.url
                resolved_page_text = response.text or ""
            except Exception:
                req = urllib.request.Request(url, method='HEAD')
                with urllib.request.urlopen(req) as response:
                    url = response.url

        decoded_url = urllib.parse.unquote(url)
        parsed = urllib.parse.urlparse(decoded_url)
        query_params = urllib.parse.parse_qs(parsed.query)

        def valid_lat_lon(lat, lon):
            return -90 <= lat <= 90 and -180 <= lon <= 180

        def parse_lat_lon_text(text):
            if not text:
                return None
            match = re.search(r'(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)', text)
            if not match:
                return None
            lat = float(match.group(1))
            lon = float(match.group(2))
            if valid_lat_lon(lat, lon):
                return lat, lon
            return None

        for key in ["q", "query", "ll", "center", "destination", "origin", "daddr", "saddr"]:
            values = query_params.get(key) or []
            for value in values:
                coords = parse_lat_lon_text(value)
                if coords:
                    return coords

        match = re.search(r'@(-?\d{1,2}\.\d+),(-?\d{1,3}\.\d+)', decoded_url)
        if match:
            lat = float(match.group(1))
            lon = float(match.group(2))
            if valid_lat_lon(lat, lon):
                return lat, lon

        match = re.search(r'!3d(-?\d{1,2}\.\d+)!4d(-?\d{1,3}\.\d+)', decoded_url)
        if match:
            lat = float(match.group(1))
            lon = float(match.group(2))
            if valid_lat_lon(lat, lon):
                return lat, lon

        match = re.search(r'!4d(-?\d{1,3}\.\d+)!3d(-?\d{1,2}\.\d+)', decoded_url)
        if match:
            lon = float(match.group(1))
            lat = float(match.group(2))
            if valid_lat_lon(lat, lon):
                return lat, lon

        match = re.search(r'place/(-?\d{1,2}\.\d+),(-?\d{1,3}\.\d+)', decoded_url)
        if match:
            lat = float(match.group(1))
            lon = float(match.group(2))
            if valid_lat_lon(lat, lon):
                return lat, lon

        # Prefer extracting place text from URL and geocoding it (more reliable for short links)
        path = urllib.parse.unquote(parsed.path or "")
        place_match = re.search(r'/maps/place/([^/]+)', path)
        if place_match:
            place_text = place_match.group(1)
            place_text = place_text.split('/data=')[0].replace('+', ' ').replace('%2C', ',').strip(' ,')
            geocoded = geocode_text_location(place_text, api_key=api_key)
            if geocoded.get("success"):
                return geocoded.get("latitude"), geocoded.get("longitude")

        if not resolved_page_text and ("google.com/maps" in decoded_url or "maps.app.goo.gl" in decoded_url):
            try:
                page_resp = requests.get(decoded_url, allow_redirects=True, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
                resolved_page_text = page_resp.text or ""
            except Exception:
                resolved_page_text = ""

        if resolved_page_text:
            match = re.search(r'!2d(-?\d{1,3}\.\d+)!3d(-?\d{1,2}\.\d+)', resolved_page_text)
            if match:
                lon = float(match.group(1))
                lat = float(match.group(2))
                if valid_lat_lon(lat, lon):
                    return lat, lon

            match = re.search(r'center=(-?\d{1,2}\.\d+)%2C(-?\d{1,3}\.\d+)', resolved_page_text)
            if match:
                lat = float(match.group(1))
                lon = float(match.group(2))
                if valid_lat_lon(lat, lon):
                    return lat, lon

    except Exception as e:
        print(f"Error resolving gmaps link: {e}")
    
    return None, None

def display_message(role, content):
    """Display a chat message with enhanced styling"""
    css_class = "user-message" if role == "user" else "bot-message"
    icon = "👤 You" if role == "user" else "🤖 Assistant"
    safe_content = html.escape(str(content or ""))
    
    st.markdown(f"""
        <div class="chat-message {css_class}">
            <div style="font-weight: 700; margin-bottom: 0.5rem; opacity: 0.8;">
                {icon}
            </div>
            <div class="message-content">
                {safe_content}
            </div>
            <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.6;">
                {datetime.now().strftime('%H:%M')}
            </div>
        </div>
    """, unsafe_allow_html=True)

def process_user_message(user_input):
    """Process user message and generate response"""

    chatbot = st.session_state.smart_chatbot

    # 1) AI conversational intent detection (handles greetings correctly)
    if chatbot:
        ai_result = chatbot.chat(user_input, st.session_state.user_info)
    else:
        ai_result = {
            "service_type": "general_inquiry",
            "intent": "inquire",
            "action_needed": False,
            "department": "General",
            "message": "I'm here to help. Please describe your civic issue in detail.",
            "follow_up_questions": None,
            "confidence": 0.4,
            "extracted_info": {}
        }

    service_type = ai_result.get("service_type", "general_inquiry")
    intent = ai_result.get("intent", "inquire")
    action_needed = ai_result.get("action_needed", False)
    st.session_state.last_ai_result = ai_result if isinstance(ai_result, dict) else {}
    
    print(f"DEBUG process_user_message: input='{user_input}' -> service_type='{service_type}' intent='{intent}' action_needed={action_needed}")

    # If this is greeting/general inquiry, do not create complaint
    if service_type in ["greeting", "general_inquiry"] and not action_needed:
        print(f"DEBUG: EARLY RETURN - Not filing complaint for {service_type}")
        response_str = str(ai_result.get("message", "Hello! How can I help you today?"))
        sentiment = ai_result.get("sentiment") if isinstance(ai_result, dict) else None
        if isinstance(sentiment, dict):
            sent_label = str(sentiment.get("label", "neutral")).lower()
            if sent_label == "negative":
                response_str += "\n\n💙 I understand this may be frustrating, and I will guide you step by step."
        followups = ai_result.get("follow_up_questions") or []
        if followups:
            response_str += "\n\n❓ **Follow-up Questions:**"
            for question in followups:
                response_str += f"\n- {question}"
        st.session_state.last_route_info = {
            "service_type": service_type,
            "intent": intent,
            "department": ai_result.get("department", "General") if isinstance(ai_result, dict) else "General",
            "should_file": False,
            "complaint_id": None,
            "followups": len(followups),
            "awaiting_details": False
        }
        return response_str

    # 2) Complaint classification and routing metadata
    classification = st.session_state.classifier.classify_message(user_input)

    text_lower = user_input.lower()
    traffic_keywords = [
        'traffic', 'congestion', 'diversion', 'road block', 'gridlock',
        'bottleneck', 'signal not working', 'signal failure', 'heavy jam',
        'vehicle queue', 'stuck traffic', 'detour'
    ]
    if any(keyword in text_lower for keyword in traffic_keywords):
        classification['category'] = 'traffic'
        classification['urgency'] = 'high'
        classification['priority_note'] = 'Traffic impact detected from complaint text'

    category = classification.get("category", "other")
    department_info = config.DEPARTMENT_MAPPING.get(category, {
        "name": "General Administration",
        "email": "admin@municipal.gov",
        "icon": "📋"
    })

    # Prefer SmartChatbot department if it matches mapping names
    ai_department = (ai_result.get("department") or "").strip().lower()
    if ai_department:
        for _, dept in config.DEPARTMENT_MAPPING.items():
            if dept.get("name", "").lower() == ai_department:
                department_info = dept
                break

    # 3) Save complaint only for actual complaint-file intents
    should_file = service_type == "complaint" and intent == "file"
    complaint_id = None
    print(f"DEBUG: should_file={should_file} (service_type={service_type}, intent={intent})")
    if should_file and classification.get("is_valid_issue", True):
        extracted = ai_result.get("extracted_info") or {}
        complaint_data = {
            "user_message": user_input,
            "description": user_input,
            "category": category,
            "department": department_info["name"],
            "department_email": department_info["email"],
            "summary": classification.get("summary", user_input[:200]),
            "location": extracted.get("location") or classification.get("location", "Not specified"),
            "urgency": extracted.get("priority") or classification.get("urgency", "medium"),
            "confidence": max(classification.get("confidence", 0.0), ai_result.get("confidence", 0.0)),
            "priority_note": classification.get("priority_note", ""),
            "citizen_id": st.session_state.user_info.get("citizen_id") if st.session_state.user_info else None
        }

        complaint_id = st.session_state.database.save_complaint(complaint_data) if st.session_state.database else None
        st.session_state.pending_complaint_id = complaint_id
        st.session_state.pending_issue_text = user_input
        st.session_state.pending_category = classification.get("category", "other")
        st.session_state.show_ai_followup = True

    # 4) Build response with follow-up questions and routing guidance
    response_str = str(ai_result.get("message") or st.session_state.classifier.generate_acknowledgment(
        classification,
        department_info
    ))

    sentiment = ai_result.get("sentiment") if isinstance(ai_result, dict) else None
    if isinstance(sentiment, dict):
        sent_label = str(sentiment.get("label", "neutral")).lower()
        if sent_label == "negative":
            response_str += "\n\n💙 I understand this is urgent or stressful for you."

    followups = ai_result.get("follow_up_questions") or []
    if followups:
        response_str += "\n\n❓ **Please share these details so I can route this accurately:**"
        for question in followups:
            response_str += f"\n- {question}"

    if complaint_id:
        response_str += f"\n\n🎫 **Tracking ID**: `{complaint_id}`"
        if classification.get("urgency") == "high":
            response_str += "\n\n⚡ **Priority**: HIGH (Fast-track routing enabled)"
        response_str += "\n\n📍 **Next**: Use AI Follow-up below chat to provide address/coordinates and optional image verification."
        response_str += "\n\n📝 **Alternative**: Open the **File Complaint** page for Manual Entry or Picture Upload with geotag."
    elif should_file:
        response_str += "\n\n📍 **Next**: Use AI Follow-up below chat to upload a geotagged photo or share location coordinates now."
        response_str += "\n\nℹ️ **Note**: Complaint ticket will be generated once database connection is available."

    st.session_state.last_route_info = {
        "service_type": service_type,
        "intent": intent,
        "department": department_info.get("name", "General Administration"),
        "should_file": should_file,
        "complaint_id": complaint_id,
        "followups": len(followups),
        "awaiting_details": bool(complaint_id)
    }

    return response_str


def submit_chat_message(user_input):
    if not user_input or not str(user_input).strip():
        return

    clean_input = str(user_input).strip()
    st.session_state.messages.append({
        "role": "user",
        "content": clean_input,
        "timestamp": datetime.now()
    })

    with st.spinner("🔍 Analyzing your issue • Classifying complaint • Routing to department..."):
        bot_response = process_user_message(clean_input)

    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_response,
        "timestamp": datetime.now()
    })
    st.rerun()


def show_login_page():
    """Show login/signup interface"""
    st.markdown(f"""
        <div class="main-header">
            <h1>{config.APP_ICON} {config.APP_TITLE}</h1>
            <p>Report municipal issues and get them routed to the right department</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.auth_page == 'login':
            st.markdown("""
            <div style="background: white; padding: 2rem; border-radius: 15px; border: 2px solid #e2e8f0;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.08); text-align: center;">
                <h2 style="color: #667eea; margin-top: 0;">🔐 Login</h2>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("👤 Username")
                password = st.text_input("🔒 Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                
                if submitted:
                    if username and password:
                        result = st.session_state.auth.login(username, password)
                        if result["success"]:
                            st.session_state.logged_in = True
                            st.session_state.user_info = result["user"]
                            st.success(f"Welcome back, {result['user']['full_name']}!")
                            st.rerun()
                        else:
                            st.error(result["message"])
                    else:
                        st.warning("Please fill in all fields")
            
            st.markdown("---")
            if st.button("📝 Don't have an account? Sign Up", use_container_width=True):
                st.session_state.auth_page = 'signup'
                st.rerun()
        
        else:  # signup
            st.markdown("""
            <div style="background: white; padding: 2rem; border-radius: 15px; border: 2px solid #e2e8f0;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.08); text-align: center;">
                <h2 style="color: #667eea; margin-top: 0;">📝 Create Account</h2>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("signup_form"):
                full_name = st.text_input("📛 Full Name")
                email = st.text_input("📧 Email")
                phone = st.text_input("📱 Phone Number")
                username = st.text_input("👤 Choose Username")
                password = st.text_input("🔒 Password", type="password")
                confirm_password = st.text_input("🔒 Confirm Password", type="password")
                submitted = st.form_submit_button("Create Account", use_container_width=True)
                
                if submitted:
                    if not all([full_name, email, phone, username, password]):
                        st.warning("Please fill in all fields")
                    elif password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        result = st.session_state.auth.signup(username, email, password, phone, full_name)
                        if result["success"]:
                            st.success(result["message"])
                            st.session_state.auth_page = 'login'
                            st.rerun()
                        else:
                            st.error(result["message"])
            
            st.markdown("---")
            if st.button("🔐 Already have an account? Login", use_container_width=True):
                st.session_state.auth_page = 'login'
                st.rerun()


def main():
    """Main application"""
    
    # Check authentication
    if not st.session_state.logged_in:
        show_login_page()
        return
    
    # Header
    st.markdown(f"""
        <div class="main-header">
            <h1>{config.APP_ICON} {config.APP_TITLE}</h1>
            <p>Report municipal issues and get them routed to the right department</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        # User info at top
        user = st.session_state.user_info
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 12px; margin-bottom: 1rem; color: white;">
            <div style="font-size: 1.5rem;">👤</div>
            <div style="font-weight: 700;">{user.get('full_name', 'User')}</div>
            <div style="font-size: 0.8rem; opacity: 0.8;">{user.get('citizen_id', '')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <h2 style="margin: 0; color: #667eea;">📊 Dashboard</h2>
            <p style="margin: 0.5rem 0 0; color: #64748b; font-size: 0.9rem;">Live Statistics</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Statistics
        stats = st.session_state.database.get_statistics() if st.session_state.database else {}
        if stats:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📋 Total", stats.get("total", 0), delta=None)
            with col2:
                st.metric("⏳ Pending", stats.get("pending", 0), delta=None)
            with col3:
                st.metric("✅ Resolved", stats.get("resolved", 0), delta=None)
            
            st.divider()
            
            # Category breakdown
            if stats.get("by_category"):
                st.subheader("📈 Issues by Category")
                for cat in stats["by_category"]:
                    category_name = cat["_id"]
                    count = cat["count"]
                    dept_info = config.DEPARTMENT_MAPPING.get(category_name, {})
                    icon = dept_info.get("icon", "📋")
                    
                    # Progress bar style
                    st.markdown(f"""
                    <div style="margin-bottom: 1rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span style="font-weight: 600; color: #1e293b;">{icon} {category_name.capitalize()}</span>
                            <span style="color: #667eea; font-weight: 700;">{count}</span>
                        </div>
                        <div style="height: 8px; background: #e2e8f0; border-radius: 10px; overflow: hidden;">
                            <div style="height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); 
                                        width: {min((count/max(stats.get('total', 1), 1)*100), 100)}%;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.divider()
        
        # Department Directory with better styling
        st.subheader("🏢 Department Directory")
        for category, dept in config.DEPARTMENT_MAPPING.items():
            with st.expander(f"{dept['icon']} {dept['name']}", expanded=False):
                st.markdown(f"""
                <div style="padding: 0.5rem 0;">
                    <p style="margin: 0.5rem 0;"><strong>Category:</strong> <code>{category}</code></p>
                    <p style="margin: 0.5rem 0;"><strong>Email:</strong> <a href="mailto:{dept['email']}">{dept['email']}</a></p>
                    <p style="margin: 0.5rem 0;"><strong>Handles:</strong> {', '.join(dept['keywords'][:5])}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        
        # Enhanced clear button
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.last_ai_result = {}
                st.session_state.last_route_info = {}
                st.rerun()
        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
    
    # Main chat interface
    st.header("💬 Report an Issue")
    
    # Display welcome message if no messages
    if len(st.session_state.messages) == 0:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div class="welcome-box" style="text-align: center; padding: 2.5rem 2rem;">
                <h2 style="margin-top: 0; color: #d97706;">👋 Welcome to Municipal Support</h2>
                <p style="font-size: 1.05rem; color: #92400e; margin: 1rem 0;">
                    I'm your intelligent assistant for reporting civic issues instantly and efficiently.
                </p>
                <hr style="border-top: 2px solid rgba(0,0,0,0.1); margin: 1.5rem 0;">
                <p style="color: #92400e; font-weight: 600; margin-bottom: 1rem;">📝 You can report:</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Issue categories
        categories_data = [
            ("🛣️", "Potholes & Road Damage", "Broken pavements, surface defects"),
            ("💧", "Water Issues", "Leaks, pressure problems, contamination"),
            ("🗑️", "Garbage Collection", "Delayed pickups, overflow bins"),
            ("💡", "Electrical", "Broken streetlights, power issues"),
            ("🌊", "Drainage", "Blocked drains, flooding, sewage"),
            ("🚦", "Traffic", "Congestion, signal failures, accidents"),
        ]
        
        cols = st.columns(3)
        for idx, (emoji, title, desc) in enumerate(categories_data):
            with cols[idx % 3]:
                st.markdown(f"""
                <div style="background: white; padding: 1.5rem; border-radius: 12px; border: 2px solid #e2e8f0; 
                            text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); transition: all 0.3s ease;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">{emoji}</div>
                    <div style="font-weight: 600; color: #1e293b; margin-bottom: 0.3rem;">{title}</div>
                    <div style="font-size: 0.9rem; color: #64748b;">{desc}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align: center; margin-top: 2rem; padding-top: 1.5rem; border-top: 2px solid #e2e8f0;">
            <p style="color: #475569; font-size: 1rem;">
                ⏱️ <strong>Quick</strong> • 🎯 <strong>Accurate</strong> • 📍 <strong>Geo-Tagged</strong> • 🚀 <strong>Fast-Track</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### ⚡ Quick Complaint Buttons")
    quick_actions = [
        ("🕳️ Pothole", "There is a dangerous pothole on the main road near the bus stop"),
        ("💧 Water Leak", "There is a major water leak from pipeline near my street"),
        ("💡 Street Light", "Street lights are not working in my area and it is unsafe"),
        ("🗑️ Garbage", "Garbage has not been collected for several days in our lane"),
        ("🌊 Drainage", "Drainage is blocked and water is overflowing onto the road"),
        ("🚦 Traffic", "Traffic signal is not working causing heavy congestion")
    ]

    quick_cols = st.columns(3)
    for idx, (label, prompt) in enumerate(quick_actions):
        with quick_cols[idx % 3]:
            if st.button(label, key=f"quick_action_{idx}", use_container_width=True):
                submit_chat_message(prompt)
    
    # Display chat history
    for message in st.session_state.messages:
        with st.container():
            display_message(message["role"], message["content"])

    last_ai = st.session_state.last_ai_result if isinstance(st.session_state.last_ai_result, dict) else {}
    route_info = st.session_state.last_route_info if isinstance(st.session_state.last_route_info, dict) else {}
    if last_ai:
        st.markdown("### 🧠 Session Insights")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Intent", str(route_info.get("intent", last_ai.get("intent", "-"))).upper())
        with c2:
            st.metric("Department", route_info.get("department", last_ai.get("department", "General")))
        with c3:
            sentiment = last_ai.get("sentiment", {}) if isinstance(last_ai.get("sentiment", {}), dict) else {}
            st.metric("Sentiment", str(sentiment.get("label", "neutral")).upper())
        with c4:
            st.metric("Follow-ups", route_info.get("followups", len(last_ai.get("follow_up_questions") or [])))

        if route_info.get("complaint_id"):
            if route_info.get("awaiting_details"):
                st.warning(f"📝 Complaint pre-registered • Tracking ID: {route_info.get('complaint_id')} • Awaiting location/image details for final routing")
            else:
                st.success(f"✅ Complaint routed successfully • Tracking ID: {route_info.get('complaint_id')}")

    if st.session_state.show_ai_followup:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); 
                    border: 2px solid #0284c7; border-radius: 15px; padding: 1.5rem; 
                    margin: 1.5rem 0; box-shadow: 0 4px 15px rgba(2, 132, 199, 0.15);">
            <h3 style="margin: 0 0 0.5rem; color: #0c4a6e;">🤖 AI Follow-up & Enhancement</h3>
            <p style="margin: 0; color: #0369a1; font-size: 0.95rem;">
                ✨ Enhance your complaint with location details, verify with imagery, and enable traffic routing
            </p>
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.pending_complaint_id:
            st.info("📌 You can upload a geotagged photo now. Ticket creation will resume automatically when database is connected.")

        with st.form("ai_followup_form"):
            location_mode = st.radio(
                "📍 Select Location Input Method",
                ["📍 Address", "🧭 Coordinates", "🔗 Google Maps Link"],
                horizontal=True
            )

            latitude = None
            longitude = None
            address_text = ""
            gmaps_url = ""

            if location_mode == "📍 Address":
                address_text = st.text_input(
                    "📮 Enter Issue Address",
                    placeholder="e.g., Anna Salai, Chennai / Main Street, Apt 10"
                )
            elif location_mode == "🔗 Google Maps Link":
                gmaps_url = st.text_input(
                    "🔗 Paste Google Maps Link",
                    placeholder="e.g., https://maps.app.goo.gl/... or https://goo.gl/maps/..."
                )
            else:
                col_lat, col_lon = st.columns(2)
                with col_lat:
                    latitude = st.number_input("🧭 Latitude", min_value=-90.0, max_value=90.0, value=13.0827, format="%.6f")
                with col_lon:
                    longitude = st.number_input("🧭 Longitude", min_value=-180.0, max_value=180.0, value=80.2707, format="%.6f")

            uploaded_image = st.file_uploader("📸 Upload Issue Photo (Optional)", type=['jpg', 'jpeg', 'png'])
            
            st.markdown("---")
            
            # Satellite image preview button
            if st.form_submit_button("🛰️ View Satellite Image", use_container_width=True):
                api_key = get_google_api_key()
                final_lat_preview = None
                final_lon_preview = None
                
                if location_mode == "📍 Address":
                    if address_text.strip():
                        if api_key:
                            geo = get_coordinates_from_address(address_text, api_key)
                            if geo.get("success"):
                                final_lat_preview = geo["latitude"]
                                final_lon_preview = geo["longitude"]
                                st.success(f"Location found: {geo.get('formatted_address')}")
                        else:
                            st.warning("Google Maps API key not configured. Use Coordinates mode.")
                    else:
                        st.error("Please enter an address")
                elif location_mode == "🔗 Google Maps Link":
                    if gmaps_url.strip():
                        glat, glon = resolve_gmaps_link(gmaps_url.strip(), api_key=api_key)
                        if glat is not None and glon is not None:
                            final_lat_preview = glat
                            final_lon_preview = glon
                            st.success(f"Location extracted: {glat:.6f}, {glon:.6f}")
                        else:
                            st.error("Could not extract coordinates from the provided link.")
                    else:
                        st.error("Please paste a Google Maps link.")
                else:
                    final_lat_preview = latitude
                    final_lon_preview = longitude
                
                if final_lat_preview is not None and final_lon_preview is not None:
                    reverse_result = get_address_from_coordinates(final_lat_preview, final_lon_preview, api_key)
                    if reverse_result.get("success"):
                        st.success(f"📍 Resolved location: {reverse_result.get('formatted_address')}")
                    st.info(f"📡 Fetching satellite image for coordinates: {final_lat_preview:.4f}, {final_lon_preview:.4f}")
                    if api_key:
                        # Display Google Maps static satellite image
                        map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={final_lat_preview},{final_lon_preview}&zoom=18&size=600x400&maptype=satellite&key={api_key}"
                        st.image(map_url, caption=f"Satellite view: {final_lat_preview:.4f}, {final_lon_preview:.4f}", use_container_width=True)
                    else:
                        st.warning("⚠️ Google Maps API key needed to display satellite images")
            
            st.markdown("---")
            
            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submit_followup = st.form_submit_button("✨ Run AI Follow-up", use_container_width=True)
            with col_cancel:
                cancel_followup = st.form_submit_button("❌ Skip For Now", use_container_width=True)

            if cancel_followup:
                st.session_state.show_ai_followup = False
                st.rerun()

            if submit_followup:
                api_key = get_google_api_key()
                final_lat = None
                final_lon = None
                reference_id = st.session_state.pending_complaint_id or f"TEMP_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # Try auto-extracting from uploaded image first
                if uploaded_image:
                    exif_lat, exif_lon = extract_gps_from_image(uploaded_image)
                    uploaded_image.seek(0) # Reset stream for later use
                    if exif_lat is not None and exif_lon is not None:
                        st.success(f"📍 Location automatically extracted from image geotag: {exif_lat:.6f}, {exif_lon:.6f}")
                        final_lat = exif_lat
                        final_lon = exif_lon
                    else:
                        st.error("please enter a geo tagged photo")
                        return

                if final_lat is None or final_lon is None:
                    if location_mode == "📍 Address":
                        if not address_text.strip():
                            st.error("Please enter an address or upload an image with a Geotag.")
                            return
                        if not api_key:
                            st.error("Google Maps API key is on hold. Use Coordinates mode for now.")
                            return
                        geo = get_coordinates_from_address(address_text, api_key)
                        if not geo.get("success"):
                            st.error(f"Address lookup failed: {geo.get('error')}")
                            return
                        final_lat = geo["latitude"]
                        final_lon = geo["longitude"]
                        st.success(f"Location found: {geo.get('formatted_address')}")
                    elif location_mode == "🔗 Google Maps Link":
                        if not gmaps_url.strip():
                            st.error("Please paste a Google Maps link or upload an image with a Geotag.")
                            return
                        glat, glon = resolve_gmaps_link(gmaps_url.strip(), api_key=api_key)
                        if glat is not None and glon is not None:
                            final_lat = glat
                            final_lon = glon
                            st.success(f"📍 Location extracted from Google Maps link: {final_lat:.6f}, {final_lon:.6f}")
                        else:
                            st.error("Could not extract coordinates from the provided link.")
                            return
                    else:
                        final_lat = latitude
                        final_lon = longitude

                reverse_result = get_address_from_coordinates(final_lat, final_lon, api_key)
                if reverse_result.get("success"):
                    st.info(f"📍 Location resolved from coordinates: {reverse_result.get('formatted_address')}")

                # Live traffic scoring (if API key available)
                traffic_escalated = False
                municipal_traffic = {"success": False}
                issue_text = st.session_state.pending_issue_text or ""
                traffic_or_diversion_case = (
                    st.session_state.pending_category == "traffic"
                    or any(keyword in issue_text.lower() for keyword in ["traffic", "diversion", "detour", "road block", "congestion"])
                )

                if api_key:
                    traffic = get_live_traffic_insight(final_lat, final_lon, api_key)
                    if traffic.get("success"):
                        st.info(
                            f"Live Traffic: {traffic['traffic_level'].upper()} "
                            f"(x{traffic['traffic_multiplier']}, +{traffic['delay_minutes']} min)"
                        )
                        if traffic.get("high_traffic"):
                            traffic_escalated = True
                            st.warning("High traffic impact detected. Marking as HIGH priority.")

                    if traffic_or_diversion_case:
                        municipal_traffic = analyze_municipal_traffic_cause(
                            final_lat,
                            final_lon,
                            api_key,
                            issue_text=issue_text
                        )
                        if municipal_traffic.get("success"):
                            if municipal_traffic.get("municipal_likely"):
                                st.warning(
                                    f"🛣️ Municipal-cause signal detected (confidence {municipal_traffic.get('confidence')}). "
                                    f"Possible roadwork/closure/diversion involvement."
                                )
                            else:
                                st.info(
                                    f"🛣️ Traffic cause check completed (confidence {municipal_traffic.get('confidence')}). "
                                    "No clear municipal-cause signal found."
                                )

                            evidence = municipal_traffic.get("evidence") or []
                            if evidence:
                                st.caption(f"Evidence: {evidence[0]}")
                        else:
                            st.caption("Traffic municipal-cause check unavailable (API/permissions may be limited).")

                # Update complaint status/remarks for high-priority traffic routing
                remark_parts = []
                if municipal_traffic.get("success"):
                    cause_label = "Likely Municipal" if municipal_traffic.get("municipal_likely") else "Not Clearly Municipal"
                    remark_parts.append(
                        f"Traffic Cause: {cause_label} (confidence {municipal_traffic.get('confidence')})"
                    )

                if st.session_state.database and st.session_state.pending_complaint_id and (
                    st.session_state.pending_category == "traffic"
                    or traffic_escalated
                    or municipal_traffic.get("municipal_likely")
                ):
                    final_remarks = "Priority: HIGH | Routed to Traffic Management Cell"
                    if remark_parts:
                        final_remarks += " | " + " | ".join(remark_parts)
                    st.session_state.database.update_complaint_status(
                        st.session_state.pending_complaint_id,
                        "In Progress",
                        final_remarks
                    )
                elif st.session_state.database and st.session_state.pending_complaint_id:
                    final_remarks = "Location/details completed by citizen | Routed for department action"
                    if remark_parts:
                        final_remarks += " | " + " | ".join(remark_parts)
                    st.session_state.database.update_complaint_status(
                        st.session_state.pending_complaint_id,
                        "In Progress",
                        final_remarks
                    )

                # Satellite pipeline (optional)
                if st.session_state.satellite and st.session_state.pending_complaint_id:
                    with st.spinner("🛰️ Processing satellite verification..."):
                        process_id, result = st.session_state.satellite.process_new_complaint({
                            "complaint_id": st.session_state.pending_complaint_id,
                            "description": st.session_state.pending_issue_text,
                            "latitude": final_lat,
                            "longitude": final_lon
                        })
                        
                        if result.get('status') == 'completed':
                            st.success(f"✅ Satellite verification completed! Process ID: {process_id}")
                            
                            # Show detection summary
                            for step in result.get('steps', []):
                                if step.get('step') == 'satellite_detection' and step.get('success'):
                                    issues = step.get('issues_detected', 0)
                                    conf = step.get('confidence', 0)
                                    st.info(f"🔍 **AI Detection:** {issues} issue(s) detected • Confidence: {round(conf*100)}%")
                        else:
                            status = result.get('status', 'unknown')
                            st.warning(f"⚠️ Satellite process status: {status}")

                        if uploaded_image:
                            image_path = Path("user_images") / f"{reference_id}_user.png"
                            image_path.parent.mkdir(exist_ok=True)
                            with open(image_path, "wb") as f:
                                f.write(uploaded_image.getbuffer())
                            
                            with st.spinner("🔬 Cross-verifying uploaded image..."):
                                user_process_id, user_result = st.session_state.satellite.process_user_image(
                                    st.session_state.pending_complaint_id,
                                    str(image_path)
                                )
                            
                            v_result = user_result.get('verification_result', {})
                            if v_result:
                                v_status = v_result.get('final_status', 'unknown')
                                v_conf = v_result.get('confidence_score', 0)
                                recommendation = v_result.get('recommendation', '')
                                
                                if v_status in ['verified_auto', 'verified_by_proximity']:
                                    st.success(f"✅ **Verified!** Confidence: {round(v_conf*100)}%")
                                elif v_status == 'verified_uncertain':
                                    st.warning(f"⚠️ **Partially verified.** Confidence: {round(v_conf*100)}%")
                                else:
                                    st.info(f"📋 Status: {v_status}")
                                
                                if recommendation:
                                    st.caption(f"💡 {recommendation}")
                            else:
                                st.success(f"📸 Image processed. ID: {user_process_id}")
                else:
                    if uploaded_image:
                        image_path = Path("user_images") / f"{reference_id}_user.png"
                        image_path.parent.mkdir(exist_ok=True)
                        with open(image_path, "wb") as f:
                            f.write(uploaded_image.getbuffer())
                        st.success(f"📸 Photo uploaded successfully as {image_path.name}")

                    # Still update location in DB even without satellite
                    if st.session_state.database and st.session_state.pending_complaint_id:
                        try:
                            conn = st.session_state.database.get_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE complaints SET latitude = %s, longitude = %s WHERE complaint_id = %s
                            """, (final_lat, final_lon, st.session_state.pending_complaint_id))
                            conn.commit()
                            cursor.close()
                            conn.close()
                        except Exception:
                            pass

                st.success("✨ AI follow-up completed!")
                st.session_state.last_route_info = {
                    "service_type": "complaint",
                    "intent": "file",
                    "department": st.session_state.last_route_info.get("department", "General Administration") if isinstance(st.session_state.last_route_info, dict) else "General Administration",
                    "should_file": True,
                    "complaint_id": st.session_state.pending_complaint_id,
                    "followups": st.session_state.last_route_info.get("followups", 0) if isinstance(st.session_state.last_route_info, dict) else 0,
                    "awaiting_details": False
                }
                st.session_state.show_ai_followup = False
    
    # Chat input with enhanced styling
    st.markdown("""
    <div style="padding: 1.5rem 0;">
        <hr style="border: none; height: 2px; background: linear-gradient(90deg, transparent, #e2e8f0, transparent);">
    </div>
    """, unsafe_allow_html=True)
    
    user_input = st.chat_input(
        "📝 Describe your issue here... (e.g., 'Pothole on Main Street' or 'Water leak in apartment')",
        key="chat_input"
    )
    
    if user_input:
        submit_chat_message(user_input)
    
    # Enhanced Footer
    st.markdown("""
    <div style="margin-top: 3rem; padding: 2rem; border-top: 2px solid #e2e8f0; text-align: center;">
        <div style="display: flex; justify-content: center; gap: 1.5rem; margin-bottom: 1rem; flex-wrap: wrap;">
            <div style="font-size: 0.95rem; color: #64748b;">
                <strong style="color: #667eea;">⚡ Instant</strong> routing
            </div>
            <div style="font-size: 0.95rem; color: #64748b;">
                <strong style="color: #667eea;">🎯 AI-Powered</strong> classification
            </div>
            <div style="font-size: 0.95rem; color: #64748b;">
                <strong style="color: #667eea;">📍 Geo-Tagged</strong> accuracy
            </div>
        </div>
        <p style="margin: 1rem 0 0.5rem; color: #94a3b8; font-size: 0.9rem;">
            🏛️ Municipal Issue Reporting System • Powered by Gemini 2.5 Flash AI
        </p>
        <p style="margin: 0.5rem 0 0; color: #cbd5e1; font-size: 0.85rem;">
            Supporting SDG 11: Sustainable Cities and Communities
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
