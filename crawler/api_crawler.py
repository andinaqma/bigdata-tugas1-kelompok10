import os, hashlib, requests, pymongo
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()  # baca file .env

# Koneksi MongoDB 
client = pymongo.MongoClient(os.getenv('MONGO_URI'))
col = client[os.getenv('MONGO_DB')][os.getenv('MONGO_COL')]

# Ambil data dari NewsAPI 
API_KEY = os.getenv('NEWS_API_KEY')
url = ('https://newsapi.org/v2/everything'
       '?q=startup+teknologi+indonesia'
       '&language=id'
       '&sortBy=publishedAt'
       '&pageSize=100'
       f'&apiKey={API_KEY}')

res = requests.get(url)
data = res.json()

saved = 0
for article in data.get('articles', []):
    url_art = article.get('url', '')
    uid = hashlib.sha1(f"newsapi|{url_art}".encode()).hexdigest()

    # Ekstrak entitas dari title (kata penting)
    title = article.get('title') or ''
    entities = [w for w in title.split() if len(w) > 5 and w[0].isupper()]

    doc = {
        '_id'     : uid,
        'src'     : 'newsapi',
        'fmt'     : 'json',
        'ts'      : article.get('publishedAt'),  # sudah ISO UTC
        'title'   : title,
        'text'    : article.get('content') or article.get('description') or '',
        'entities': entities,
        'kv'      : {
            'author'  : article.get('author'),
            'url'     : url_art,
            'site'    : article.get('source', {}).get('name'),
            'likes'   : 0,
            'shares'  : 0,
        }
    }

    # upsert: insert jika belum ada, update jika sudah ada
    result = col.update_one({'_id': uid}, {'$set': doc}, upsert=True)
    if result.upserted_id:
        saved += 1

print(f'[NewsAPI] Selesai. {saved} dokumen baru disimpan.')
