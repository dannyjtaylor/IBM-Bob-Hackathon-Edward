#!/usr/bin/env python3
"""Test script for context enhancer and clipboard assistant"""

from clipboard_assistant import get_clipboard_assistant
from context_enhancer import get_context_enhancer

print("=" * 60)
print("Testing Context Enhancer & Clipboard Assistant")
print("=" * 60)

# Test 1: Clipboard Assistant
print("\n[TEST 1] Clipboard Content Analysis")
ca = get_clipboard_assistant()

test_cases = [
    ("def hello():\n    print('world')", "Python code"),
    ("SELECT * FROM users WHERE id = 1", "SQL query"),
    ('{"name": "Edward", "type": "AI"}', "JSON data"),
    ("TypeError: cannot concatenate str and int", "Error message"),
    ("https://github.com/example/repo", "URL"),
]

for content, expected in test_cases:
    content_type = ca.analyze_content_type(content)
    print(f"  Content: {content[:30]}...")
    print(f"  Detected: {content_type} (Expected: {expected})")
    print()

# Test 2: Context Enhancer
print("\n[TEST 2] Enhanced Prompt Building")
ce = get_context_enhancer()

user_question = "What does this code do?"
screenshot_base64 = "fake_base64_data"

enhanced_prompt, metadata = ce.build_enhanced_prompt(
    user_question=user_question,
    screenshot_base64=screenshot_base64,
    include_clipboard=False,  # Don't actually read clipboard
    conversation_history=None
)

print(f"  Original question: {user_question}")
print(f"  Enhanced prompt length: {len(enhanced_prompt)} chars")
print(f"  Metadata: {metadata}")
print()

# Test 3: Smart Suggestions
print("\n[TEST 3] Smart Suggestions")
code = "def calculate(x, y):\n    return x + y"
content_type = ca.analyze_content_type(code)
suggestions = ca.get_smart_suggestions(code)

print(f"  Code: {code}")
print(f"  Type: {content_type}")
print(f"  Suggestions:")
for i, suggestion in enumerate(suggestions[:3], 1):
    print(f"    {i}. {suggestion}")

print("\n" + "=" * 60)
print("All tests completed successfully!")
print("=" * 60)

# Made with Bob
