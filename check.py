from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
col = client['bigdata_db']['articles']

print('Total dokumen:', col.count_documents({}))
print('Dari NewsAPI:', col.count_documents({'src': 'newsapi'}))
print('Dari Detik  :', col.count_documents({'src': 'detik_inet'}))

# Tampilkan 1 contoh dari masing-masing
import json
for src in ['newsapi', 'detik_inet']:
    doc = col.find_one({'src': src})
    print(f'\n=== Contoh dari {src} ===')
    print(json.dumps(doc, indent=2, default=str, ensure_ascii=False))
