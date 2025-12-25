"""
LangGraph Chat Service for AI Practice Conversations.

This module provides a conversational AI service using LangGraph with Groq
for the AI Practice feature. It manages conversation state and generates contextual
responses based on user level, formality, and scenario.
"""

import os
from typing import TypedDict, Optional
from pathlib import Path
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.core.logging import get_logger

# Load environment variables from the correct path
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize logger
logger = get_logger(__name__)


class ChatState(TypedDict):
    """State for the conversation graph."""
    messages: list  # Conversation history
    scenario: dict  # Scenario metadata (level, formality, aiPrompt, etc.)
    user_message: str  # Current user message
    ai_response: str  # AI response
    correction: Optional[str]  # Grammar correction if applicable


def get_groq_model():
    """Get the Groq model instance."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error(f"GROQ_API_KEY not found. Env path: {env_path}, exists: {env_path.exists()}")
        raise ValueError("GROQ_API_KEY environment variable is not set")
    
    logger.debug(f"GROQ_API_KEY loaded successfully (length: {len(api_key)})")
    
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=api_key,
        temperature=0.7,
    )


def build_system_prompt(scenario: dict) -> str:
    """Build the system prompt based on scenario metadata."""
    level = scenario.get("level", "A1")
    formality = scenario.get("formality", "casual")
    ai_role = scenario.get("aiRole", "a friendly French speaker")
    ai_prompt = scenario.get("aiPrompt", "")
    title = scenario.get("title", "French conversation")
    
    # CEFR level guidelines
    level_guidelines = {
        "A1": "Use very simple vocabulary and short sentences. Stick to present tense. Speak slowly and clearly.",
        "A2": "Use simple vocabulary and basic sentence structures. Include common phrases. Use present and simple past tenses.",
        "B1": "Use intermediate vocabulary. Include compound sentences. Use various tenses including future.",
        "B2": "Use varied vocabulary and complex sentences. Include idiomatic expressions. Use all common tenses.",
        "C1": "Use advanced vocabulary and sophisticated structures. Include nuanced expressions and cultural references.",
        "C2": "Use native-level French with full range of vocabulary, idioms, and cultural nuances.",
    }
    
    formality_style = "casual and friendly" if formality == "casual" else "polite and formal"
    level_guide = level_guidelines.get(level.upper(), level_guidelines["A1"])
    
    system_prompt = f"""You are {ai_role} helping a French language learner practice conversation.

SCENARIO: {title}
{ai_prompt}

IMPORTANT RULES:
1. ALWAYS respond in French only (no English unless translating for corrections)
2. Match the learner's CEFR level ({level}): {level_guide}
3. Be {formality_style} in your communication style
4. Keep responses concise (2-4 sentences typically)
5. Stay in character and maintain the conversation flow
6. If the user makes grammar mistakes, note them but continue the conversation naturally

GRAMMAR CORRECTION FORMAT:
If you notice grammar errors in the user's message, start your response with a correction in this exact format:
[CORRECTION: corrected sentence here]

Then continue with your natural conversational response.

If the user's French is correct, just respond normally without any correction tag."""

    return system_prompt


def process_message(state: ChatState) -> ChatState:
    """Process user message and generate AI response."""
    logger.debug(f"Processing message: {state['user_message'][:50]}...")
    
    try:
        model = get_groq_model()
        
        # Build messages list
        messages = []
        
        # Add system prompt
        system_prompt = build_system_prompt(state["scenario"])
        messages.append(SystemMessage(content=system_prompt))
        
        # Add conversation history
        for msg in state.get("messages", []):
            if msg.get("sender") == "user":
                messages.append(HumanMessage(content=msg.get("text", "")))
            elif msg.get("sender") == "ai":
                messages.append(AIMessage(content=msg.get("text", "")))
        
        # Add current user message
        messages.append(HumanMessage(content=state["user_message"]))
        
        # Generate response
        response = model.invoke(messages)
        response_text = response.content
        
        # Parse correction if present
        correction = None
        ai_response = response_text
        
        if "[CORRECTION:" in response_text:
            parts = response_text.split("]", 1)
            if len(parts) == 2:
                correction = parts[0].replace("[CORRECTION:", "").strip()
                ai_response = parts[1].strip()
        
        logger.debug(f"AI response generated: {ai_response[:50]}...")
        
        return {
            **state,
            "ai_response": ai_response,
            "correction": correction,
        }
    
    except Exception as e:
        logger.exception(f"Error generating AI response: {str(e)}")
        return {
            **state,
            "ai_response": "Je suis désolé, je n'ai pas pu répondre. Pouvez-vous répéter ?",
            "correction": None,
        }


def create_chat_graph() -> StateGraph:
    """Create the LangGraph conversation graph."""
    graph = StateGraph(ChatState)
    
    # Add nodes
    graph.add_node("process_message", process_message)
    
    # Set entry point
    graph.set_entry_point("process_message")
    
    # Add edge to end
    graph.add_edge("process_message", END)
    
    return graph.compile()


def generate_initial_greeting(scenario: dict) -> dict:
    """Generate an initial AI greeting for a new conversation."""
    logger.info(f"Generating initial greeting for scenario: {scenario.get('title', 'Unknown')}")
    
    try:
        model = get_groq_model()
        system_prompt = build_system_prompt(scenario)
        
        greeting_prompt = f"""{system_prompt}

Start the conversation with a friendly greeting appropriate for this scenario. 
Keep it short (1-2 sentences) and invite the user to respond."""
        
        response = model.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content="Please start the conversation with an appropriate greeting.")
        ])
        
        logger.debug(f"Initial greeting generated: {response.content[:50]}...")
        
        return {
            "ai_response": response.content,
            "correction": None,
        }
    
    except Exception as e:
        logger.exception(f"Error generating initial greeting: {str(e)}")
        return {
            "ai_response": "Bonjour ! Comment allez-vous aujourd'hui ?",
            "correction": None,
        }


def chat(
    user_message: str,
    conversation_history: list,
    scenario: dict
) -> dict:
    """
    Main entry point for chat functionality.
    
    Args:
        user_message: The user's message in French
        conversation_history: List of previous messages
        scenario: Scenario metadata (level, formality, aiPrompt, etc.)
    
    Returns:
        dict with ai_response, correction, and updated conversation_history
    """
    logger.info(f"Processing chat | scenario={scenario.get('title', 'Unknown')} | level={scenario.get('level', 'A1')}")
    
    # Create initial state
    state = ChatState(
        messages=conversation_history,
        scenario=scenario,
        user_message=user_message,
        ai_response="",
        correction=None,
    )
    
    # Run the graph
    graph = create_chat_graph()
    result = graph.invoke(state)
    
    # Build updated conversation history
    new_history = list(conversation_history)
    new_history.append({
        "sender": "user",
        "text": user_message,
    })
    new_history.append({
        "sender": "ai",
        "text": result["ai_response"],
        "correction": result.get("correction"),
    })
    
    return {
        "ai_response": result["ai_response"],
        "correction": result.get("correction"),
        "conversation_history": new_history,
    }
