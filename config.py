import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    # Discord Configuration
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    ALLOWED_SERVER_ID = int(os.getenv('ALLOWED_SERVER_ID')) if os.getenv('ALLOWED_SERVER_ID') else None
    BOT_PREFIX = os.getenv('BOT_PREFIX', '!')
    
    # LM Studio Configuration
    LM_STUDIO_URL = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1/chat/completions')
    LM_STUDIO_TIMEOUT = int(os.getenv('LM_STUDIO_TIMEOUT', '30'))
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', '500'))
    TEMPERATURE = float(os.getenv('TEMPERATURE', '0.8'))
    
    # Bot Personality
    BOT_NAME = os.getenv('BOT_NAME', 'Gooby')
    RESPONSE_CHANCE = float(os.getenv('RESPONSE_CHANCE', '0.3'))
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', './data/gooby.db')
    
    # Validation
    @classmethod
    def validate(cls):
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN is required in .env file")
        if not cls.ALLOWED_SERVER_ID:
            raise ValueError("ALLOWED_SERVER_ID is required in .env file")
        return True

def load_personality(filename: str = "gooby_personality.md") -> str:
    """
    Load Gooby's personality from a file
    
    Args:
        filename: Name of the personality file to load
        
    Returns:
        The personality prompt as a string
    """
    personality_path = Path(filename)
    
    try:
        with open(personality_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
            # Remove markdown headers and format for LLM
            lines = content.split('\n')
            cleaned_lines = []
            
            for line in lines:
                # Skip markdown headers, separators, and empty lines
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('---'):
                    cleaned_lines.append(line)
            
            personality = ' '.join(cleaned_lines)
            
            # Clean up extra spaces
            while '  ' in personality:
                personality = personality.replace('  ', ' ')
            
            logger.info(f"Successfully loaded personality from {filename}")
            return personality
            
    except FileNotFoundError:
        logger.error(f"Personality file {filename} not found and no fallback available")
        raise FileNotFoundError(f"Required personality file {filename} not found")
    except Exception as e:
        logger.error(f"Error loading personality file {filename}: {e}")
        raise Exception(f"Failed to load personality file {filename}: {e}")


def load_decision_prompt(filename: str = "gooby_decision.md") -> str:
    """
    Load Gooby's decision-making prompt from a file
    
    Args:
        filename: Name of the decision file to load
        
    Returns:
        The decision prompt as a string
    """
    decision_path = Path(filename)
    
    try:
        with open(decision_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
            # Remove markdown headers and format for LLM
            lines = content.split('\n')
            cleaned_lines = []
            
            for line in lines:
                # Skip markdown headers, separators, and empty lines
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('---'):
                    cleaned_lines.append(line)
            
            decision = ' '.join(cleaned_lines)
            
            # Clean up extra spaces
            while '  ' in decision:
                decision = decision.replace('  ', ' ')
            
            logger.info(f"Successfully loaded decision prompt from {filename}")
            return decision
            
    except FileNotFoundError:
        logger.error(f"Decision file {filename} not found, using fallback")
        # Simple fallback
        return "Analyze the conversation and decide if Gooby should respond. Reply with [SKIP] or [RESPOND]."
    except Exception as e:
        logger.error(f"Error loading decision file {filename}: {e}")
        return "Analyze the conversation and decide if Gooby should respond. Reply with [SKIP] or [RESPOND]."


# Load Gooby's personality from file
GOOBY_SYSTEM_PROMPT = load_personality()
GOOBY_DECISION_PROMPT = load_decision_prompt()