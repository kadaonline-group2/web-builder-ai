#!/usr/bin/env python3
"""Measure current token usage for optimization baseline."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tiktoken
from app.services.llm_service import GENERATE_SYSTEM_PROMPT, REVISE_SYSTEM_PROMPT

enc = tiktoken.encoding_for_model("gpt-4o")

# Measure prompts
gen_tokens = len(enc.encode(GENERATE_SYSTEM_PROMPT))
revise_tokens = len(enc.encode(REVISE_SYSTEM_PROMPT))

# Measure worst-case user inputs
worst_case_gen = "Warung Kopi Sejahtera, jual kopi tubruk dan roti bakar di Surabaya, target anak muda nugas, wa 08123456789, buka jam 8 pagi sampai 10 malam, ada wifi gratis, tempatnya cozy banget buat nugas" * 2  # ~400 chars
worst_case_revise = "Ganti semua warna menjadi cokelat tua klasik, ubah tagline jadi lebih formal, tambahkan 2 produk baru: Es Kopi Susu Rp18.000 dan Roti Cokelat Rp15.000" * 2  # ~300 chars

gen_input_tokens = len(enc.encode(worst_case_gen))
revise_input_tokens = len(enc.encode(worst_case_revise))

print(f"=== TOKEN BASELINE REPORT ===")
print(f"GENERATE_SYSTEM_PROMPT:  {gen_tokens} tokens")
print(f"REVISE_SYSTEM_PROMPT:    {revise_tokens} tokens")
print(f"Worst-case gen input:    {gen_input_tokens} tokens")
print(f"Worst-case revise input: {revise_input_tokens} tokens")
print(f"")
print(f"=== TOTAL PER REQUEST ===")
print(f"Generate (worst):  {gen_tokens + gen_input_tokens} tokens")
print(f"Revise (worst):    {revise_tokens + revise_input_tokens} tokens")
print(f"")
print(f"=== SAVINGS TARGET ===")
print(f"Target GENERATE:   <800 tokens (from {gen_tokens})")
print(f"Target REVISE:     <1200 tokens (from {revise_tokens})")
