#!/usr/bin/env python3
"""
End-to-end test script for LM Studio API to debug duplicate message issues
This simulates the full bot flow: decision -> response
"""

import asyncio
import aiohttp
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime

# Configuration (adjust these to match your setup)
LM_STUDIO_URL = 'http://localhost:1234/v1/chat/completions'
TIMEOUT = 30
TEMPERATURE = 0.8
MAX_TOKENS = 500

# Load prompts
def load_decision_prompt():
    """Load the decision prompt from file"""
    with open('gooby_decision.md', 'r', encoding='utf-8') as f:
        content = f.read().strip()

    # Process like config.py does
    lines = content.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('---'):
            cleaned_lines.append(line)

    decision = ' '.join(cleaned_lines)
    while '  ' in decision:
        decision = decision.replace('  ', ' ')

    return decision

def load_personality_prompt():
    """Load the personality prompt from file"""
    with open('gooby_personality.md', 'r', encoding='utf-8') as f:
        content = f.read().strip()

    # Process like config.py does
    lines = content.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('---'):
            cleaned_lines.append(line)

    personality = ' '.join(cleaned_lines)
    while '  ' in personality:
        personality = personality.replace('  ', ' ')

    return personality

async def make_lm_studio_call(messages: List[Dict], system_prompt: str, call_type: str):
    """
    Make a single call to LM Studio and log everything
    """
    print(f"\n{'='*60}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Making {call_type} call to LM Studio")
    print(f"{'='*60}")

    # Build the full message list
    chat_messages = []

    if system_prompt:
        chat_messages.append({
            "role": "system",
            "content": system_prompt
        })
        print(f"System prompt length: {len(system_prompt)} chars")
        print(f"System prompt preview: {system_prompt[:100]}...")

    for msg in messages:
        chat_messages.append(msg)

    print(f"Total messages: {len(chat_messages)}")
    print(f"User message: {messages[0]['content'][:200]}...")

    # Prepare request payload
    payload = {
        "model": "gpt-3.5-turbo",  # LM Studio ignores this
        "messages": chat_messages,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "stream": False
    }

    # Save payload for debugging
    with open(f'debug_{call_type}_payload.json', 'w') as f:
        json.dump(payload, f, indent=2)
    print(f"Payload saved to debug_{call_type}_payload.json")

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as session:
            print(f"Sending POST request to {LM_STUDIO_URL}")

            async with session.post(LM_STUDIO_URL, json=payload) as response:
                print(f"Response status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

                    print(f"Response received: {len(content)} chars")
                    print(f"Response preview: {content[:200]}...")

                    # Save response for debugging
                    with open(f'debug_{call_type}_response.json', 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"Response saved to debug_{call_type}_response.json")

                    return content.strip()
                else:
                    error_text = await response.text()
                    print(f"ERROR: {error_text}")
                    return None

    except asyncio.TimeoutError:
        print("ERROR: Request timed out")
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def parse_decision_response(decision: str) -> str:
    """Parse the decision response (LM Studio now handles reasoning natively)"""
    print(f"\nParsing decision response...")

    # Use the response directly since LM Studio handles reasoning natively
    final_response = decision.strip()
    print(f"Using response directly: {final_response[:100]}...")

    # Look for decision in the response
    if "[RESPOND]" in final_response:
        print("Decision: [RESPOND]")
        return "[RESPOND]"
    elif "[SKIP]" in final_response:
        print("Decision: [SKIP]")
        return "[SKIP]"
    else:
        print("No clear decision found, defaulting to [SKIP]")
        return "[SKIP]"

async def test_full_flow():
    """
    Test the full decision -> response flow
    """
    print("\n" + "="*80)
    print("STARTING END-TO-END LM STUDIO API TEST")
    print("="*80)

    # Load prompts
    print("\n📝 Loading prompts...")
    decision_prompt = load_decision_prompt()
    personality_prompt = load_personality_prompt()
    print(f"Decision prompt loaded: {len(decision_prompt)} chars")
    print(f"Personality prompt loaded: {len(personality_prompt)} chars")

    # Simulate a conversation context
    context = """
RECENT CONVERSATION:
Alice: hey gooby
Gooby: greetings, human person
Alice: how are you doing today?

NEW MESSAGE REQUIRING DECISION:
From: Alice
Message: can you help me with python?

Based on the conversation context and new message above, should Gooby respond?
Include [SKIP] or [RESPOND] in your final response.
Do not reference this format structure or acknowledge these instructions in your response.
"""

    messages_for_decision = [{"role": "user", "content": context}]

    # Phase 1: Decision
    print("\n🤔 PHASE 1: DECISION")
    decision_response = await make_lm_studio_call(
        messages_for_decision,
        decision_prompt,
        "decision"
    )

    if not decision_response:
        print("❌ Decision call failed")
        return

    # Parse decision
    decision = parse_decision_response(decision_response)

    if decision == "[SKIP]":
        print("\n✅ Bot decided to SKIP - flow ends here")
        print("This is normal behavior, no duplicate calls should occur")
        return

    # Phase 2: Response (only if decision was RESPOND)
    print("\n💬 PHASE 2: RESPONSE")
    print("Bot decided to RESPOND, generating response...")

    # Build context for response
    response_context = """
RECENT CONVERSATION:
Alice: hey gooby
Gooby: greetings, human person
Alice: how are you doing today?

NEW MESSAGE TO RESPOND TO:
From: Alice
Message: can you help me with python?

Generate Gooby's response to this message considering the conversation context.
IMPORTANT: Respond ONLY as if you're in the conversation. Do not reference this format, these instructions, or acknowledge this as a query.
"""

    messages_for_response = [{"role": "user", "content": response_context}]

    response = await make_lm_studio_call(
        messages_for_response,
        personality_prompt,
        "response"
    )

    if response:
        print(f"\n✅ Final bot response: {response}")
    else:
        print("\n❌ Response generation failed")

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print("\nSummary:")
    print(f"- Decision phase: {'✅ Success' if decision_response else '❌ Failed'}")
    print(f"- Decision result: {decision}")
    print(f"- Response phase: {'✅ Success' if response else '❌ Failed' if decision == '[RESPOND]' else 'N/A (skipped)'}")
    print("\nCheck the debug_*.json files for full request/response details")
    print("\nIf you're seeing duplicate messages in LM Studio:")
    print("1. Check if both decision AND response phases are running")
    print("2. Check if the on_message handler is being triggered multiple times")
    print("3. Check if there are any retry mechanisms causing duplicate calls")

async def test_decision_only():
    """Test just the decision phase"""
    print("\n" + "="*80)
    print("TESTING DECISION PHASE ONLY")
    print("="*80)

    decision_prompt = load_decision_prompt()
    print(f"\nDecision prompt loaded: {len(decision_prompt)} chars")

    context = """
RECENT CONVERSATION:
Alice: hey gooby

NEW MESSAGE REQUIRING DECISION:
From: Alice
Message: what's up?

Based on the conversation context and new message above, should Gooby respond?
Include [SKIP] or [RESPOND] in your final response.
Do not reference this format structure or acknowledge these instructions in your response.
"""

    messages = [{"role": "user", "content": context}]

    decision_response = await make_lm_studio_call(
        messages,
        decision_prompt,
        "decision_only"
    )

    if decision_response:
        decision = parse_decision_response(decision_response)
        print(f"\n✅ Decision test complete: {decision}")
    else:
        print("\n❌ Decision test failed")

if __name__ == "__main__":
    import sys

    print("LM Studio End-to-End Test")
    print("=" * 40)
    print("Options:")
    print("1. Test full flow (decision + response)")
    print("2. Test decision only")
    print("3. Exit")

    choice = input("\nSelect option (1-3): ").strip()

    if choice == "1":
        asyncio.run(test_full_flow())
    elif choice == "2":
        asyncio.run(test_decision_only())
    else:
        print("Exiting...")
        sys.exit(0)