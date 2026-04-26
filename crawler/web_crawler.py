import os, hashlib, requests, pymongo, time
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# ── Koneksi MongoDB ──────────────────────────
client = pymongo.MongoClient(os.getenv('MONGO_URI'))
col = client[os.getenv('MONGO_DB')][os.getenv('MONGO_COL')]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

BASE_URL = 'https://inet.detik.com'

# ── Ambil halaman utama ──────────────────────
res = requests.get(BASE_URL, headers=HEADERS, timeout=10)

print("Status:", res.status_code)

soup = BeautifulSoup(res.text, 'lxml')

# ── Ambil semua link artikel (FIXED) ─────────
links = set()
for a in soup.find_all('a', href=True):
    href = a['href']

    if 'inet.detik.com' in href:
        # skip halaman yang bukan artikel
        if any(x in href for x in ['video', 'foto', 'tag', 'indeks']):
            continue

        links.add(href)

print(f'Ditemukan {len(links)} link artikel...')

# ── Proses detail artikel ────────────────────
saved = 0

for link in list(links)[:30]:  # ambil max 30 artikel
    try:
        time.sleep(1)  # biar ga ke-block

        detail = requests.get(link, headers=HEADERS, timeout=10)
        d = BeautifulSoup(detail.text, 'lxml')

        # ── Judul ──
        title_tag = d.find('h1')
        title = title_tag.text.strip() if title_tag else None

        # ── Timestamp ──
        time_tag = d.find('time')
        meta_ts = d.find('meta', {'property': 'article:published_time'})

        if time_tag and time_tag.get('datetime'):
            ts = time_tag['datetime']
        elif meta_ts:
            ts = meta_ts.get('content')
        else:
            ts = datetime.now(timezone.utc).isoformat()

        # ── Isi artikel ──
        paragraphs = d.select('div.detail__body p')

        if not paragraphs:
            paragraphs = d.select('article p')

        text = ' '.join(p.text.strip() for p in paragraphs if p.text.strip())

        # ── Keywords ──
        meta_kw = d.find('meta', {'name': 'keywords'})
        entities = []

        if meta_kw and meta_kw.get('content'):
            entities = [k.strip() for k in meta_kw['content'].split(',')][:10]

        # ── Unique ID ──
        uid = hashlib.sha1(f'detik|{link}'.encode()).hexdigest()

        # ── Dokumen ──
        doc = {
            '_id': uid,
            'src': 'detik_inet',
            'fmt': 'html',
            'ts': ts,
            'title': title,
            'text': text[:3000],
            'entities': entities,
            'kv': {
                'site': 'inet.detik.com',
                'url': link
            }
        }

        # ── Simpan ke MongoDB ──
        result = col.update_one({'_id': uid}, {'$set': doc}, upsert=True)

        if result.upserted_id and title and text:
            saved += 1
            print(f'✓ Saved: {title[:60]}')

    except Exception as e:
        print(f'✗ Error di {link}: {e}')

print(f'[Detik.com] Selesai. {saved} dokumen baru disimpan.')