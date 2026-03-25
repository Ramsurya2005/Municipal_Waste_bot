"""
NLP Classifier module using Google Gemini API
Handles issue detection and classification
"""

import json
import config

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class IssueClassifier:
    def __init__(self):
        """Initialize Gemini API"""
        self.model = "gemini-2.5-flash"
        self.ai_available = False
        
        if not GEMINI_AVAILABLE:
            print("WARNING: google-genai not installed. Install with: pip install google-genai")
            return
        
        try:
            api_key = config.GEMINI_API_KEY
            if not api_key:
                print("ERROR: GEMINI_API_KEY not found in environment")
                return
            
            self.client = genai.Client(api_key=api_key)
            self.ai_available = True
            print(f"INFO: Gemini API connected successfully ({self.model})")
        except Exception as e:
            self.ai_available = False
            print(f"ERROR: Failed to initialize Gemini: {e}")
    
    def classify_message(self, user_message):
        """
        Classify a user message using Google Gemini
        
        Args:
            user_message (str): The user's complaint message
            
        Returns:
            dict: Classification results
        """
        try:
            if not self.ai_available:
                return self._fallback_classification(user_message)
            
            # Prepare the prompt
            full_prompt = config.CLASSIFICATION_PROMPT + f"\n\n{user_message}"
            
            # Call Gemini API
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    {
                        "role": "user",
                        "parts": [{"text": full_prompt}]
                    }
                ],
                config={
                    "temperature": 0.3,
                }
            )
            
            # Extract response
            result_text = response.text.strip()
            
            # Parse JSON response
            # Sometimes the model wraps JSON in markdown code blocks
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()
            elif result_text.startswith("```"):
                result_text = result_text.replace("```", "").strip()
            
            result = json.loads(result_text)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return self._fallback_classification(user_message)
        except Exception as e:
            print(f"Classification error: {e}")
            return self._fallback_classification(user_message)
    
    def _fallback_classification(self, user_message):
        """Fallback classification when API fails"""
        text_lower = user_message.lower()
        
        # Simple keyword-based classification
        classifications = {
            "pothole": {"category": "roads", "urgency": "high", "confidence": 0.9},
            "road": {"category": "roads", "urgency": "medium", "confidence": 0.8},
            "water": {"category": "water", "urgency": "high", "confidence": 0.9},
            "leak": {"category": "water", "urgency": "high", "confidence": 0.85},
            "garbage": {"category": "sanitation", "urgency": "medium", "confidence": 0.9},
            "trash": {"category": "sanitation", "urgency": "medium", "confidence": 0.85},
            "light": {"category": "electrical", "urgency": "low", "confidence": 0.8},
            "traffic": {"category": "traffic", "urgency": "high", "confidence": 0.9},
            "electricity": {"category": "electrical", "urgency": "medium", "confidence": 0.85},
        }
        
        detected_category = "other"
        detected_urgency = "medium"
        detected_confidence = 0.5
        
        for keyword, details in classifications.items():
            if keyword in text_lower:
                detected_category = details["category"]
                detected_urgency = details["urgency"]
                detected_confidence = details["confidence"]
                break
        
        return {
            "is_valid_issue": True,
            "category": detected_category,
            "confidence": detected_confidence,
            "summary": user_message[:200],
            "location": "Not specified",
            "urgency": detected_urgency,
            "reason": "Fallback classification used"
        }
    
    def generate_acknowledgment(self, classification_result, department_info):
        """
        Generate a user-friendly acknowledgment message
        
        Args:
            classification_result (dict): Result from classify_message
            department_info (dict): Department details
            
        Returns:
            str: Acknowledgment message
        """
        if not classification_result.get("is_valid_issue", False):
            return ("I couldn't identify this as a municipal issue. "
                   "Please describe issues like potholes, water leakage, garbage collection, "
                   "streetlight problems, or other civic infrastructure concerns.")
        
        category = classification_result.get("category", "other")
        summary = classification_result.get("summary", "your issue")
        location = classification_result.get("location", "your area")
        urgency = classification_result.get("urgency", "medium")
        
        dept_name = department_info.get("name", "Appropriate Department")
        dept_icon = department_info.get("icon", "📋")
        
        urgency_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(urgency, "🟡")
        
        message = f"""
✅ **Issue Recorded Successfully!**

{dept_icon} **Department**: {dept_name}
📝 **Summary**: {summary}
📍 **Location**: {location}
{urgency_emoji} **Urgency**: {urgency.capitalize()}

Your complaint has been forwarded to the {dept_name}.
A tracking ID will be generated and the department will review your issue shortly.

Thank you for helping keep our city better! 🏙️
"""
        return message.strip()
