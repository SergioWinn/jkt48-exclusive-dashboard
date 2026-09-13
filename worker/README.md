# Close snapshot Worker

Worker ini menyimpan snapshot bonus dan mengirimnya ke Telegram pada **menit tepat sebelum** penutupan penjualan (misalnya close 10:00 WIB, kirim pada 09:59 WIB). Dashboard Streamlit tidak perlu dibuka.

Sebelum kedua secret Telegram diisi, Worker berhenti tanpa memanggil API JKT48 atau Telegram.

Worker menyegarkan jadwal setiap 6 jam. Karena list API sering tidak berisi `sales_period`, Worker membaca detail event saat sinkronisasi untuk menemukan waktu close yang sebenarnya. Hanya pada menit target Worker memanggil detail utama **dan** endpoint `/bonus`; tanpa JSON bonus yang valid, tidak ada snapshot yang dikirim.

## Setup

1. Dari folder `worker`, install Wrangler lalu buat namespace KV:

   ```powershell
   npm install
   npx wrangler kv namespace create SNAPSHOTS
   ```

2. Salin ID namespace hasil perintah tersebut ke `wrangler.jsonc`, menggantikan `REPLACE_WITH_KV_NAMESPACE_ID`.

3. Simpan kredensial Telegram sebagai secret (jangan masukkan ke Git):

   ```powershell
   npx wrangler secret put TELEGRAM_BOT_TOKEN
   npx wrangler secret put TELEGRAM_CHAT_ID
   ```

   `TELEGRAM_CHAT_ID` dapat berupa ID chat pribadi, grup, atau `@nama_channel`; bot harus sudah memulai chat atau menjadi admin channel.

   Jika JKT48 mengembalikan Waiting Room/Cloudflare untuk Worker, isi cookie Waiting Room yang masih berlaku sebagai secret opsional:

   ```powershell
   npx wrangler secret put JKT48_COOKIE
   ```

4. Verifikasi logika dan deploy:

   ```powershell
   npm test
   npx wrangler deploy
   ```

Cron `* * * * *` memakai UTC, tetapi kode menghitung waktu close dari API dalam WIB. Cron hanya menentukan kapan Worker bangun; pengiriman hanya dilakukan saat selisihnya tepat satu menit.

Snapshot dikirim sebagai dokumen JSON dan juga disimpan di KV. Ini sengaja memakai data API langsung, bukan screenshot Streamlit, sehingga tetap bekerja tanpa browser aktif dan tidak membutuhkan Browser Run/headless Chrome.
