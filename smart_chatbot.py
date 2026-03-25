"""
Smart AI Chatbot with Google Gemini Integration
Handles natural language complaint routing
"""

import json
import config
from datetime import datetime
import re

#Import new Google Genai SDK
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class SmartChatbot:
    def __init__(self):
        """Initialize Gemini AI Chatbot"""
        self.ai_available = False
        
        if not GEMINI_AVAILABLE:
            print("WARNING: google-genai not installed")
            self.conversation_history = []
            self.context = {}
            return
        
        # Configure Gemini with API key
        try:
            api_key = config.GEMINI_API_KEY
            if not api_key:
                print("WARNING: GEMINI_API_KEY not found in .env")
                self.conversation_history = []
                self.context = {}
                return
            
            # Initialize client
            self.client = genai.Client(api_key=api_key)
            self.model_id = "gemini-2.5-flash"  # Using latest available model
            
            self.ai_available = True
            print(f"SUCCESS: Gemini AI connected successfully ({self.model_id})")
            
        except Exception as e:
            print(f"ERROR: Gemini initialization error: {e}")
            self.ai_available = False
        
        self.conversation_history = []
        self.context = {}
        
        # Define keyword-to-department mappings for direct routing
        self.complaint_keywords = {
            'pothole': {'department': 'Public Works', 'issue_type': 'Pothole', 'priority': 'high'},
            'road damage': {'department': 'Public Works', 'issue_type': 'Road Damage', 'priority': 'high'},
            'pavement': {'department': 'Public Works', 'issue_type': 'Pavement Issue', 'priority': 'medium'},
            'garbage': {'department': 'Sanitation', 'issue_type': 'Garbage Collection', 'priority': 'medium'},
            'trash': {'department': 'Sanitation', 'issue_type': 'Garbage Collection', 'priority': 'medium'},
            'waste': {'department': 'Sanitation', 'issue_type': 'Waste Management', 'priority': 'medium'},
            'street light': {'department': 'Electrical', 'issue_type': 'Street Light', 'priority': 'medium'},
            'streetlight': {'department': 'Electrical', 'issue_type': 'Street Light', 'priority': 'medium'},
            'light not working': {'department': 'Electrical', 'issue_type': 'Street Light', 'priority': 'medium'},
            'water leak': {'department': 'Water Supply', 'issue_type': 'Water Leak', 'priority': 'high'},
            'pipe burst': {'department': 'Water Supply', 'issue_type': 'Pipe Burst', 'priority': 'high'},
            'drainage': {'department': 'Drainage', 'issue_type': 'Drainage Block', 'priority': 'high'},
            'sewer': {'department': 'Drainage', 'issue_type': 'Sewer Issue', 'priority': 'high'},
            'manhole': {'department': 'Public Works', 'issue_type': 'Manhole Issue', 'priority': 'high'}
        }
    
    def _check_direct_keywords(self, user_message):
        """Check if message contains direct complaint keywords and route immediately"""
        msg_lower = user_message.lower()
        sentiment = self._estimate_sentiment(user_message)
        
        # Check each keyword pattern
        for keyword, details in self.complaint_keywords.items():
            if keyword in msg_lower:
                # Direct match found - route immediately!
                return {
                    'service_type': 'complaint',
                    'intent': 'file',
                    'action_needed': True,
                    'department': details['department'],
                    'message': self._add_sentiment_empathy(
                        f"Got it! I see you want to report a {details['issue_type'].lower()} issue. I will route this to the **{details['department']} Department**.",
                        sentiment
                    ),
                    'follow_up_questions': self._generate_follow_up_questions(
                        user_message,
                        service_type='complaint',
                        extracted_info={'issue_type': details['issue_type'], 'priority': details['priority']},
                        sentiment=sentiment
                    ),
                    'confidence': 0.95,
                    'sentiment': sentiment,
                    'extracted_info': {
                        'issue_type': details['issue_type'],
                        'priority': details['priority']
                    }
                }
        
        return None  # No direct keyword match
    
    def chat(self, user_message, citizen_info=None):
        """
        Have an intelligent conversation with the user
        
        Args:
            user_message (str): User's message
            citizen_info (dict): Citizen profile information
            
        Returns:
            dict: Response with type, action, and message
        """
        # Add to conversation history
        self.conversation_history.append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Check for direct keyword match first
        keyword_response = self._check_direct_keywords(user_message)
        if keyword_response:
            response = keyword_response
        elif self.ai_available:
            response = self._gpt_chat(user_message, citizen_info)
        else:
            response = self._fallback_chat(user_message)
        
        # Add response to history
        self.conversation_history.append({
            'role': 'assistant',
            'content': response['message'],
            'timestamp': datetime.now().isoformat()
        })
        
        return response
    
    def _gpt_chat(self, user_message, citizen_info=None):
        """Use Gemini AI to process user message with enhanced context"""
        try:
            # Create detailed instruction prompt with follow-up questions
            instruction = f"""You are an excellent Municipal Services AI assistant that helps citizens report civic issues effectively.

The citizen says: "{user_message}"

IMPORTANT: Ask intelligent follow-up questions to gather complete information for better resolution.

Analyze this and respond with JSON containing:
- service_type: complaint, building_plan, water_connection, or general_inquiry
- intent: file, track, apply, or inquire  
- department: the relevant municipal department (Public Works, Sanitation, Electrical, Water Supply, Drainage, Roads, etc.)
- message: a friendly, empathetic response (3-4 sentences) that acknowledges their concern and asks for more details
- follow_up_questions: array of 2-3 specific questions to gather more information about the issue (e.g., "When did you first notice this?", "How severe is the damage?", "Any injuries or safety hazards?")
- sentiment: {{"label": "positive/neutral/negative", "score": 0.0 to 1.0}}
- extracted_info: {{"location": "if mentioned", "issue_type": "type of complaint", "priority": "high/medium/low", "mention_count": "if mentioned", "urgency_indicators": []}}

CRITICAL INSTRUCTIONS:
1. Show genuine empathy and understanding for their situation
2. Ask specific follow-up questions relevant to their exact complaint
3. Try to understand urgency from their tone
4. If they mention safety hazard, priority should be HIGH
5. Extract any numbers they mention (e.g., "3 days", "20 meters")
6. Make the message conversational and human-like, NOT generic

FOLLOW-UP QUESTION EXAMPLES FOR DIFFERENT ISSUES:
- For water leaks: "Is water pooling on the road?" "How much water is escaping?" "Any damage to nearby properties?"
- For roads: "What's the size of the pothole?" "Is it affecting traffic?" "Have you seen any accidents?"
- For garbage: "How long has garbage been accumulating?" "Is it blocking the street?" "Any health concerns?"
- For street lights: "How many lights are out?" "What area is affected?" "Any dark spots causing safety issues?"
- For drainage: "Is water backing up into homes?" "Any foul smell?" "Is it blocking the street?"

Respond ONLY with valid JSON, no other text."""

            response = self.client.models.generate_content(
                model=f"models/{self.model_id}",
                contents=instruction
            )
            
            result_text = response.text.strip()
            print(f"DEBUG: Raw Gemini response: {result_text[:150]}")
            
            # Clean JSON markers
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()
            elif result_text.startswith("```"):
                result_text = result_text.replace("```", "").strip()
            
            # Parse JSON
            result = json.loads(result_text)

            # Normalize sentiment returned by model
            result["sentiment"] = self._normalize_sentiment(result.get("sentiment"), user_message)
            
            # Add defaults if missing
            if "confidence" not in result:
                result["confidence"] = 0.9
            if "action_needed" not in result:
                result["action_needed"] = False
            if "follow_up_questions" not in result:
                result["follow_up_questions"] = None
            if "extracted_info" not in result:
                result["extracted_info"] = {}
            
            print(f"SUCCESS: Gemini AI successfully generated response")
            
            # Post-process
            result = self._postprocess_response(result, user_message)
            
            # Store context
            self.context.update(result.get('extracted_info', {}))
            
            return result
            
        except Exception as e:
            print(f"ERROR: Gemini API error: {type(e).__name__}: {str(e)[:200]}")
            print(f"WARNING: Falling back to rule-based responses")
            return self._fallback_chat(user_message)
    
    def _fallback_chat(self, user_message):
        """Simple rule-based fallback when AI is not available"""
        msg_lower = user_message.lower()
        sentiment = self._estimate_sentiment(user_message)
        
        # Greetings
        if any(word in msg_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return {
                'service_type': 'greeting',
                'intent': 'chat',
                'action_needed': False,
                'department': 'General',
                'message': self._add_sentiment_empathy("👋 Hello! I'm your Municipal Services Assistant. I can help you with complaints, property tax, certificates, licenses, building plans, water connections, and park bookings. What can I assist you with today?", sentiment),
                'follow_up_questions': None,
                'sentiment': sentiment,
                'extracted_info': {}
            }
        
        # Complaints
        elif any(word in msg_lower for word in ['pothole', 'road', 'broken', 'garbage', 'leak', 'light', 'street', 'drainage']):
            return {
                'service_type': 'complaint',
                'intent': 'file',
                'action_needed': True,
                'department': self._detect_department(msg_lower),
                'message': self._add_sentiment_empathy(
                    f"I understand you want to report an issue. I'm here to help! The **{self._detect_department(msg_lower)} Department** will handle this.\n\nTo better assist you, could you provide some details?",
                    sentiment
                ),
                'follow_up_questions': self._generate_follow_up_questions(
                    user_message,
                    service_type='complaint',
                    extracted_info={'issue_type': self._detect_issue_type(msg_lower)},
                    sentiment=sentiment
                ),
                'sentiment': sentiment,
                'extracted_info': {
                    'issue_type': self._detect_issue_type(msg_lower),
                    'priority': 'high' if any(word in msg_lower for word in ['urgent', 'danger', 'broken', 'leak', 'damage']) else 'medium'
                }
            }
        
        # Property Tax
        elif any(word in msg_lower for word in ['property tax', 'tax payment', 'tax due', 'pay tax']):
            return {
                'service_type': 'property_tax',
                'intent': 'inquire',
                'action_needed': False,
                'department': 'Property Tax',
                'message': self._add_sentiment_empathy("I can help you with property tax services! You can:\n\n💰 **Pay Tax** - Make online payments\n📋 **Check Dues** - See pending amounts\n➕ **Register Property** - Add new property\n\nWhat would you like to do?", sentiment),
                'follow_up_questions': None,
                'sentiment': sentiment,
                'extracted_info': {}
            }
        
        # Certificates
        elif any(word in msg_lower for word in ['birth certificate', 'death certificate', 'certificate']):
            return {
                'service_type': 'certificate',
                'intent': 'inquire',
                'action_needed': False,
                'department': 'Certificates',
                'message': self._add_sentiment_empathy("I can help you apply for certificates! We offer:\n\n👶 **Birth Certificate**\n🕊️ **Death Certificate**\n\nWhich one do you need? I'll guide you through the application process.", sentiment),
                'follow_up_questions': None,
                'sentiment': sentiment,
                'extracted_info': {}
            }
        
        # General Help
        elif any(word in msg_lower for word in ['help', 'what can you do', 'services', 'how']):
            return {
                'service_type': 'general_inquiry',
                'intent': 'inquire',
                'action_needed': False,
                'department': 'General',
                'message': self._add_sentiment_empathy("""I'm here to help! Here are all the services I can assist you with:

📝 **Complaints** - Report civic issues (roads, water, garbage, etc.)
🏠 **Property Tax** - Manage tax payments and properties
📜 **Certificates** - Apply for birth/death certificates
🏪 **Trade Licenses** - Business license applications
🏗️ **Building Plans** - Submit construction plans
💧 **Water Connection** - New connection applications
🌳 **Park Booking** - Book parks and facilities

Just tell me what you need, and I'll guide you through it!""", sentiment),
                'follow_up_questions': None,
                'sentiment': sentiment,
                'extracted_info': {}
            }
        
        # Default
        else:
            return {
                'service_type': 'general_inquiry',
                'intent': 'inquire',
                'action_needed': False,
                'department': 'General',
                'message': self._add_sentiment_empathy("I'm here to help! Could you please tell me more about what you need? Are you looking to:\n\n• Report a complaint\n• Pay property tax\n• Apply for certificates\n• Get a trade license\n• Submit building plans\n• Request water connection\n• Book a park facility\n\nOr ask me anything else!", sentiment),
                'follow_up_questions': None,
                'confidence': 0.4,
                'sentiment': sentiment,
                'extracted_info': {}
            }

    def _postprocess_response(self, result, user_message):
        """Normalize and strengthen response behavior"""
        service_type = result.get("service_type")
        extracted = result.get("extracted_info", {})
        location = (extracted.get("location") or "").strip()
        sentiment = self._normalize_sentiment(result.get("sentiment"), user_message)
        result["sentiment"] = sentiment

        if service_type == "complaint":
            result["follow_up_questions"] = self._generate_follow_up_questions(
                user_message,
                service_type='complaint',
                extracted_info=extracted,
                sentiment=sentiment,
                existing_questions=result.get("follow_up_questions")
            )

        if service_type == "complaint" and not location:
            result["action_needed"] = False
            if "message" in result:
                result["message"] = result["message"].rstrip() + "\n\nPlease share the exact location to file the complaint."

        confidence = result.get("confidence", 0.5)
        if confidence < 0.5 and not result.get("follow_up_questions"):
            result["follow_up_questions"] = [
                "Could you provide a bit more detail so I can help you better?"
            ]

        if "message" in result:
            result["message"] = self._add_sentiment_empathy(result["message"], sentiment)

        return result

    def _estimate_sentiment(self, user_message):
        """Estimate sentiment using weighted keyword scoring"""
        msg_lower = user_message.lower()

        negative_weights = {
            'angry': -0.7, 'upset': -0.5, 'annoyed': -0.4, 'frustrated': -0.6,
            'terrible': -0.7, 'worst': -0.9, 'bad': -0.35, 'danger': -0.8,
            'unsafe': -0.8, 'urgent': -0.7, 'emergency': -0.95, 'hate': -0.8,
            'pathetic': -0.8, 'disgusting': -0.9, 'fed up': -0.8, 'immediately': -0.4,
            'accident': -0.6, 'injury': -0.8, 'flooding': -0.7
        }
        positive_weights = {
            'thanks': 0.45, 'thank you': 0.55, 'appreciate': 0.6, 'good': 0.3,
            'great': 0.55, 'helpful': 0.45, 'please': 0.2, 'excellent': 0.7,
            'resolved': 0.6, 'better': 0.25, 'happy': 0.65
        }

        score = 0.0
        for phrase, weight in negative_weights.items():
            if phrase in msg_lower:
                score += weight
        for phrase, weight in positive_weights.items():
            if phrase in msg_lower:
                score += weight

        exclamation_hits = user_message.count('!')
        if exclamation_hits >= 2 and score <= 0:
            score -= 0.15

        score = max(-1.0, min(1.0, score))
        if score <= -0.2:
            label = 'negative'
        elif score >= 0.2:
            label = 'positive'
        else:
            label = 'neutral'

        return {'label': label, 'score': round(score, 2)}

    def _normalize_sentiment(self, sentiment_value, user_message):
        """Normalize sentiment shape and fallback if invalid"""
        fallback = self._estimate_sentiment(user_message)

        if isinstance(sentiment_value, dict):
            label = str(sentiment_value.get('label', fallback['label'])).strip().lower()
            try:
                score = float(sentiment_value.get('score', fallback['score']))
            except Exception:
                score = fallback['score']

            if label not in {'positive', 'neutral', 'negative'}:
                label = fallback['label']
            score = max(-1.0, min(1.0, score))
            return {'label': label, 'score': round(score, 2)}

        return fallback

    def _add_sentiment_empathy(self, message, sentiment):
        """Add brief empathy prefix for negative sentiment"""
        if not isinstance(message, str):
            return message

        label = (sentiment or {}).get('label', 'neutral')
        if label == 'negative':
            lower_msg = message.lower()
            empathy_markers = ['sorry', 'understand this is frustrating', 'that sounds stressful']
            if not any(marker in lower_msg for marker in empathy_markers):
                return "I'm sorry you're facing this. " + message
        return message

    def _generate_follow_up_questions(self, user_message, service_type, extracted_info=None, sentiment=None, existing_questions=None):
        """Generate targeted follow-up questions to improve complaint quality"""
        if service_type != 'complaint':
            return existing_questions

        extracted_info = extracted_info or {}
        msg_lower = user_message.lower()
        issue_type = str(extracted_info.get('issue_type') or self._detect_issue_type(msg_lower) or '').lower()
        priority = str(extracted_info.get('priority') or '').lower()

        question_pool = [
            'What is the exact location? (street name, landmark, or nearest building)',
            'When did you first notice this issue?'
        ]

        if any(word in issue_type for word in ['pothole', 'road', 'pavement']):
            question_pool.extend([
                'What is the approximate size/depth of the road damage?',
                'Is this affecting traffic flow or causing accident risk?'
            ])
        elif any(word in issue_type for word in ['water leak', 'pipe', 'water']):
            question_pool.extend([
                'Is water continuously leaking or intermittent?',
                'Is nearby property, road, or public area being damaged?'
            ])
        elif any(word in issue_type for word in ['garbage', 'waste', 'trash']):
            question_pool.extend([
                'How long has garbage been accumulating here?',
                'Is there a foul smell or visible health risk in this area?'
            ])
        elif any(word in issue_type for word in ['street light', 'light']):
            question_pool.extend([
                'How many street lights are not working in this area?',
                'Does the darkness create a safety concern at night?'
            ])
        elif any(word in issue_type for word in ['drainage', 'sewer', 'manhole']):
            question_pool.extend([
                'Is water/sewage overflowing into roads or homes?',
                'Any foul smell or blockage affecting movement?'
            ])
        else:
            question_pool.extend([
                'How severe is this issue for daily public use?',
                'Are there any immediate safety hazards?'
            ])

        if priority == 'high' or any(word in msg_lower for word in ['urgent', 'danger', 'emergency', 'unsafe']):
            question_pool.append('Has this caused any injury, accident, or immediate risk to citizens?')

        if (sentiment or {}).get('label') == 'negative':
            question_pool.append('Would you like this marked for urgent municipal review?')

        for source in (existing_questions or []):
            if isinstance(source, str) and source.strip():
                question_pool.insert(0, source.strip())

        deduped = []
        seen = set()
        for q in question_pool:
            key = re.sub(r'\s+', ' ', q.strip().lower())
            if key and key not in seen:
                seen.add(key)
                deduped.append(q.strip())

        return deduped[:3] if deduped else None
    
    def _detect_department(self, text):
        """Detect department from text"""
        if any(word in text for word in ['road', 'pothole', 'street', 'pavement']):
            return 'Public Works'
        elif any(word in text for word in ['water', 'leak', 'pipe', 'supply']):
            return 'Water Supply'
        elif any(word in text for word in ['garbage', 'trash', 'waste', 'cleanliness']):
            return 'Sanitation'
        elif any(word in text for word in ['light', 'streetlight', 'electricity', 'lamp']):
            return 'Electrical'
        elif any(word in text for word in ['drainage', 'sewer', 'flood', 'manhole']):
            return 'Drainage'
        elif any(word in text for word in ['park', 'garden', 'playground']):
            return 'Parks'
        elif any(word in text for word in ['health', 'mosquito', 'disease']):
            return 'Health'
        elif any(word in text for word in ['building', 'construction', 'illegal']):
            return 'Building'
        else:
            return 'General'
    
    def _detect_issue_type(self, text):
        """Detect specific issue type"""
        if 'pothole' in text:
            return 'Pothole'
        elif 'garbage' in text or 'waste' in text or 'trash' in text:
            return 'Garbage Collection'
        elif 'light' in text or 'streetlight' in text:
            return 'Street Light'
        elif 'leak' in text or 'water' in text:
            return 'Water Leak'
        elif 'drainage' in text or 'sewer' in text:
            return 'Drainage Issue'
        else:
            return 'Other'
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.context = {}
    
    def get_context(self):
        """Get current conversation context"""
        return self.context
