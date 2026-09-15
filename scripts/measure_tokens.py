import tiktoken

enc = tiktoken.encoding_for_model("gpt-4o")

with open("app/services/llm_service.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find GENERATE_SYSTEM_PROMPT
marker = 'GENERATE_SYSTEM_PROMPT = """'
gen_start = content.find(marker) + len(marker)
gen_end = content.find('"""', gen_start)
gen_prompt = content[gen_start:gen_end]

# Find REVISE_SYSTEM_PROMPT
marker = 'REVISE_SYSTEM_PROMPT = """'
revise_start = content.find(marker) + len(marker)
revise_end = content.find('"""', revise_start)
revise_prompt = content[revise_start:revise_end]

gen_tokens = len(enc.encode(gen_prompt))
revise_tokens = len(enc.encode(revise_prompt))

worst_case_gen = ("Warung Kopi Sejahtera, jual kopi tubruk dan roti bakar di Surabaya, " * 3)[:400]
worst_case_revise = ("Ganti semua warna menjadi cokelat tua klasik, ubah tagline, " * 3)[:300]

gen_input_tokens = len(enc.encode(worst_case_gen))
revise_input_tokens = len(enc.encode(worst_case_revise))

print("=== TOKEN BASELINE REPORT ===")
print(f"GENERATE_SYSTEM_PROMPT:  {gen_tokens} tokens")
print(f"REVISE_SYSTEM_PROMPT:    {revise_tokens} tokens")
print(f"Worst-case gen input:    {gen_input_tokens} tokens")
print(f"Worst-case revise input: {revise_input_tokens} tokens")
print("")
print("=== TOTAL PER REQUEST ===")
print(f"Generate (worst):  {gen_tokens + gen_input_tokens} tokens")
print(f"Revise (worst):    {revise_tokens + revise_input_tokens} tokens")
print("")
print("=== SAVINGS TARGET ===")
print(f"Target GENERATE:   <800 tokens (from {gen_tokens})")
print(f"Target REVISE:     <1200 tokens (from {revise_tokens})")
