#!/usr/bin/env python3
# encoding: utf-8

import sys
from typing import Tuple, List

LOW_A = ord('a')
UP_A = ord('A')

def encrypt_character(ch: str, s1: int, s2: int) -> str:
    # Lowercase
    if 'a' <= ch <= 'z':
        if ch <= 'm':  # a-m: forward by s1*s2
            shift = s1 * s2
            return chr((ord(ch) - LOW_A + shift) % 26 + LOW_A)
        else:  # n-z: backward by (s1 + s2)
            shift = -(s1 + s2)
            return chr((ord(ch) - LOW_A + shift) % 26 + LOW_A)

    # Uppercase
    if 'A' <= ch <= 'Z':
        if ch <= 'M':  # A-M: backward by s1
            shift = -s1
            return chr((ord(ch) - UP_A + shift) % 26 + UP_A)
        else:  # N-Z: forward by s2^2
            shift = (s2 * s2)
            return chr((ord(ch) - UP_A + shift) % 26 + UP_A)

    # Everything else unchanged
    return ch


def decrypt_character_with_ambiguity(ch: str, s1: int, s2: int) -> Tuple[str, bool]:
    """
    Returns (decoded_char, ambiguous_flag).
    If decoding is ambiguous (cannot know which original half it came from),
    returns one of the valid candidates but marks ambiguous_flag=True.
    """
    # Lowercase
    if 'a' <= ch <= 'z':
        idx = ord(ch) - LOW_A
        cand_first = (idx - (s1 * s2)) % 26  # assuming original in a-m
        cand_second = (idx + (s1 + s2)) % 26  # assuming original in n-z
        c1 = chr(cand_first + LOW_A)
        c2 = chr(cand_second + LOW_A)

        ok1 = (c1 <= 'm' and encrypt_character(c1, s1, s2) == ch)
        ok2 = (c2 >= 'n' and encrypt_character(c2, s1, s2) == ch)

        if ok1 and not ok2:
            return c1, False
        if ok2 and not ok1:
            return c2, False
        if ok1 and ok2:
            # True ambiguity: both halves map to ch under the given shifts
            # Return c1 deterministically, but flag ambiguity
            return c1, True
        # If neither matches (shouldn't happen), return ch unchanged but flag
        return ch, True

    # Uppercase
    if 'A' <= ch <= 'Z':
        idx = ord(ch) - UP_A
        cand_first = (idx + s1) % 26      # original in A-M
        cand_second = (idx - (s2 * s2)) % 26  # original in N-Z
        c1 = chr(cand_first + UP_A)
        c2 = chr(cand_second + UP_A)

        ok1 = (c1 <= 'M' and encrypt_character(c1, s1, s2) == ch)
        ok2 = (c2 >= 'N' and encrypt_character(c2, s1, s2) == ch)

        if ok1 and not ok2:
            return c1, False
        if ok2 and not ok1:
            return c2, False
        if ok1 and ok2:
            return c1, True
        return ch, True

    # Everything else unchanged
    return ch, False


def encrypt_file(s1: int, s2: int) -> None:
    with open("raw_text.txt", "r", encoding="utf-8") as infile, \
         open("encrypted_text.txt", "w", encoding="utf-8") as outfile:
        text = infile.read()
        encrypted = ''.join(encrypt_character(ch, s1, s2) for ch in text)
        outfile.write(encrypted)


def decrypt_file(s1: int, s2: int) -> List[int]:
    ambiguous_positions: List[int] = []
    with open("encrypted_text.txt", "r", encoding="utf-8") as infile, \
         open("decrypted_text.txt", "w", encoding="utf-8") as outfile:
        cipher = infile.read()
        out_chars = []
        for i, ch in enumerate(cipher):
            dec, amb = decrypt_character_with_ambiguity(ch, s1, s2)
            out_chars.append(dec)
            if amb and ch.isalpha():
                ambiguous_positions.append(i)
        outfile.write(''.join(out_chars))
    return ambiguous_positions


def verify_files(show_diffs: int = 5) -> bool:
    with open("raw_text.txt", "r", encoding="utf-8") as f1, \
         open("decrypted_text.txt", "r", encoding="utf-8") as f2:
        raw = f1.read()
        dec = f2.read()
        if raw == dec:
            print("✅ Verification successful: Decryption matches the original!")
            return True
        else:
            print("❌ Verification failed: Decryption does not match the original.")
            # Show first few diffs to help debug
            mismatches = []
            for i, (a, b) in enumerate(zip(raw, dec)):
                if a != b:
                    mismatches.append((i, a, b))
                    if len(mismatches) >= show_diffs:
                        break
            if len(raw) != len(dec):
                print(f"   Note: length differs (raw={len(raw)}, decrypted={len(dec)}).")
            if mismatches:
                print("   First differences (pos, raw, decrypted):")
                for pos, a, b in mismatches:
                    ra = repr(a)
                    rb = repr(b)
                    print(f"   - {pos}: {ra} vs {rb}")
            return False


def check_reversibility_for_text(text: str, s1: int, s2: int) -> None:
    """
    Explains whether the mapping is guaranteed to be reversible for the specific text:
    - If text has only lowercase letters, it's reversible iff (s1*s2 + s1 + s2) % 26 == 0
    - If only uppercase letters, reversible iff (s1 + s2*s2) % 26 == 0 (i.e., -s1 ≡ s2^2 mod 26)
    - If mixed case letters are present, with the given rules there is generally NO non-trivial
      pair (s1, s2) that guarantees perfect reversibility for all letters.
    """
    has_lower = any('a' <= ch <= 'z' for ch in text)
    has_upper = any('A' <= ch <= 'Z' for ch in text)

    if has_lower and not has_upper:
        cond = (s1 * s2 + s1 + s2) % 26 == 0
        print(f"Lowercase-only text detected. Reversibility condition: (s1*s2 + s1 + s2) % 26 == 0")
        print(f"Your shifts: s1={s1}, s2={s2} -> Condition holds? {cond}")
    elif has_upper and not has_lower:
        cond = (s1 + (s2 * s2)) % 26 == 0
        print(f"Uppercase-only text detected. Reversibility condition: (s1 + s2^2) % 26 == 0")
        print(f"Your shifts: s1={s1}, s2={s2} -> Condition holds? {cond}")
    elif has_lower and has_upper:
        print("Mixed-case text detected.")
        print("⚠ With the given rules, there is no non-trivial (s1, s2) that guarantees a perfect inverse for BOTH cases simultaneously.")
        print("   You may still decrypt most characters, but some will be ambiguous depending on values and letters used.")
        print("   To guarantee perfect reversibility you could either:")
        print("   - Use s1 = 0 and s2 = 0 (no-op), OR")
        print("   - Restrict your text to only lowercase or only uppercase letters and choose shifts that satisfy the respective condition.")
    else:
        print("No letters found in the text; nothing to encrypt/decrypt.")


def main():
    try:
        s1 = int(input("Enter shift1 value: "))
        s2 = int(input("Enter shift2 value: "))
    except ValueError:
        print("Please enter integer values for shift1 and shift2.")
        sys.exit(1)

    # Step 0: Optional heads-up about reversibility on this specific text
    with open("raw_text.txt", "r", encoding="utf-8") as f:
        sample = f.read()
    check_reversibility_for_text(sample, s1, s2)

    # Step 1: Encrypt
    encrypt_file(s1, s2)
    print("Encryption completed. Output saved to encrypted_text.txt")

    # Step 2: Decrypt
    ambiguous_positions = decrypt_file(s1, s2)
    print("Decryption completed. Output saved to decrypted_text.txt")
    if ambiguous_positions:
        # Show just a few positions to avoid noise
        preview = ', '.join(map(str, ambiguous_positions[:10]))
        more = "" if len(ambiguous_positions) <= 10 else f" (and {len(ambiguous_positions)-10} more)"
        print(f"ℹ Ambiguity detected at positions: {preview}{more}")
        print("   This happens when both halves map different letters to the same encrypted letter under your shifts.")

    # Step 3: Verify
    verify_files()

if __name__ == "__main__":
    main()