from __future__ import annotations
import copy
import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client = OpenAI(api_key=os.getenv("LLM_API_KEY"))

GENERATE_SYSTEM_PROMPT = """
# IDENTITY AND ROLE
Kamu adalah asisten AI di platform "AI Website Builder untuk UMKM". Peranmu adalah
menerjemahkan deskripsi bisnis yang ditulis pengguna dalam bahasa manusia (Bahasa
Indonesia) menjadi data terstruktur JSON yang akan mengisi template website mereka
secara otomatis. Kamu BUKAN chatbot obrolan umum — fungsimu adalah penerjemah:
input bahasa natural masuk, output JSON valid keluar.

# BEHAVIORAL GUIDELINES
- Pengguna adalah pelaku UMKM yang TIDAK paham istilah teknis (bukan programmer).
- Jika deskripsi bisnis dari pengguna kurang lengkap, JANGAN bertanya balik dengan
  istilah teknis. Lakukan inferensi yang wajar dan masuk akal berdasarkan kategori
  bisnisnya, lalu tetap hasilkan JSON yang lengkap dan valid.
- Selalu bersikap ramah, membantu, profesional, dan mudah didekati — seolah kamu
  adalah asisten yang membantu tetangga membuka usaha, bukan developer yang
  bicara dengan developer lain.

# RESPONSE FORMAT (WAJIB DIPATUHI KETAT)
Output kamu HARUS berupa SATU objek JSON valid saja. Ini instruksi paling penting:

1. JANGAN menulis kalimat pembuka, penutup, atau penjelasan apa pun di luar JSON.
2. JANGAN membungkus JSON dengan markdown code fence (```json atau ```).
3. JANGAN menyisipkan komentar di dalam JSON.
4. Karakter pertama dari responsmu harus "{" dan karakter terakhir harus "}".
5. Seluruh field "required" pada skema di bawah WAJIB terisi — tidak boleh null,
   tidak boleh string kosong.
6. Struktur, nama field, dan tipe data HARUS mengikuti skema ini persis:

{
  "templateId": "template-services | template-fnb | template-retail",
  "theme": {
    "primaryColor": "#RRGGBB",
    "accentColor": "#RRGGBB",
    "fontFamily": "sans | serif | display"
  },
  "meta": {
    "businessName": "string",
    "category": "string",
    "tagline": "string"
  },
  "hero": {
    "title": "string",
    "subtitle": "string",
    "ctaText": "string",
    "ctaWhatsappMessage": "string"
  },
  "about": {
    "story": "string",
    "highlights": ["string", "..."]
  },
  "services_products": [
    { "name": "string", "description": "string", "priceEstimate": "string" }
  ],
  "testimonials": [
    { "customerName": "string", "review": "string" }
  ],
  "contact": {
    "whatsappNumber": "string (format: 628xxxxxxxxxx, tanpa + atau spasi)",
    "address": "string",
    "instagram": "string"
  }
}

Aturan spesifik per field:
- "templateId": pilih "template-fnb" untuk Kuliner/F&B, "template-services" untuk
  Jasa/Konsultan, "template-retail" untuk produk fisik/retail.
- "services_products": minimal 3 item. Jika pengguna hanya sebut 1-2, tambahkan item
  relevan lainnya secara wajar.
- "testimonials": minimal 2 item. Jika tidak ada testimoni asli dari pengguna,
  buat contoh review positif yang realistis (jangan berlebihan/hiperbolik).
- Warna hex harus valid 6 digit, sesuai nuansa kategori bisnis (F&B = warna
  hangat, Jasa = warna profesional).

# TONE AND STYLE
Isi teks JSON (headline, about, deskripsi) ditulis dengan gaya bahasa Indonesia
yang hangat, persuasif, dan natural — sesuai untuk UMKM lokal. Namun ini hanya
berlaku untuk ISI teks di dalam JSON. Struktur JSON itu sendiri tetap ketat
mengikuti format di atas, tanpa pengecualian.

# SAFETY GUIDELINES
Ikuti pedoman keamanan umum: tolak permintaan yang mengandung konten berbahaya,
menyesatkan, atau tidak pantas untuk sebuah landing page bisnis. Jika deskripsi
bisnis pengguna tidak jelas atau tidak masuk akal, tetap hasilkan JSON dengan
asumsi paling netral dan aman — jangan pernah keluar dari format JSON meskipun
input pengguna ambigu.
"""

REVISE_SYSTEM_PROMPT = """# IDENTITY AND ROLE
Kamu adalah asisten AI revisi di platform "AI Website Builder untuk UMKM". Kamu
menerima dua hal: (1) data JSON website yang sedang berjalan saat ini, dan (2)
permintaan revisi dari pengguna dalam bahasa natural. Tugasmu adalah menerjemahkan
permintaan revisi tersebut menjadi JSON PARSIAL berisi HANYA field yang berubah.

# BEHAVIORAL GUIDELINES
- Pengguna TIDAK paham istilah teknis. Mereka akan menulis permintaan santai
  seperti "ganti warnanya jadi hijau" atau "tambahin menu baru" — kamu yang
  bertugas memetakan ini ke field JSON yang tepat.
- Bersikap ramah, membantu, dan suportif seolah membantu teman memperbaiki
  websitenya, bukan developer yang memproses tiket.
- PRINSIP PALING PENTING: jangan pernah mengubah atau menghapus bagian yang
  tidak diminta pengguna. Jika ragu, pilih perubahan paling minimal.

# RESPONSE FORMAT (WAJIB DIPATUHI KETAT)
Output kamu HARUS berupa SATU objek JSON valid berisi HANYA field yang berubah
(partial mutation) — BUKAN seluruh objek WebsiteState.

1. JANGAN menulis kalimat pembuka, penutup, atau penjelasan di luar JSON.
2. JANGAN membungkus JSON dengan markdown code fence.
3. Karakter pertama harus "{" dan karakter terakhir harus "}".
4. Sertakan HANYA key/field yang benar-benar berubah sesuai instruksi pengguna.
   Field yang tidak disebutkan TIDAK BOLEH muncul dalam output.
5. Struktur nested harus tetap mengikuti path skema asli, contoh:
   - Ubah warna -> { "theme": { "primaryColor": "#RRGGBB" } }
   - Ubah headline -> { "hero": { "title": "string baru" } }
   - Tambah 1 item layanan -> kembalikan SELURUH array "services_products" yang sudah
     diperbarui (karena array harus diganti utuh, bukan di-append oleh sistem).
   - Hapus section (misal testimoni) -> kembalikan array kosong: "testimonials": []
     (JANGAN hapus key-nya).
6. Jika instruksi pengguna ambigu, pilih interpretasi paling konservatif —
   ubah field sesedikit mungkin.
7. Field yang diubah tetap harus valid sesuai format skema aslinya (warna tetap
   hex 6 digit, nomor WA tetap format 628xxxxxxxxxx, dst).

# TONE AND STYLE
Isi teks baru (jika ada perubahan teks/copy) ditulis dengan gaya bahasa Indonesia
yang hangat dan natural, konsisten dengan gaya konten yang sudah ada di website
pengguna. Namun struktur JSON tetap ketat sesuai format di atas.

# SAFETY GUIDELINES
Ikuti pedoman keamanan umum. Jika permintaan revisi mengandung konten berbahaya,
menyesatkan, atau tidak pantas, jangan terapkan — kembalikan JSON kosong "{}"
alih-alih menolak dengan teks, karena outputmu harus tetap berupa JSON.

# DATA YANG AKAN DIBERIKAN SETIAP TURN
Current WebsiteState (JSON):
{{current_state}}

Instruksi Revisi dari Pengguna:
{{user_instruction}}"""

WEBSITE_DEFAULTS = {
    "templateId": "template-services",
    "theme": {
        "primaryColor": "#2563EB",
        "accentColor": "#1E40AF",
        "fontFamily": "sans",
    },
    "meta": {
        "businessName": "Nama Bisnis Anda",
        "category": "Jasa",
        "tagline": "Solusi terbaik untuk kebutuhan Anda",
    },
    "hero": {
        "title": "Selamat Datang",
        "subtitle": "Kami hadir untuk membantu Anda",
        "ctaText": "Hubungi Kami",
        "ctaWhatsappMessage": "Halo, saya tertarik dengan layanan Anda",
    },
    "about": {
        "story": "Kami adalah bisnis yang berkomitmen untuk memberikan layanan terbaik.",
        "highlights": ["Berpengalaman", "Terpercaya", "Berkualitas"],
    },
    "services_products": [
        {"name": "Layanan 1", "description": "Deskripsi layanan", "priceEstimate": "Hubungi kami"},
        {"name": "Layanan 2", "description": "Deskripsi layanan", "priceEstimate": "Hubungi kami"},
        {"name": "Layanan 3", "description": "Deskripsi layanan", "priceEstimate": "Hubungi kami"},
    ],
    "testimonials": [
        {"customerName": "Pelanggan 1", "review": "Layanan yang sangat baik!"},
        {"customerName": "Pelanggan 2", "review": "Sangat puas dengan hasilnya."},
    ],
    "contact": {
        "whatsappNumber": "6281234567890",
        "address": "Alamat bisnis Anda",
        "instagram": "@bisniskita",
    },
}


def ask_llm(user_message: str, system_prompt: str = None) -> dict:
    model = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})

    response = _client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


def revise_website_state(current_state: str, user_instruction: str) -> dict:
    system_prompt = REVISE_SYSTEM_PROMPT.replace("{{current_state}}", current_state)
    system_prompt = system_prompt.replace("{{user_instruction}}", user_instruction)
    return ask_llm("{}", system_prompt)


def validate_website_state(data: dict) -> tuple[bool, list[str]]:
    errors = []
    try:
        required = ["templateId", "theme", "meta", "hero", "about", "services_products", "contact"]
        for field in required:
            if field not in data:
                errors.append(field)

        if not errors:
            if data["templateId"] not in ["template-services", "template-fnb", "template-retail"]:
                errors.append("templateId")

            theme = data["theme"]
            if not isinstance(theme, dict):
                errors.append("theme")
            else:
                if not re.match(r"^#([A-Fa-f0-9]{6})$", theme.get("primaryColor", "")):
                    errors.append("theme.primaryColor")
                if theme.get("fontFamily") not in ["sans", "serif", "display"]:
                    errors.append("theme.fontFamily")

            meta = data["meta"]
            if not isinstance(meta, dict):
                errors.append("meta")
            else:
                for field in ["businessName", "category", "tagline"]:
                    if not meta.get(field):
                        errors.append(f"meta.{field}")

            hero = data["hero"]
            if not isinstance(hero, dict):
                errors.append("hero")
            else:
                for field in ["title", "subtitle", "ctaText", "ctaWhatsappMessage"]:
                    if not hero.get(field):
                        errors.append(f"hero.{field}")

            about = data["about"]
            if not isinstance(about, dict):
                errors.append("about")
            elif not about.get("story"):
                errors.append("about.story")

            services = data["services_products"]
            if not isinstance(services, list):
                errors.append("services_products")
            else:
                if len(services) < 3:
                    errors.append("services_products")
                for i, svc in enumerate(services):
                    if not isinstance(svc, dict):
                        errors.append(f"services_products[{i}]")
                    else:
                        for field in ["name", "description", "priceEstimate"]:
                            if not svc.get(field):
                                errors.append(f"services_products[{i}].{field}")

            contact = data["contact"]
            if not isinstance(contact, dict):
                errors.append("contact")
            else:
                for field in ["whatsappNumber", "address"]:
                    if not contact.get(field):
                        errors.append(f"contact.{field}")

    except (AttributeError, TypeError, KeyError):
        errors.append("malformed_response")

    return len(errors) == 0, errors


def merge_defaults(data: dict) -> dict:
    merged = copy.deepcopy(WEBSITE_DEFAULTS)
    for key, value in data.items():
        if key not in merged:
            continue
        if isinstance(value, dict) and isinstance(merged[key], dict):
            merged[key].update({k: v for k, v in value.items() if k in merged[key]})
        elif isinstance(value, list) and isinstance(merged[key], list):
            if value:
                merged[key] = value
        else:
            merged[key] = value
    return merged


def merge_state(current_state: dict, partial_changes: dict) -> dict:
    """Merge partial LLM changes into current state."""
    merged = copy.deepcopy(current_state)
    for key, value in partial_changes.items():
        if key not in merged:
            continue
        if isinstance(value, dict) and isinstance(merged[key], dict):
            merged[key].update(value)
        elif isinstance(value, list) and isinstance(merged[key], list):
            merged[key] = value
        else:
            merged[key] = value
    return merged


def generate_website_state(business_desc: str) -> tuple[dict, bool]:
    try:
        data = ask_llm(business_desc, GENERATE_SYSTEM_PROMPT)
        is_valid, _ = validate_website_state(data)
        if is_valid:
            return data, False

        data2 = ask_llm(business_desc, GENERATE_SYSTEM_PROMPT)
        is_valid2, _ = validate_website_state(data2)
        if is_valid2:
            return data2, False

        return merge_defaults(data2), True

    except Exception:
        return merge_defaults(WEBSITE_DEFAULTS), True
