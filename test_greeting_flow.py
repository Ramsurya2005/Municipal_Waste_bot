#!/usr/bin/env python3
"""Test the greeting flow to debug why it's still filing complaints"""

import sys
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

from smart_chatbot import SmartChatbot
from classifier import IssueClassifier
import config

print("=" * 70)
print("TEST: Greeting Flow in Municipal Chatbot")
print("=" * 70)

# Initialize
smart_chatbot = SmartChatbot()
classifier = IssueClassifier()
user_info = {"citizen_id": "test_123"}

print(f"\nSmartChatbot initialized: ai_available={smart_chatbot.ai_available}")
print(f"IssueClassifier initialized: ai_available={classifier.ai_available}")

def process_user_message(user_input):
    """Exact copy of the app's process_user_message function"""
    
    chatbot = smart_chatbot

    # 1) AI conversational intent detection (handles greetings correctly)
    if chatbot:
        ai_result = chatbot.chat(user_input, user_info)
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
    
    print(f"DEBUG process_user_message: input='{user_input}' -> service_type='{service_type}' intent='{intent}' action_needed={action_needed}")

    # If this is greeting/general inquiry, do not create complaint
    if service_type in ["greeting", "general_inquiry"] and not action_needed:
        print(f"DEBUG: EARLY RETURN - Not filing complaint for {service_type}")
        response = ai_result.get("message", "Hello! How can I help you today?")
        followups = ai_result.get("follow_up_questions") or []
        if followups:
            response += "\n\nFollow-up Questions:"
            for question in followups:
                response += f"\n- {question}"
        return {
            "response": response,
            "filed_complaint": False,
            "complaint_id": None
        }

    # 2) Complaint classification and routing metadata
    classification = classifier.classify_message(user_input)

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

    # 3) Save complaint only for actual complaint-file intents
    should_file = service_type == "complaint" and intent == "file"
    complaint_id = None
    print(f"DEBUG: should_file={should_file} (service_type={service_type}, intent={intent})")
    if should_file and classification.get("is_valid_issue", True):
        print("DEBUG: WOULD FILE COMPLAINT TO DATABASE")
        # In real app, this would save to database
        complaint_id = "COMPLAINT_123"

    # 4) Build response
    response = ai_result.get("message") or classifier.generate_acknowledgment(
        classification,
        department_info
    )

    followups = ai_result.get("follow_up_questions") or []
    if followups:
        response += "\n\nFollow-up Questions:"
        for question in followups:
            response += f"\n- {question}"

    if complaint_id:
        response += f"\n\nTracking ID: {complaint_id}"

    return {
        "response": response,
        "filed_complaint": bool(complaint_id),
        "complaint_id": complaint_id
    }

# Test cases
test_cases = [
    "hii",
    "hello",
    "good morning",
    "pothole on main street",
    "water leak"
]

for test_input in test_cases:
    print(f"\n{'-' * 70}")
    print(f"TEST INPUT: '{test_input}'")
    print('-' * 70)
    result = process_user_message(test_input)
    print(f"\nRESULT:")
    print(f"  Filed Complaint: {result['filed_complaint']}")
    print(f"  Complaint ID: {result['complaint_id']}")
    print(f"  Response Preview: {result['response'][:100]}...")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
