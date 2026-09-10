# API Contract — AI Website Builder untuk UMKM

**Versi Dokumen:** 0.1 (Draft — sebagian TBD)
**Referensi:** FRD v1.2, Scrum Project Plan v1.2 (3 Developer: 2 Backend+AI + 1 Frontend)
**Status:** Belum final — lihat Bagian 8 untuk daftar keputusan yang masih perlu didiskusikan tim

## Legend

- ✅ **Ditetapkan** — langsung diturunkan dari FRD/Scrum Plan, bukan asumsi.
- 🟡 **TBD** — belum diputuskan, dibahas di Bagian 8.

> **Catatan struktural:** Dokumen sumber (FRD, Scrum Plan) mendeskripsikan arsitektur secara high-level ("Chat Orchestrator", "Backend API Route", "Export Engine") tanpa mendefinisikan protokol API secara eksplisit. Untuk keperluan dokumen ini, endpoint ditulis dalam gaya REST/JSON sebagai kerangka penulisan — ini **bukan keputusan final**, hanya scaffolding agar draft bisa didiskusikan. Base path, versioning, dan penamaan resource tetap 🟡 TBD (lihat item #5).

---

## 1. WebsiteState Schema (Authoritative)

✅ Diambil verbatim dari FRD Bagian 5 ("kontrak skema JSON yang wajib divalidasi dari output LLM"). Ini adalah bentuk data yang dipertukarkan di seluruh endpoint (Generate, Revise, Export, Publish).

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UMKMWebsiteState",
  "type": "object",
  "required": ["templateId", "theme", "meta", "hero", "about", "services", "contact"],
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
    "services": {
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

🟡 **Catatan diskrepansi (lihat item #6):** FR-03 menyebut field `services_products`, sedangkan skema resmi §5 memakai `services`. Dokumen ini memakai `services` sebagai authoritative karena §5 eksplisit berlabel kontrak wajib.

---

## 2. Endpoint: Generate First Draft

**Referensi:** US-04, US-05, FR-02, FR-03, FR-04
**Method/Path:** `POST /generate` 🟡 (path final TBD, lihat item #5)

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

🟡 Ada tidaknya flag fallback dan bentuknya — lihat item #2.

### Constraint Tambahan
- ✅ Jika output LLM invalid/timeout: auto-retry 1x, lalu fallback ke data default tanpa membuat aplikasi crash (FR-03).
- ✅ Target waktu render preview < 5 detik setelah JSON diterima dari LLM (FR-04) — relevan sebagai target latensi endpoint ini.

---

## 3. Endpoint: Revise

**Referensi:** US-07, US-08, FR-05
**Method/Path:** `POST /revise` 🟡

### Request Body

```json
{
  "currentState": "WebsiteState — 🟡 TBD apakah wajib dikirim client, lihat item #1",
  "instruction": "string — perintah revisi dari user, mis. 'Ubah warna jadi nuansa hijau toska'"
}
```

✅ FR-05 menyebut eksplisit bahwa sistem menyertakan state JSON saat ini ke dalam prompt context LLM — jadi `currentState` (dalam bentuk apa pun ia sampai ke backend) pasti dibutuhkan sebagai bagian dari request LLM. 🟡 Yang belum jelas: siapa yang menyimpan/mengirim `currentState` ini (lihat item #1).

Tiga jenis intent revisi yang wajib dikenali (✅ FR-05):
- Perubahan warna/tema
- Perubahan teks/copy
- Perubahan struktur (hapus/tambah section)

### Response Body
🟡 Bentuk response — full `WebsiteState` hasil merge, atau partial diff — lihat item #7.

### Constraint Wajib (✅ FR-05 acceptance criteria)
> Perubahan pada satu section **tidak boleh** menghapus atau merusak data pada section lain yang tidak disebutkan dalam revisi.

Ini berlaku terlepas dari keputusan desain response (full state vs diff).

---

## 4. Endpoint: Export

**Referensi:** US-09, FR-06, TC-04
**Trigger UI:** tombol "Download Website"

🟡 **Seluruh mekanisme endpoint ini TBD** — termasuk apakah perlu call ke backend sama sekali (lihat item #3 dan #8). Kerangka di bawah adalah placeholder jika desain server-side dipilih:

```
POST /export 🟡
{
  "currentState": "WebsiteState"
}
```

Response: 🟡 TBD (binary stream / base64 / signed URL — item #8)

### Kriteria Wajib (✅ dari FRD, berlaku terlepas dari pilihan desain teknis)
- File hasil export **self-contained**: CSS terbundel (mis. Tailwind CDN atau embedded style tag), bersih dari script editor/kode internal builder (FR-06).
- Tombol WhatsApp aktif memakai format `https://wa.me/{nomor}?text={pesan}` (FR-06).
- File `index.html` bisa dibuka langsung offline (klik dua kali) dan tampilannya identik dengan preview (FR-06 acceptance criteria, TC-04).

---

## 5. Endpoint: Publish (Stretch — Could-Have)

**Referensi:** US-11, FR-07
**Trigger UI:** tombol "Publish Online"

🟡 **Seluruh mekanisme endpoint ini TBD** — provider hosting belum diputuskan (item #4), begitu juga path/request/response detail.

Yang eksplisit dari FRD:
- ✅ Fitur ini mengunggah bundle HTML ke *static storage provider*.
- ✅ Response **wajib** mengembalikan public URL aktif (FR-07: *"mengembalikan public URL aktif"*).
- FRD menyebut Vercel CLI API, Supabase Storage, Firebase Hosting **sebagai contoh**, bukan keputusan final.

```
POST /publish 🟡
{
  "currentState": "WebsiteState" 🟡
}

Response:
{
  "publicUrl": "string" ✅ (wajib ada)
  // field lain tergantung provider — 🟡 TBD
}
```

---

## 6. Error Handling (Umum)

✅ Dari dokumen:
- Kegagalan parsing/invalid output JSON dari LLM → auto-retry 1x → fallback default → tidak boleh crash aplikasi (FR-03).
- Graceful degradation, tanpa perlu refresh halaman (NFR-04).

🟡 Belum ditentukan:
- Representasi HTTP status code untuk kegagalan LLM (item #2).
- Struktur error envelope umum untuk kegagalan lain di luar LLM — validasi request, dsb. (item #9).

---

## 7. Ringkasan Endpoint

| Endpoint | Method | Status Kepastian | Referensi |
|---|---|---|---|
| Generate | `POST /generate` 🟡 path | Struktur request/response sebagian ✅, sebagian 🟡 | US-04, US-05, FR-02–04 |
| Revise | `POST /revise` 🟡 path | Struktur request/response sebagian ✅, sebagian 🟡 | US-07, US-08, FR-05 |
| Export | `POST /export` 🟡 seluruhnya | Hanya kriteria hasil akhir yang ✅ | US-09, FR-06 |
| Publish | `POST /publish` 🟡 seluruhnya | Hanya kewajiban `publicUrl` yang ✅ | US-11, FR-07 |

---

## 8. Daftar Pertanyaan Terbuka untuk Didiskusikan Tim

### #1 — State tracking antara Generate dan Revise
FR-05 menyebut state JSON saat ini disertakan ke prompt context, tapi tidak dijelaskan siapa yang menyimpannya (frontend atau backend), sementara FRD §1.3 menyebut *"penyimpanan sesi lokal/in-memory"* tanpa merinci lokasi (browser atau server).

- **Opsi A — Stateless (client kirim full `currentState` tiap request Revise)**
  - (+) Sesuai dengan tidak adanya auth/DB persisten; tidak butuh session store; cocok timeline 8 hari.
  - (–) Payload request lebih besar tiap kali revisi; tidak ada histori otomatis di sisi server untuk debugging.
- **Opsi B — In-memory session di backend (`Map<sessionId, WebsiteState>`)**
  - (+) Payload request lebih kecil (cukup kirim `sessionId` + instruksi); backend bisa log histori revisi.
  - (–) Perlu mekanisme `sessionId` (header/cookie); state hilang saat server restart; menambah kompleksitas yang sebenarnya coba dihindari FRD.

### #2 — Desain flag fallback & status HTTP untuk kegagalan fatal
FR-03/NFR-04 menetapkan fallback harus terjadi tanpa merusak aplikasi/refresh halaman, tapi tidak merinci representasi HTTP-nya.

- **Opsi A — Flag top-level (`isFallback: true`) + tetap HTTP 200; kegagalan fatal (LLM API down total) pakai status 5xx terpisah**
  - (+) Frontend bisa bedakan kegagalan ringan vs fatal untuk keperluan UX/logging.
  - (–) Frontend perlu handle dua code path.
- **Opsi B — Semua kondisi (termasuk fatal) tetap HTTP 200 dengan data fallback disertakan**
  - (+) Konsisten dengan prinsip "tanpa refresh halaman"; frontend cukup satu code path.
  - (–) Sulit membedakan kegagalan ringan vs fatal untuk kebutuhan metrik latensi (Scrum Plan Hari 6: "logging metrik latensi").

### #3 — Mekanisme Export: server-side vs client-side
FRD tidak merinci apakah ZIP/HTML dibangun di backend atau langsung di browser dari state yang sudah ada di frontend.

- **Opsi A — Server-side generation**
  - (+) Satu sumber kebenaran untuk rendering logic (preview & export pakai engine yang sama di backend).
  - (–) Backend perlu mereplikasi template rendering engine yang mungkin juga ada di frontend (duplikasi kerja).
- **Opsi B — Client-side generation (tanpa call API)**
  - (+) Tidak ada duplikasi rendering logic; lebih cepat (tanpa round-trip network).
  - (–) Risiko drift antara apa yang tampil di preview dan hasil export jika ada perbedaan environment/versi.

### #4 — Provider untuk fitur Publish
FR-07 menyebutkan Vercel CLI API, Supabase Storage, atau Firebase Hosting **hanya sebagai contoh**, bukan keputusan. Ini murni pilihan tim — perlu dipertimbangkan dari sisi kemudahan integrasi dalam sisa waktu sprint mengingat fitur ini Could-Have (US-11) dan berisiko dipotong jika waktu tidak cukup (lihat Risk Matrix Scrum Plan).

### #5 — Base path & konvensi penamaan endpoint
Tidak disebutkan sama sekali di FRD/Scrum Plan. Perlu disepakati: prefix path (mis. `/api/...` atau tanpa prefix), penamaan resource (`/generate` vs `/website/generate`, dst.), dan apakah perlu versioning eksplisit.

### #6 — Diskrepansi nama field: `services_products` (FR-03) vs `services` (Skema §5)
FR-03 (deskripsi naratif requirement) menyebut field `services_products`, sementara kontrak skema resmi di §5 (yang eksplisit berlabel "wajib divalidasi") memakai `services`. Draft ini memakai `services` sebagai default karena §5 adalah kontrak formal, tapi perlu dikonfirmasi supaya prompt engineering (Dev 1) tidak salah pakai nama field.

### #7 — Bentuk response Revise: full state vs partial diff
FR-05 hanya menyebut *"LLM mengembalikan JSON mutasi"*, tapi Scrum Plan v1.2 mencantumkan tanggung jawab Dev 2 (Hari 5) sebagai *"merge/validation partial state mutation, regression guard"* — mengindikasikan proses merge terjadi di backend, sehingga response ke frontend kemungkinan berupa `WebsiteState` penuh hasil merge (bukan raw diff yang perlu di-merge sendiri oleh frontend). Ini masih inferensi, bukan pernyataan eksplisit.

- **Opsi A — Response = full merged `WebsiteState` (backend yang merge)**
  - (+) Frontend tinggal replace seluruh state (tidak perlu merge logic sendiri); lebih aman untuk memenuhi syarat "section lain tidak boleh rusak" (FR-05).
  - (–) Payload response lebih besar.
- **Opsi B — Response = partial diff/patch (frontend yang merge)**
  - (+) Payload lebih kecil.
  - (–) Risiko bug merge di sisi frontend; kurang selaras dengan pembagian kerja Dev 2 di Scrum Plan v1.2 yang eksplisit menyebut "merge" sebagai tanggung jawab backend.

### #8 — Format delivery file Export
Tergantung jawaban item #3 di atas.

- **Opsi A — Binary stream** (`Content-Type: application/zip`) langsung di response HTTP.
- **Opsi B — Base64-encoded** di dalam field JSON.
- **Opsi C — Backend upload sementara, kembalikan signed URL** untuk didownload terpisah.

### #9 — Error envelope umum (di luar fallback LLM)
Belum ada spesifikasi untuk jenis kegagalan lain: request tidak valid (mis. format nomor WhatsApp salah), token budget per turn terlampaui (NFR-05), dsb. Perlu skema error response yang konsisten dipakai di semua endpoint (mis. `{ "error": { "code": ..., "message": ... } }`).

---

**Rekomendasi langkah berikutnya:** bahas Bagian 8 di sesi sync tim (Dev 1 & Dev 2, mengingat Dev 2 juga Scrum Master dan integration owner per Scrum Plan v1.2), lalu update dokumen ini — ganti 🟡 menjadi ✅ seiring keputusan diambil.
