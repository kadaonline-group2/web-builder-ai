# API Contract — AI Website Builder untuk UMKM

**Versi Dokumen:** 0.2 (Draft — keputusan #1–#8 sudah diambil tim, #9 masih terbuka)
**Referensi:** FRD v1.2, Scrum Project Plan v1.2 (3 Developer: 2 Backend+AI + 1 Frontend)
**Status:** Sebagian besar TBD sudah diputuskan — lihat Bagian 8 untuk keputusan final. Item #9 masih perlu dibahas tim.

## Legend

- ✅ **Ditetapkan** — langsung diturunkan dari FRD/Scrum Plan, bukan asumsi.
- 🟢 **Diputuskan (Tim)** — keputusan tim yang menggantikan status TBD sebelumnya.
- 🟡 **TBD** — belum diputuskan, dibahas di Bagian 8.

> **Catatan struktural:** Dokumen sumber (FRD, Scrum Plan) mendeskripsikan arsitektur secara high-level ("Chat Orchestrator", "Backend API Route", "Export Engine") tanpa mendefinisikan protokol API secara eksplisit. Untuk keperluan dokumen ini, endpoint ditulis dalam gaya REST/JSON sebagai kerangka penulisan. 🟢 **Base path, versioning, dan penamaan resource sudah diputuskan tim (lihat item #5): prefix `/api` + versioning eksplisit (`/api/v1/...`).**

---

## 1. WebsiteState Schema (Authoritative)

✅ Diambil verbatim dari FRD Bagian 5 ("kontrak skema JSON yang wajib divalidasi dari output LLM"). Ini adalah bentuk data yang dipertukarkan di seluruh endpoint (Generate, Revise, Export, Publish).

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UMKMWebsiteState",
  "type": "object",
  "required": ["templateId", "theme", "meta", "hero", "about", "services_products", "contact"],
  "properties": {
    "templateId": { "type": "string", "enum": ["template-services", "template-fnb", "template-retail"] },
    "theme": {
      "type": "object",
      "required": ["primaryColor", "fontFamily"],
      "properties": {
        "primaryColor": { "type": "string", "pattern": "^#([A-Fa-f0-9]{6})$" },
        "accentColor": { "type": "string", "pattern": "^#([A-Fa-f0-9]{6})$" },
        "fontFamily": { "type": "string", "enum": ["sans", "serif", "display"] }
      }
    },
    "meta": {
      "type": "object",
      "required": ["businessName", "category", "tagline"],
      "properties": {
        "businessName": { "type": "string" },
        "category": { "type": "string" },
        "tagline": { "type": "string" }
      }
    },
    "hero": {
      "type": "object",
      "required": ["title", "subtitle", "ctaText", "ctaWhatsappMessage"],
      "properties": {
        "title": { "type": "string" },
        "subtitle": { "type": "string" },
        "ctaText": { "type": "string" },
        "ctaWhatsappMessage": { "type": "string" }
      }
    },
    "about": {
      "type": "object",
      "required": ["story"],
      "properties": {
        "story": { "type": "string" },
        "highlights": { "type": "array", "items": { "type": "string" } }
      }
    },
    "services_products": {
      "type": "array",
      "minItems": 3,
      "items": {
        "type": "object",
        "required": ["name", "description", "priceEstimate"],
        "properties": {
          "name": { "type": "string" },
          "description": { "type": "string" },
          "priceEstimate": { "type": "string" }
        }
      }
    },
    "testimonials": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["customerName", "review"],
        "properties": {
          "customerName": { "type": "string" },
          "review": { "type": "string" }
        }
      }
    },
    "contact": {
      "type": "object",
      "required": ["whatsappNumber", "address"],
      "properties": {
        "whatsappNumber": { "type": "string" },
        "address": { "type": "string" },
        "instagram": { "type": "string" }
      }
    }
  }
}
```

🟢 **Keputusan diskrepansi (item #6 — resolved):** FR-03 menyebut field `services_products`, sedangkan skema resmi §5 (draft sebelumnya) memakai `services`. Tim memutuskan `services_products` sebagai nama field final, mengikuti penamaan di FR-03. Skema di atas sudah menggunakan nama final ini di `required` dan di `properties`.

---

## 2. Endpoint: Generate First Draft

**Referensi:** US-04, US-05, FR-02, FR-03, FR-04
**Method/Path:** 🟢 `POST /api/v1/generate` (base path & versioning diputuskan — lihat item #5)

### Request Body
✅ Input berupa deskripsi bisnis dalam chat (FR-02). Field name di bawah adalah 🟡 placeholder (tidak disebut eksplisit di dokumen):

```json
{
  "businessDescription": "string — deskripsi bisnis, bahasa Indonesia, multiline"
}
```

Constraint dari dokumen:
- ✅ Tidak boleh pesan kosong (FR-02 acceptance criteria).
- ✅ Prompt dibatasi maksimal 2.000 token per turn (NFR-05).

### Response Body
✅ Body utama: objek `WebsiteState` (Bagian 1), dengan `templateId` dipilih otomatis berdasarkan kategori bisnis secara deterministik (FR-04):
- `template-services` → Jasa & Konsultan
- `template-fnb` → Kuliner & F&B
- `template-retail` → Retail & Produk Fisik

🟢 **Desain flag fallback & status HTTP (item #2 — resolved):** Flag top-level `isFallback: true` disertakan pada response, tetap HTTP 200, untuk kondisi fallback ringan (retry gagal, dipakai data default). Kegagalan fatal (LLM API down total) menggunakan status 5xx terpisah, agar frontend/metrik bisa membedakan kegagalan ringan vs fatal.

### Constraint Tambahan
- ✅ Jika output LLM invalid/timeout: auto-retry 1x, lalu fallback ke data default tanpa membuat aplikasi crash (FR-03).
- ✅ Target waktu render preview < 5 detik setelah JSON diterima dari LLM (FR-04) — relevan sebagai target latensi endpoint ini.

---

## 3. Endpoint: Revise

**Referensi:** US-07, US-08, FR-05
**Method/Path:** 🟢 `POST /api/v1/revise` (lihat item #5)

### Request Body

```json
{
  "currentState": "WebsiteState — 🟢 wajib dikirim penuh oleh client di setiap request (lihat item #1)",
  "instruction": "string — perintah revisi dari user, mis. 'Ubah warna jadi nuansa hijau toska'"
}
```

✅ FR-05 menyebut eksplisit bahwa sistem menyertakan state JSON saat ini ke dalam prompt context LLM — jadi `currentState` (dalam bentuk apa pun ia sampai ke backend) pasti dibutuhkan sebagai bagian dari request LLM. 🟢 **State tracking (item #1 — resolved):** Pendekatan stateless dipilih — client (frontend) menyimpan dan mengirimkan `currentState` penuh pada setiap request Revise. Tidak ada session store di backend; sesuai dengan arsitektur "penyimpanan sesi lokal/in-memory" di FRD §1.3 dan timeline 8 hari.

Tiga jenis intent revisi yang wajib dikenali (✅ FR-05):
- Perubahan warna/tema
- Perubahan teks/copy
- Perubahan struktur (hapus/tambah section)

### Response Body
🟢 **Bentuk response (item #7 — resolved):** Response berupa **full merged `WebsiteState`** (backend yang melakukan merge/partial-mutation), bukan raw diff. Frontend cukup replace seluruh state di preview. Ini juga selaras dengan pembagian kerja Dev 2 di Scrum Plan v1.2 ("merge/validation partial state mutation, regression guard").

### Constraint Wajib (✅ FR-05 acceptance criteria)
> Perubahan pada satu section **tidak boleh** menghapus atau merusak data pada section lain yang tidak disebutkan dalam revisi.

Ini berlaku terlepas dari keputusan desain response (full state vs diff).

---

## 4. Endpoint: Export

**Referensi:** US-09, FR-06, TC-04
**Trigger UI:** tombol "Download Website"

🟢 **Mekanisme endpoint (item #3 & #8 — resolved):** Export dilakukan **server-side** (Option A) — backend membangun ulang bundle HTML/CSS dari `WebsiteState` menggunakan satu rendering engine yang sama dengan preview, menghindari drift antara preview dan hasil export. Delivery menggunakan **binary stream** (Option A) dengan `Content-Type: application/zip` langsung pada response HTTP.

```
POST /api/v1/export
{
  "currentState": "WebsiteState"
}
```

Response: 🟢 Binary stream, `Content-Type: application/zip` (item #8 — resolved)

### Kriteria Wajib (✅ dari FRD, berlaku terlepas dari pilihan desain teknis)
- File hasil export **self-contained**: CSS terbundel (mis. Tailwind CDN atau embedded style tag), bersih dari script editor/kode internal builder (FR-06).
- Tombol WhatsApp aktif memakai format `https://wa.me/{nomor}?text={pesan}` (FR-06).
- File `index.html` bisa dibuka langsung offline (klik dua kali) dan tampilannya identik dengan preview (FR-06 acceptance criteria, TC-04).

---

## 5. Endpoint: Publish (Stretch — Could-Have)

**Referensi:** US-11, FR-07
**Trigger UI:** tombol "Publish Online"

🟢 **Provider & mekanisme (item #4 — resolved):** Tim memutuskan **deploy** (bukan menunda fitur ini). Provider yang dipilih: **Render**, sebagai satu web service Python/FastAPI yang menjalankan backend (termasuk LLM calls) sekaligus menyajikan bundle HTML hasil export lewat route statis miliknya sendiri (mis. `/sites/{id}/index.html`). Tidak diperlukan static storage provider terpisah (Vercel/Supabase/Firebase) karena backend yang sudah men-generate bundle (item #3) bisa langsung menyimpan dan menyajikannya kembali. Konsekuensi: Render free tier mengalami cold start/spin-down setelah idle, jadi endpoint perlu di-"warm up" (satu request percobaan) sebelum sesi demo capstone.

```
POST /api/v1/publish
{
  "currentState": "WebsiteState"
}

Response:
{
  "publicUrl": "string" ✅ (wajib ada — URL yang di-serve langsung oleh backend Render yang sama)
}
```

---

## 6. Error Handling (Umum)

✅ Dari dokumen:
- Kegagalan parsing/invalid output JSON dari LLM → auto-retry 1x → fallback default → tidak boleh crash aplikasi (FR-03).
- Graceful degradation, tanpa perlu refresh halaman (NFR-04).

🟢 **Representasi HTTP status code untuk kegagalan LLM (item #2 — resolved):** Lihat Bagian 2 — flag `isFallback: true` + HTTP 200 untuk fallback ringan; HTTP 5xx untuk kegagalan fatal.

🟡 Belum ditentukan:
- Struktur error envelope umum untuk kegagalan lain di luar LLM — validasi request, dsb. (item #9 — masih terbuka, referensi ada di dokumen lain).

---

## 7. Ringkasan Endpoint

| Endpoint | Method | Status Kepastian | Referensi |
|---|---|---|---|
| Generate | 🟢 `POST /api/v1/generate` | Struktur request/response ✅/🟢, fallback flag 🟢 resolved | US-04, US-05, FR-02–04 |
| Revise | 🟢 `POST /api/v1/revise` | State tracking 🟢 resolved, response format 🟢 resolved | US-07, US-08, FR-05 |
| Export | 🟢 `POST /api/v1/export` | Mekanisme & delivery format 🟢 resolved (server-side, binary stream) | US-09, FR-06 |
| Publish | 🟢 `POST /api/v1/publish` | Provider 🟢 resolved (Render, self-hosted); `publicUrl` ✅ wajib ada | US-11, FR-07 |

---

## 8. Daftar Pertanyaan Terbuka untuk Didiskusikan Tim

### #1 — State tracking antara Generate dan Revise — 🟢 **Diputuskan: Opsi A**
FR-05 menyebut state JSON saat ini disertakan ke prompt context, tapi tidak dijelaskan siapa yang menyimpannya (frontend atau backend), sementara FRD §1.3 menyebut *"penyimpanan sesi lokal/in-memory"* tanpa merinci lokasi (browser atau server).

- **Opsi A — Stateless (client kirim full `currentState` tiap request Revise)** ✅ **DIPILIH**
  - (+) Sesuai dengan tidak adanya auth/DB persisten; tidak butuh session store; cocok timeline 8 hari.
  - (–) Payload request lebih besar tiap kali revisi; tidak ada histori otomatis di sisi server untuk debugging.
- **Opsi B — In-memory session di backend (`Map<sessionId, WebsiteState>`)**
  - (+) Payload request lebih kecil (cukup kirim `sessionId` + instruksi); backend bisa log histori revisi.
  - (–) Perlu mekanisme `sessionId` (header/cookie); state hilang saat server restart; menambah kompleksitas yang sebenarnya coba dihindari FRD.

### #2 — Desain flag fallback & status HTTP untuk kegagalan fatal — 🟢 **Diputuskan: Opsi A**
FR-03/NFR-04 menetapkan fallback harus terjadi tanpa merusak aplikasi/refresh halaman, tapi tidak merinci representasi HTTP-nya.

- **Opsi A — Flag top-level (`isFallback: true`) + tetap HTTP 200; kegagalan fatal (LLM API down total) pakai status 5xx terpisah** ✅ **DIPILIH**
  - (+) Frontend bisa bedakan kegagalan ringan vs fatal untuk keperluan UX/logging.
  - (–) Frontend perlu handle dua code path.
- **Opsi B — Semua kondisi (termasuk fatal) tetap HTTP 200 dengan data fallback disertakan**
  - (+) Konsisten dengan prinsip "tanpa refresh halaman"; frontend cukup satu code path.
  - (–) Sulit membedakan kegagalan ringan vs fatal untuk kebutuhan metrik latensi (Scrum Plan Hari 6: "logging metrik latensi").

### #3 — Mekanisme Export: server-side vs client-side — 🟢 **Diputuskan: Opsi A**
FRD tidak merinci apakah ZIP/HTML dibangun di backend atau langsung di browser dari state yang sudah ada di frontend.

- **Opsi A — Server-side generation** ✅ **DIPILIH**
  - (+) Satu sumber kebenaran untuk rendering logic (preview & export pakai engine yang sama di backend).
  - (–) Backend perlu mereplikasi template rendering engine yang mungkin juga ada di frontend (duplikasi kerja).
  - *Catatan:* Ini juga selaras dengan Scrum Plan v1.2, yang sudah menugaskan "Generator bundle ZIP/HTML standalone" ke Dev 2 sebagai backend work (Hari 6 & Hari 10).
- **Opsi B — Client-side generation (tanpa call API)**
  - (+) Tidak ada duplikasi rendering logic; lebih cepat (tanpa round-trip network).
  - (–) Risiko drift antara apa yang tampil di preview dan hasil export jika ada perbedaan environment/versi.

### #4 — Provider untuk fitur Publish — 🟢 **Diputuskan: Deploy dengan Render**
FR-07 menyebutkan Vercel CLI API, Supabase Storage, atau Firebase Hosting **hanya sebagai contoh**, bukan keputusan. Tim memutuskan untuk tetap mengerjakan fitur ini (bukan dipotong meski berstatus Could-Have), dengan **Render** sebagai provider:

- Render menjalankan backend Python/FastAPI sebagai persistent web service (bukan per-invocation serverless function), jadi tidak ada batas durasi eksekusi ketat saat memanggil LLM API.
- Free tier tanpa kartu kredit, cocok untuk proyek capstone tanpa budget.
- Backend yang sama (yang sudah membangun bundle export secara server-side per item #3) langsung menyajikan bundle tersebut lewat route publik miliknya sendiri — tidak perlu provider static storage terpisah.
- **Trade-off yang perlu diantisipasi:** Render free tier mengalami spin-down saat idle (cold start ~10–30 detik pada request pertama). Mitigasi: warm-up endpoint sesaat sebelum sesi demo sidang, dan tetap siapkan video fallback demo (sudah ada di checklist Scrum Plan).

### #5 — Base path & konvensi penamaan endpoint — 🟢 **Diputuskan**
Prefix path: **`/api`**, dengan versioning eksplisit (**`/api/v1/...`**). Semua endpoint pada dokumen ini (`/api/v1/generate`, `/api/v1/revise`, `/api/v1/export`, `/api/v1/publish`) mengikuti konvensi ini.

### #6 — Diskrepansi nama field: `services_products` (FR-03) vs `services` (Skema §5) — 🟢 **Diputuskan**
Field final: **`services_products`**, mengikuti penamaan di FR-03. Skema di Bagian 1 dokumen ini sudah diperbarui menggunakan nama final ini. Perlu dikonfirmasi ulang ke Dev 2 & Dev 3 agar validator, prompt engineering, dan renderer konsisten memakai nama yang sama.

### #7 — Bentuk response Revise: full state vs partial diff — 🟢 **Diputuskan: Opsi A**
FR-05 hanya menyebut *"LLM mengembalikan JSON mutasi"*, tapi Scrum Plan v1.2 mencantumkan tanggung jawab Dev 2 (Hari 5) sebagai *"merge/validation partial state mutation, regression guard"* — mengindikasikan proses merge terjadi di backend.

- **Opsi A — Response = full merged `WebsiteState` (backend yang merge)** ✅ **DIPILIH**
  - (+) Frontend tinggal replace seluruh state (tidak perlu merge logic sendiri); lebih aman untuk memenuhi syarat "section lain tidak boleh rusak" (FR-05).
  - (–) Payload response lebih besar.
- **Opsi B — Response = partial diff/patch (frontend yang merge)**
  - (+) Payload lebih kecil.
  - (–) Risiko bug merge di sisi frontend; kurang selaras dengan pembagian kerja Dev 2 di Scrum Plan v1.2 yang eksplisit menyebut "merge" sebagai tanggung jawab backend.

### #8 — Format delivery file Export — 🟢 **Diputuskan: Opsi A**
Tergantung jawaban item #3 di atas (server-side generation, sudah diputuskan).

- **Opsi A — Binary stream** (`Content-Type: application/zip`) langsung di response HTTP. ✅ **DIPILIH**
  - Konsisten dengan pendekatan stateless (item #1) dan cukup sederhana untuk timeline 8 hari; cocok dengan alur TC-04 ("ekstrak zip, buka file index.html").
- **Opsi B — Base64-encoded** di dalam field JSON.
- **Opsi C — Backend upload sementara, kembalikan signed URL** untuk didownload terpisah.

### #9 — Error envelope umum (di luar fallback LLM) — 🟡 **Masih TBD**
Belum ada spesifikasi untuk jenis kegagalan lain: request tidak valid (mis. format nomor WhatsApp salah), token budget per turn terlampaui (NFR-05), dsb. Perlu skema error response yang konsisten dipakai di semua endpoint (mis. `{ "error": { "code": ..., "message": ... } }`). Referensi keputusan untuk item ini ada di dokumen lain — belum dijawab di sini, sengaja dibiarkan terbuka.

---

**Rekomendasi langkah berikutnya:** Item #1–#8 sudah final per keputusan tim di atas. Sinkronkan penamaan field `services_products` (item #6) dan base path `/api/v1` (item #5) ke Dev 2 (validator/orchestrator) dan Dev 3 (renderer) secepatnya agar tidak terjadi drift kontrak di sisa sprint. Item #9 masih perlu dibahas bersama tim sebelum code freeze (Hari 7).
