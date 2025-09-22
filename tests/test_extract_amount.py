#!/usr/bin/env python3
"""
Test script for extract_amount method
"""

import sys
import os
# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from typing import Optional

# Copy the extract_amount method for isolated testing
def extract_amount(text: str) -> Optional[float]:
    """Extract monetary amount from user input"""
    text = text.lower().replace(",", "").replace("$", "")
    
    # Handle written numbers
    number_words = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
        "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
        "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
        "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000, "million": 1000000
    }
    
    # Look for direct numbers first
    amount_patterns = [
        r'(\d+(?:\.\d{2})?)\s*(?:thousand|k)',  # 50 thousand, 50k
        r'(\d+(?:\.\d{2})?)\s*(?:million|m)',   # 1 million, 1m
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)',        # 50,000 or 50000
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, text)
        if match:
            amount = float(match.group(1).replace(",", ""))
            if "thousand" in text or "k" in text:
                amount *= 1000
            elif "million" in text or "m" in text:
                amount *= 1000000
            return amount
    
    # Handle written amounts like "fifty thousand"
    words = text.split()
    total = 0
    current = 0
    
    for word in words:
        if word in number_words:
            value = number_words[word]
            if value == 100:
                # If current is 0, treat "hundred" as 100
                if current == 0:
                    current = 100
                else:
                    current *= 100  # "fifty hundred" = 50 * 100 = 5000
            elif value == 1000:
                # Add accumulated value * 1000 to total
                if current == 0:
                    current = 1  # Handle standalone "thousand"
                total += current * 1000
                current = 0
            elif value == 1000000:
                # Add accumulated value * 1000000 to total
                if current == 0:
                    current = 1  # Handle standalone "million"
                total += current * 1000000
                current = 0
            else:
                current += value
    
    total += current
    return total if total > 0 else None

def test_extract_amount():
    """Test the extract_amount method with various inputs"""
    
    # Test cases: (input, expected_output)
    test_cases = [
        # Numeric formats
        ("50000", 50000),
        ("50,000", 50000),
        ("$50,000", 50000),
        ("50000.00", 50000),
        
        # Thousand formats
        ("50 thousand", 50000),
        ("50k", 50000),
        ("50K", 50000),
        ("fifty thousand", 50000),
        
        # Million formats
        ("1 million", 1000000),
        ("1m", 1000000),
        ("1M", 1000000),
        ("one million", 1000000),
        
        # Complex written numbers
        ("twenty five thousand", 25000),
        ("two hundred thousand", 200000),
        ("one hundred", 100),
        ("fifty", 50),
        ("hundred", 100),
        ("thousand", 1000),
        
        # Edge cases
        ("zero", 0),
        ("nothing", None),
        ("I don't have any", None),
        ("", None),
        
        # Sentences with amounts
        ("I need about fifty thousand dollars", 50000),
        ("Around 25k would be good", 25000),
        ("Maybe two hundred and fifty thousand", 250000),
        ("I'm looking for one hundred thousand", 100000),
        
        # Tricky cases
        ("fifty hundred", 5000),  # 50 * 100
        ("ten thousand five hundred", 10500),  # This might be tricky
    ]
    
    print("Testing extract_amount method:")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for i, (input_text, expected) in enumerate(test_cases, 1):
        try:
            result = extract_amount(input_text)
            
            if result == expected:
                status = "✅ PASS"
                passed += 1
            else:
                status = "❌ FAIL"
                failed += 1
                
            print(f"{i:2d}. Input: '{input_text}'")
            print(f"    Expected: {expected}")
            print(f"    Got:      {result}")
            print(f"    Status:   {status}")
            print()
            
        except Exception as e:
            print(f"{i:2d}. Input: '{input_text}'")
            print(f"    ERROR: {str(e)}")
            print(f"    Status: ❌ ERROR")
            print()
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print(f"Success rate: {passed/(passed+failed)*100:.1f}%")
    
    return passed, failed

if __name__ == "__main__":
    test_extract_amount()