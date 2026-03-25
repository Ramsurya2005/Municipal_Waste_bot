"""
Configuration file for Municipal Chatbot
Contains department mappings and system settings
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("GEMINI_API_KEY")  # Fallback for compatibility

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "municipal_chatbot")
DATABASE_NAME = MONGODB_DB_NAME  # Alias for compatibility

# Application Settings
APP_TITLE = os.getenv("APP_TITLE", "Municipal Issue Reporting Chatbot")
APP_ICON = os.getenv("APP_ICON", "🏛️")

# Department Mapping
DEPARTMENT_MAPPING = {
    "traffic": {
        "name": "Traffic Management Cell",
        "keywords": ["traffic", "congestion", "diversion", "road block", "bottleneck", "signal", "gridlock", "jam"],
        "email": "traffic@municipal.gov",
        "icon": "🚦"
    },
    "roads": {
        "name": "Public Works Department",
        "keywords": ["road", "pothole", "street", "pavement", "highway", "traffic", "signage", "zebra crossing"],
        "email": "publicworks@municipal.gov",
        "icon": "🛣️"
    },
    "water": {
        "name": "Water Supply Board",
        "keywords": ["water", "leak", "pipe", "supply", "drinking water", "tap", "water pressure", "burst pipe"],
        "email": "water@municipal.gov",
        "icon": "💧"
    },
    "sanitation": {
        "name": "Sanitation Department",
        "keywords": ["garbage", "trash", "waste", "cleanliness", "dump", "litter", "collection", "bin", "sweeping"],
        "email": "sanitation@municipal.gov",
        "icon": "🗑️"
    },
    "electricity": {
        "name": "Electrical Department",
        "keywords": ["streetlight", "light", "electricity", "power", "lamp", "bulb", "pole", "wiring"],
        "email": "electrical@municipal.gov",
        "icon": "💡"
    },
    "drainage": {
        "name": "Drainage Department",
        "keywords": ["drainage", "sewer", "manhole", "flood", "overflow", "blocked drain", "stagnant water"],
        "email": "drainage@municipal.gov",
        "icon": "🌊"
    },
    "parks": {
        "name": "Parks and Recreation",
        "keywords": ["park", "garden", "playground", "tree", "green space", "bench", "recreation"],
        "email": "parks@municipal.gov",
        "icon": "🌳"
    },
    "health": {
        "name": "Public Health Department",
        "keywords": ["health", "sanitation", "mosquito", "pest", "hygiene", "disease", "pollution"],
        "email": "health@municipal.gov",
        "icon": "🏥"
    },
    "building": {
        "name": "Building and Planning Department",
        "keywords": ["building", "construction", "illegal", "encroachment", "permission", "demolition"],
        "email": "building@municipal.gov",
        "icon": "🏗️"
    }
}

# Issue Classification Prompt
CLASSIFICATION_PROMPT = """You are an AI assistant for a municipal government. Your job is to analyze citizen messages and determine:
1. Whether it's a valid municipal/civic issue that requires government action
2. Which department should handle it
3. Extract key information (issue type, location, urgency)

Analyze the following message and respond ONLY in this JSON format:
{
    "is_valid_issue": true/false,
    "category": "traffic/roads/water/sanitation/electricity/drainage/parks/health/building/other",
    "confidence": 0.0-1.0,
    "summary": "Brief summary of the issue",
    "location": "Extracted location if mentioned",
    "urgency": "low/medium/high",
    "reason": "Brief explanation of classification"
}

If the message is not a municipal issue (casual chat, spam, unrelated), set is_valid_issue to false.

Message to analyze: """
