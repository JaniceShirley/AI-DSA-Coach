"""
Technical Speech & Transcript Normalizer for Coding Interviews.
Preserves candidate's technical claims, mistakes, or correctness while
cleaning acoustic speech-to-text errors and phonetic homophones.
"""

import re

def normalize_dsa_transcript(raw_text: str) -> str:
    """
    Cleans acoustic speech-to-text misrecognitions for DSA interview dialogue.
    Preserves candidate's actual conceptual intention, claims, or errors without rewriting.
    """
    if not raw_text:
        return ""

    text = raw_text.strip()

    # 1. Common acoustic misrecognitions for "brute force"
    text = re.sub(
        r'\b(?:root|route|brew|fruit|brood|rude)\s*(?:force|froze|frost)\b',
        'brute force',
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(r'\bbrut\s+force\b', 'brute force', text, flags=re.IGNORECASE)

    # 2. Misrecognitions for "iterate" / "iteration"
    text = re.sub(
        r'\bhydrate(?:\s+through|\s+from|\s+over|\s+across|\s+the)?\b',
        'iterate through',
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(r'\bhydrate\b', 'iterate', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(?:eye\s*iterate|eye\s*rate)\b', 'iterate', text, flags=re.IGNORECASE)
    text = re.sub(r'\brate\s+through\s+the\s+array\b', 'iterate through the array', text, flags=re.IGNORECASE)

    # 3. Two Pointers terminology
    text = re.sub(r'\b(?:to|too)\s+pointers?\b', 'two pointers', text, flags=re.IGNORECASE)
    text = re.sub(r'\btwo\s+pointer\b', 'two pointers', text, flags=re.IGNORECASE)
    text = re.sub(r'\btwo\s+point\b', 'two pointers', text, flags=re.IGNORECASE)

    # 4. Hash Map / Hash Table terminology
    text = re.sub(r'\b(?:cash|hush)\s*maps?\b', 'hash map', text, flags=re.IGNORECASE)
    text = re.sub(r'\bhashmap\b', 'hash map', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(?:cash|hush)\s*tables?\b', 'hash table', text, flags=re.IGNORECASE)
    text = re.sub(r'\bhashtable\b', 'hash table', text, flags=re.IGNORECASE)
    text = re.sub(r'\bhash\s*sets?\b', 'hash set', text, flags=re.IGNORECASE)
    text = re.sub(r'\bhashset\b', 'hash set', text, flags=re.IGNORECASE)

    # 5. Complement in arithmetic/sum context
    text = re.sub(r'\bcompliments?\b', 'complement', text, flags=re.IGNORECASE)

    # 6. Time and Space Complexity notation
    # O(n^2) / O(n squared)
    text = re.sub(r'\b(?:big\s*)?(?:oh|o|order)\s+of\s+n\s*(?:squared|square|\^2|2)\b', 'O(n²)', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(?:big\s*)?o\s*\(\s*n\s*(?:squared|square|\^2|2)\s*\)', 'O(n²)', text, flags=re.IGNORECASE)
    text = re.sub(r'\boh\s*of\s*n\s*square\b', 'O(n²)', text, flags=re.IGNORECASE)
    text = re.sub(r'\boh\s*of\s*n\s*squared\b', 'O(n²)', text, flags=re.IGNORECASE)

    # O(n log n)
    text = re.sub(r'\b(?:big\s*)?(?:oh|o|order)\s+of\s+n\s*log\s*n\b', 'O(n log n)', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(?:big\s*)?o\s*\(\s*n\s*log\s*n\s*\)', 'O(n log n)', text, flags=re.IGNORECASE)

    # O(log n)
    text = re.sub(r'\b(?:big\s*)?(?:oh|o|order)\s+of\s+log\s*n\b', 'O(log n)', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(?:big\s*)?o\s*\(\s*log\s*n\s*\)', 'O(log n)', text, flags=re.IGNORECASE)

    # O(n)
    text = re.sub(r'\b(?:big\s*)?(?:oh|o|order)\s+of\s+n\b', 'O(n)', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(?:big\s*)?o\s*\(\s*n\s*\)', 'O(n)', text, flags=re.IGNORECASE)

    # O(1)
    text = re.sub(r'\b(?:big\s*)?(?:oh|o|order)\s+of\s+(?:one|1)\b', 'O(1)', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(?:big\s*)?o\s*\(\s*1\s*\)', 'O(1)', text, flags=re.IGNORECASE)

    # Complexity terms
    text = re.sub(r'\btime\s+complexly\b', 'time complexity', text, flags=re.IGNORECASE)
    text = re.sub(r'\bspace\s+complexly\b', 'space complexity', text, flags=re.IGNORECASE)
    text = re.sub(r'\bauxiliary\s+space\b', 'auxiliary space', text, flags=re.IGNORECASE)

    # 7. Other common DSA acoustic errors
    text = re.sub(r'\bbinary\s+surge\b', 'binary search', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(?:link|lynx)\s+list\b', 'linked list', text, flags=re.IGNORECASE)
    text = re.sub(r'\bcall\s+stuck\b', 'call stack', text, flags=re.IGNORECASE)
    text = re.sub(r'\bkey\s*values?\b', 'key-value', text, flags=re.IGNORECASE)

    # 8. Clean conversational stutter / verbal pause fillers at sentence starts without altering candidate content
    text = re.sub(r'^(?:you know what|um|uh|like um|so basically I think|you know|so yeah)\s*,?\s*', '', text, flags=re.IGNORECASE)

    # Clean double spaces
    text = re.sub(r'\s{2,}', ' ', text).strip()

    return text
