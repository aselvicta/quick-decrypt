from django.shortcuts import render
import nltk
from nltk.corpus import words
import enchant
import math

# Using NLTK words 
nltk.download('words')
english_words = set(words.words())
dictionary = enchant.Dict("en_US")

# English letter frequencies (approximate, as percentages)
ENGLISH_FREQ = {
    'a': 8.167, 'b': 1.492, 'c': 2.782, 'd': 4.253, 'e': 12.702,
    'f': 2.228, 'g': 2.015, 'h': 6.094, 'i': 6.966, 'j': 0.153,
    'k': 0.772, 'l': 4.025, 'm': 2.406, 'n': 6.749, 'o': 7.507,
    'p': 1.929, 'q': 0.095, 'r': 5.987, 's': 6.327, 't': 9.056,
    'u': 2.758, 'v': 0.978, 'w': 2.360, 'x': 0.150, 'y': 1.974,
    'z': 0.074
}

def score_english(text):
    if not text or not any(c.isalpha() for c in text):
        return 0
    
    score = 0
    word = text.lower().replace(" ", "")  # Remove spaces for analysis

    # Dictionary-based scoring
    if dictionary.check(word):
        score += 20  # Higher boost for valid full word
    for i in range(len(word)):
        for length in range(3, min(7, len(word) - i + 1)):
            chunk = word[i:i+length]
            if dictionary.check(chunk):
                score += 2  # Boost for valid substrings

    # Letter frequency analysis
    letter_counts = {}
    total_letters = 0
    for char in word:
        if char.isalpha():
            letter_counts[char] = letter_counts.get(char, 0) + 1
            total_letters += 1
    
    if total_letters == 0:
        return score

    # Calculate chi-squared statistic to compare with English frequencies
    chi_square = 0
    for char in 'abcdefghijklmnopqrstuvwxyz':
        observed = letter_counts.get(char, 0)
        expected = ENGLISH_FREQ[char] * total_letters / 100
        chi_square += (observed - expected) ** 2 / (expected + 0.01)  # Avoid division by zero

    # Lower chi-square means closer to English; convert to a positive score
    freq_score = max(0, 100 - chi_square) * 0.5  # Scale to balance with dictionary score
    score += freq_score

    return score

def caesar_decrypt(text, shift):
    decrypted = ''
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            decrypted += chr((ord(char) - base - shift) % 26 + base)
        else:
            decrypted += char
    return decrypted

def brute_force_caesar(text):
    possibilities = []
    for shift in range(1, 26):
        decrypted = caesar_decrypt(text, shift)
        possibilities.append((shift, decrypted))
    return possibilities

def auto_detect_best(text):
    candidates = brute_force_caesar(text)
    scored = [(shift, result, score_english(result)) for shift, result in candidates]
    
    # Debug output for all shifts
    for shift, result, score in scored:
        print(f"Shift {shift}: {result} (Score: {score})")
    
    # Return the best result based on highest score
    best = max(scored, key=lambda x: x[2], default=(0, "", 0))
    return (best[0], best[1])

def home(request):
    result = ""
    brute_results = []
    best_guess = ("", "")
    if request.method == "POST":
        text = request.POST.get("ciphertext", "")
        shift = request.POST.get("shift", "")
        if shift:
            try:
                result = caesar_decrypt(text, int(shift))
            except ValueError:
                result = "Invalid shift value"
        else:
            brute_results = brute_force_caesar(text)
            best_guess = auto_detect_best(text)
    return render(request, 'home.html', {
        "result": result,
        "brute_results": brute_results,
        "best_guess": best_guess
    })