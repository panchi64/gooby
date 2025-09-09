#!/usr/bin/env python3
"""
Test script for the decision prompt
"""

from config import load_decision_prompt, load_personality

def test_prompts():
    print("Testing prompt loading...")
    
    # Test decision prompt
    try:
        decision = load_decision_prompt()
        print(f"✓ Decision prompt loaded: {len(decision)} characters")
        print(f"  First 100 chars: {decision[:100]}...")
    except Exception as e:
        print(f"✗ Failed to load decision prompt: {e}")
    
    # Test personality prompt
    try:
        personality = load_personality()
        print(f"✓ Personality prompt loaded: {len(personality)} characters")
        print(f"  First 100 chars: {personality[:100]}...")
    except Exception as e:
        print(f"✗ Failed to load personality prompt: {e}")
    
    # Check for key phrases in decision prompt
    if "[SKIP]" in decision and "[RESPOND]" in decision:
        print("✓ Decision prompt contains required tags")
    else:
        print("✗ Decision prompt missing [SKIP] or [RESPOND] tags")
    
    # Check personality doesn't have decision logic
    if "when to respond" not in personality.lower():
        print("✓ Personality prompt correctly separated from decision logic")
    else:
        print("⚠ Personality prompt may still contain decision logic")

if __name__ == "__main__":
    test_prompts()