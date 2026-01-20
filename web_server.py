#!/usr/bin/env python3
"""
JARVIS Web Server
Browser-based interface with speech recognition
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import logging
import sys
from pathlib import Path

# Add project root to path
JARVIS_ROOT = Path(__file__).parent
sys.path.insert(0, str(JARVIS_ROOT))

from core.brain import get_brain
from core.dispatcher import get_dispatcher
from core.memory import get_memory
from config import ASSISTANT_NAME, USER_NAME

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for API calls

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize JARVIS components
brain = get_brain()
dispatcher = get_dispatcher()
memory = get_memory()

# Load all skills
from skills import system, apps, time_date, web, conversation

logger.info("JARVIS Web Server initialized")


@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Handle chat messages from the web interface
    
    Expected JSON:
    {
        "message": "user's message"
    }
    
    Returns JSON:
    {
        "response": "JARVIS response",
        "success": true
    }
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': 'No message provided'
            }), 400
        
        logger.info(f"User: {user_message}")
        
        # Classify intent
        intent = brain.classify_intent(user_message)
        logger.debug(f"Intent: {intent.category.name}.{intent.action} (confidence: {intent.confidence})")
        
        # Dispatch to appropriate handler
        result = dispatcher.dispatch(intent)
        
        # Extract response
        if result.get('success'):
            handler_result = result.get('result', {})
            
            if isinstance(handler_result, dict):
                response_text = handler_result.get('response', 'Done.')
            else:
                response_text = str(handler_result)
        else:
            response_text = "I apologize, I encountered an issue processing that request."
            logger.error(f"Dispatch failed: {result.get('error')}")
        
        logger.info(f"JARVIS: {response_text}")
        
        return jsonify({
            'success': True,
            'response': response_text,
            'intent': {
                'category': intent.category.name,
                'action': intent.action,
                'confidence': intent.confidence
            }
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/status', methods=['GET'])
def status():
    """Get JARVIS status"""
    try:
        from core.ai import get_ai
        ai = get_ai()
        
        return jsonify({
            'success': True,
            'status': 'online',
            'name': ASSISTANT_NAME,
            'user': USER_NAME,
            'ai_enabled': ai.is_available(),
            'skills_loaded': len(dispatcher._handlers)
        })
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/skills', methods=['GET'])
def get_skills():
    """Get list of available skills"""
    try:
        skills = dispatcher.get_registered_skills()
        return jsonify({
            'success': True,
            'skills': skills
        })
    except Exception as e:
        logger.error(f"Skills error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print(f"🌐 JARVIS Web Interface Starting...")
    print(f"Open your browser to: http://localhost:5000")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False  # Avoid double initialization
    )
