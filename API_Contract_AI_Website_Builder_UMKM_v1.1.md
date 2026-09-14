# API Contract — AI Website Builder untuk UMKM

**Versi Dokumen:** 1.1 (Final — konsolidasi keputusan tim dari draft v0.2 dan v1.0)
**Status:** Siap Diimplementasikan
**Referensi:** FRD v1.2, Scrum Project Plan v1.2 (3 Developer: 2 Backend+AI + 1 Frontend), `website-state.schema.json`

## Catatan Konsolidasi

Dokumen ini adalah hasil akhir setelah membandingkan draft v0.2 dan v1.0, per item:

| # | Topik | Sumber Keputusan | Keputusan Final |
|---|---|---|---|
| 1 | Nama field array produk/layanan | v1.0 | `services` |
| 2 | Mekanisme export | v0.2 | Server-side |
| 3 | Fitur Publish | v1.0 | Stretch / Could-Have, bukan komitmen MVP |
| 4 | Tech stack | v1.0 | Node.js + Express + TypeScript (orkestrasi) + Python/FastAPI (AI generation) |
| 5 | Normalisasi nomor WhatsApp | v1.0 | Normalisasi ke `62...`, URL dibuat aplikasi |
| 6 | `iconKeyword` | — | Field opsional, tag ikon per item service |
| 7 | Error handling | v1.0 | Full error envelope + tabel status/kode |
| 8 | Metadata response Revise | — | Tambahan tim (`revisionApplied`, `changedPaths`, `fallbackReason`), bukan mandat FRD |
| 9 | Health check | v1.0 | `GET /api/v1/health` |
| 10 | Sumber kebenaran schema | v1.0 | File eksternal `website-state.schema.json` |

---

## 1. Tujuan dan Ruang Lingkup

Dokumen ini menjadi kesepakatan teknis antara repository frontend dan backend untuk proyek AI Website Builder untuk UMKM.

Arsitektur backend bersifat hybrid:

- **Orkestrasi utama (routing, validasi, revision merge, export, error handling):** Node.js + Express + TypeScript, dimiliki Dev 2.
- **AI Generation Service (system prompt, pemanggilan LLM, parsing/validasi output LLM, retry/fallback):** Python + FastAPI, dimiliki Dev 1 (`llm_service.py`). Service ini dipanggil oleh layer orkestrasi Node/Express sebagai service terpisah — bukan bagian dari proses Node yang sama.

Frontend menggunakan React, Vite, dan TypeScript. LLM hanya boleh menghasilkan data terstruktur. HTML website selalu dibuat oleh template renderer yang dikendalikan aplikasi, bukan oleh LLM.

Kontrak ini mencakup:

- pembuatan draft pertama website;
- revisi website melalui instruksi chat;
- validasi `WebsiteState`;
- format response dan error;
- export website;
- health check backend.

Publish online tetap menjadi stretch goal (Could-Have per Scrum Plan/FR-07) dan tidak menjadi dependency fitur utama maupun bagian dari kontrak MVP yang wajib diimplementasikan.

## 2. Keputusan Teknis yang Mengikat

| Topik | Keputusan |
|---|---|
| Base path API | `/api/v1` |
| Sumber kebenaran data | `website-state.schema.json` (file eksternal) |
| Nama array produk atau layanan | `services` |
| Warna kedua | `accentColor` (wajib) |
| Penyimpanan state | Stateless; frontend mengirim `currentState` penuh saat revisi |
| Response revisi | Full merged `WebsiteState`, bukan partial diff |
| Fallback generation | Retry satu kali, lalu gunakan fallback state yang valid |
| Export MVP | **Server-side** — backend membangun bundle ZIP/HTML dari `WebsiteState` menggunakan rendering engine yang sama dengan preview |
| Publish online | Stretch goal (Could-Have); tidak termasuk kontrak MVP yang wajib |
| Autentikasi dan database | Tidak digunakan pada MVP |
| Backend orkestrasi | Node.js + Express + TypeScript |
| Backend AI generation | Python + FastAPI, dipanggil sebagai service terpisah oleh layer orkestrasi |

## 3. Base URL dan Konvensi Umum

Base URL lokal:

```text
http://localhost:3000/api/v1
```

Base URL frontend disimpan dalam environment variable:

```env
VITE_API_BASE_URL=http://localhost:3000/api/v1
```

Semua request JSON wajib menggunakan header:

```http
Content-Type: application/json
Accept: application/json
```

Backend wajib mengizinkan origin frontend melalui CORS. API key LLM hanya disimpan pada environment AI Generation Service (Python/FastAPI) dan tidak boleh dikirim ke frontend maupun disimpan di layer Node/Express.

## 4. Model Data WebsiteState

`WebsiteState` adalah bentuk data utama yang dipertukarkan oleh endpoint generate dan revise, serta digunakan oleh template renderer frontend.

Schema resmi disimpan pada file terpisah dan menjadi satu-satunya sumber kebenaran:

```text
website-state.schema.json
```

Keputusan penting:

- Field resmi adalah **`services`**, bukan `services_products`. FR-03 (narasi requirement) perlu diselaraskan ke penamaan ini — lihat Bagian 12.
- `testimonials` wajib berisi minimal dua item (`minItems: 2`, ditegakkan schema).
- `services` wajib berisi minimal tiga item (`minItems: 3`).
- `accentColor` wajib tersedia agar setiap template memiliki warna utama dan warna aksen.
- Setiap object pada schema bersifat `additionalProperties: false` — LLM/backend tidak boleh menyisipkan field tambahan di luar yang didefinisikan schema. Prompt generation dan `parse_and_validate()` harus memastikan tidak ada key liar sebelum validasi.
- URL WhatsApp tidak dihasilkan oleh LLM dan tidak disimpan sebagai field schema. URL dibuat oleh aplikasi dari `contact.whatsappNumber` dan `hero.ctaWhatsappMessage`.
- Nomor WhatsApp pada `WebsiteState` harus sudah dinormalisasi ke format angka Indonesia dengan awalan `62`, tanpa tanda plus, spasi, atau tanda hubung (`pattern: ^62[0-9]{8,13}$`).
- `iconKeyword` bersifat opsional pada setiap item `services`, digunakan sebagai tag ikon (mis. `"coffee"`, `"bread"`) yang dipetakan template renderer ke ikon/placeholder visual — bukan gambar aktual dari LLM.

Contoh pembuatan link WhatsApp:

```ts
const whatsappUrl =
  `https://wa.me/${state.contact.whatsappNumber}` +
  `?text=${encodeURIComponent(state.hero.ctaWhatsappMessage)}`;
```

### 4.1 Normalisasi nomor WhatsApp

Input pengguna boleh menggunakan format seperti:

```text
08123456789
+628123456789
62812 3456 789
```

Backend (AI Generation Service atau layer normalisasi Node) harus menormalisasinya menjadi:

```text
628123456789
```

## 5. Format Response Umum

### 5.1 Response berhasil

```json
{
  "success": true,
  "data": {},
  "meta": {
    "requestId": "req_abc123",
    "isFallback": false,
    "latencyMs": 4200
  }
}
```

`data` berisi `WebsiteState` lengkap untuk endpoint generate dan revise.

`latencyMs` adalah waktu pemrosesan total (Node orchestration + panggilan ke AI Generation Service). Waktu render iframe di browser diukur oleh frontend dan bukan bagian dari latency endpoint.

### 5.2 Response error

```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Business description tidak boleh kosong",
    "details": {}
  },
  "meta": {
    "requestId": "req_abc123"
  }
}
```

`details` bersifat opsional dan tidak boleh berisi API key atau detail internal server.

### 5.3 Status HTTP dan error code

| Status | Error code | Penggunaan |
|---:|---|---|
| 400 | `INVALID_REQUEST` | Body request kosong atau format field salah |
| 400 | `INVALID_WEBSITE_STATE` | `currentState` tidak sesuai schema |
| 422 | `UNSUPPORTED_REVISION` | Instruksi revisi belum didukung MVP |
| 429 | `RATE_LIMITED` | Batas request atau kuota API terlampaui |
| 502 | `LLM_UNAVAILABLE` | LLM gagal dan fallback tidak tersedia |
| 500 | `INTERNAL_ERROR` | Kesalahan internal backend |

## 6. Endpoint Generate First Draft

### `POST /api/v1/generate`

Membuat draft pertama website berdasarkan deskripsi bisnis pengguna.

#### Request body

```json
{
  "businessDescription": "Warung Kopi Sejahtera, jual kopi tubruk dan roti bakar di Surabaya, target anak muda nugas, wa 08123456789"
}
```

Aturan validasi:

- `businessDescription` wajib berupa string.
- Tidak boleh kosong setelah `trim`.
- Panjang yang diterima: 10 sampai 4000 karakter.
- Bahasa utama yang diharapkan adalah bahasa Indonesia.

#### Alur backend

1. Node/Express memvalidasi request.
2. Node/Express meneruskan `businessDescription` ke AI Generation Service (Python/FastAPI).
3. AI Generation Service mengirim instruksi terstruktur ke LLM, mem-parse output sebagai JSON.
4. Normalisasi nomor WhatsApp.
5. Validasi hasil terhadap `website-state.schema.json`.
6. Jika invalid, lakukan retry satu kali di dalam AI Generation Service.
7. Jika tetap gagal, kembalikan fallback `WebsiteState` yang valid dengan `isFallback: true`.
8. Node/Express menerima hasil dari AI Generation Service dan meneruskannya ke frontend dalam format response standar (Bagian 5).

#### Response berhasil

```json
{
  "success": true,
  "data": {
    "templateId": "template-fnb",
    "theme": {
      "primaryColor": "#6B3E26",
      "accentColor": "#F4C27A",
      "fontFamily": "sans"
    },
    "meta": {
      "businessName": "Warung Kopi Sejahtera",
      "category": "F&B",
      "tagline": "Teman ngopi dan nugas setiap hari"
    },
    "hero": {
      "title": "Kopi Nikmat untuk Menemani Harimu",
      "subtitle": "Kopi dan roti bakar untuk teman kerja dan nugas",
      "ctaText": "Pesan Sekarang",
      "ctaWhatsappMessage": "Halo, saya ingin memesan dari Warung Kopi Sejahtera"
    },
    "about": {
      "story": "Warung kopi yang menyediakan minuman dan makanan ringan untuk anak muda di Surabaya.",
      "highlights": ["Tempat nyaman untuk nugas", "Bahan berkualitas"]
    },
    "services": [
      {
        "name": "Kopi Tubruk",
        "description": "Kopi tubruk dengan rasa kuat dan aroma khas.",
        "priceEstimate": "Rp12.000",
        "iconKeyword": "coffee"
      },
      {
        "name": "Roti Bakar Cokelat",
        "description": "Roti bakar hangat dengan isian cokelat.",
        "priceEstimate": "Rp15.000",
        "iconKeyword": "bread"
      },
      {
        "name": "Es Kopi Susu",
        "description": "Kopi susu dingin dengan rasa lembut.",
        "priceEstimate": "Rp18.000",
        "iconKeyword": "milk"
      }
    ],
    "testimonials": [
      {
        "customerName": "Rina",
        "review": "Tempatnya nyaman untuk mengerjakan tugas dan kopinya enak."
      },
      {
        "customerName": "Bagas",
        "review": "Pelayanannya cepat dan roti bakarnya recommended."
      }
    ],
    "contact": {
      "whatsappNumber": "628123456789",
      "address": "Surabaya dan sekitarnya",
      "instagram": "@warungkopisejahtera"
    }
  },
  "meta": {
    "requestId": "req_abc123",
    "isFallback": false,
    "latencyMs": 4200
  }
}
```

## 7. Endpoint Revise

### `POST /api/v1/revise`

Memproses instruksi lanjutan pengguna tanpa merusak section yang tidak disebutkan.

#### Request body

`currentState` wajib berupa object `WebsiteState` lengkap, yaitu state dari response
`/generate` atau response `/revise` sebelumnya.

```json
{
  "currentState": "<WebsiteState lengkap dari response generate/revise>",
  "instruction": "Ganti nuansa warna menjadi cokelat tua klasik"
}
```

Backend tidak menggunakan session server untuk MVP; `currentState` wajib dikirim penuh oleh client setiap request.

#### Revisi yang wajib didukung MVP

- Mengubah `theme.primaryColor` atau `theme.accentColor`.
- Mengubah `theme.fontFamily`.
- Mengubah judul, subtitle, tagline, deskripsi, atau CTA.
- Menambah satu item baru pada `services`.
- Mengubah informasi kontak.

Perubahan section lain yang tidak disebutkan harus dipertahankan.

#### Alur backend

1. Node/Express memvalidasi `currentState` terhadap schema.
2. Node/Express meneruskan `currentState` dan `instruction` ke AI Generation Service sebagai context.
3. LLM menghasilkan instruksi mutasi internal.
4. Node/Express menerapkan mutasi ke state lama (merge/regression guard).
5. Node/Express memvalidasi hasil merge sebagai `WebsiteState` lengkap terhadap schema.
6. Node/Express mengembalikan full state hasil merge ke frontend.

Frontend tidak melakukan merge JSON sendiri.

#### Response berhasil

```json
{
  "success": true,
  "data": "<WebsiteState hasil merge>",
  "meta": {
    "requestId": "req_def456",
    "isFallback": false,
    "revisionApplied": true,
    "changedPaths": ["theme.primaryColor", "theme.accentColor"],
    "latencyMs": 3100
  }
}
```

> Catatan: `revisionApplied`, `changedPaths`, dan `fallbackReason` adalah tambahan desain tim untuk mendukung regression guard dan observability — bukan field yang secara eksplisit diwajibkan oleh FRD/Scrum Plan.

#### Revisi gagal setelah retry

Jika LLM gagal menghasilkan revisi yang valid, backend harus mengembalikan state lama tanpa perubahan:

```json
{
  "success": true,
  "data": "<WebsiteState lama>",
  "meta": {
    "requestId": "req_def456",
    "isFallback": true,
    "revisionApplied": false,
    "fallbackReason": "REVISION_FAILED",
    "latencyMs": 5200
  }
}
```

Jika instruksi memang belum didukung MVP, gunakan HTTP `422` dengan error code `UNSUPPORTED_REVISION`.

## 8. Endpoint Export

### `POST /api/v1/export`

Membuat bundle website final di sisi server, menggunakan rendering engine yang sama dengan yang dipakai preview, untuk menghindari drift antara preview dan hasil export.

#### Request body

```json
{
  "currentState": "WebsiteState"
}
```

#### Response

Binary stream dengan `Content-Type: application/zip`.

#### Kriteria wajib

- File hasil export **self-contained**: CSS terbundel, bersih dari script editor/kode internal builder (FR-06).
- Tombol WhatsApp aktif memakai format `https://wa.me/{nomor}?text={pesan}` (FR-06).
- File `index.html` bisa dibuka langsung offline (klik dua kali) dan tampilannya identik dengan preview (FR-06 acceptance criteria, TC-04).
- Rendering engine export wajib sama dengan rendering engine preview untuk mencegah drift.

## 9. Endpoint Publish (Stretch — Could-Have)

### `POST /api/v1/publish`

**Status:** Stretch goal (Could-Have per FR-07/US-11 dan Risk Matrix Scrum Plan). Bukan bagian dari kontrak MVP yang wajib diimplementasikan; dapat dipotong jika waktu sprint tidak mencukupi tanpa mempengaruhi status Done fitur lain.

```
POST /api/v1/publish
{
  "currentState": "WebsiteState"
}

Response:
{
  "publicUrl": "string"
}
```

Jika dikerjakan, `publicUrl` wajib ada pada response sukses (FR-07). Provider dan detail teknis (mis. static storage terpisah vs serving langsung dari backend) belum menjadi keputusan mengikat dan dapat diputuskan belakangan tanpa mempengaruhi kontrak endpoint lain.

## 10. Endpoint Health Check

### `GET /api/v1/health`

Digunakan frontend, developer, atau deployment untuk memastikan backend orkestrasi (Node/Express) dan AI Generation Service berjalan.

#### Response

```json
{
  "success": true,
  "data": {
    "status": "ok",
    "service": "ai-website-builder-backend"
  },
  "meta": {
    "requestId": "req_health001"
  }
}
```

## 11. Pembagian Implementasi

### Dev 1 — Backend & AI Generation Lead

- System prompt dan prompt engineering (generate & revise).
- Integrasi LLM (Python/FastAPI, `llm_service.py`).
- Parsing output JSON, normalisasi nomor WhatsApp.
- Retry dan fallback generation.
- Pengujian output terhadap `website-state.schema.json`.

### Dev 2 — Backend & AI Revision/Integration Lead

- Express app dan routing (`/api/v1/*`).
- Request validation.
- Orchestration generate dan revise, termasuk pemanggilan AI Generation Service.
- Merge mutation dan regression guard pada endpoint revise.
- Export Engine (ZIP/HTML server-side).
- Error handler dan health check.
- Integrasi API dengan frontend.

### Dev 3 — Frontend

- API client React.
- State `WebsiteState`.
- Chat panel dan loading state.
- Template renderer dan iframe preview.
- Revision update (replace full state, tanpa merge sendiri).
- UI download/export (memicu endpoint server-side, bukan generate ZIP sendiri).

## 12. Aturan Perubahan Kontrak

- `website-state.schema.json` adalah sumber kebenaran utama data.
- Perubahan field harus melalui Pull Request.
- Perubahan yang memengaruhi frontend wajib diberi tahu kepada seluruh tim.
- Jangan mengganti nama field hanya pada satu repository.
- Setiap perubahan kontrak harus menaikkan versi dokumen jika bersifat breaking change.
- API key dan file `.env` tidak boleh di-commit.

## 13. Sinkronisasi dengan Dokumen FRD dan Scrum Plan

Dokumen FRD perlu diselaraskan pada bagian berikut:

1. Ganti `services_products` menjadi `services` pada FR-03, agar konsisten dengan FRD §5 (yang sudah menggunakan `services`) dan `website-state.schema.json`.
2. Jelaskan bahwa URL WhatsApp dibuat aplikasi, bukan output langsung LLM.
3. Tambahkan `testimonials` sebagai field wajib minimal dua item pada narasi FR-03 (schema sudah menegakkan ini).
4. Gunakan field opsional `iconKeyword` seperti pada schema, alih-alih menyebut "keyword icon/image placeholder" secara umum.
5. Perjelas bahwa FR-07 (Publish) tetap berstatus stretch/Could-Have, sesuai keputusan tim — tidak perlu diangkat menjadi kewajiban MVP.

Scrum Plan tidak perlu perubahan besar: penugasan Export Engine ke Dev 2 (Hari 6 & 10) sudah konsisten dengan keputusan server-side export pada dokumen ini.
