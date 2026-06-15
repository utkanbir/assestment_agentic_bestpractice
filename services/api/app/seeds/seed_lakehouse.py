"""One-shot script: load Migros-specific lakehouse questions into API.
Run: py seed_lakehouse.py
"""
import asyncio
import httpx

LAKEHOUSE_QUESTIONS = [
    {
        "workstream": "lakehouse",
        "area": "medallion_architecture",
        "text": "Databricks ortaminizda Bronze-Silver-Gold (medallion) katlari nasil tanimlanmis? Her katmanin sorumlulugu ve veri donusum kurallari nelerdir?",
        "follow_ups": [
            "Bronze'dan Silver'a geciste hangi temizleme adimlar uygulaniy or?",
            "Gold katmaninda kac is alanina ait aggregate tablo var?",
            "Katmanlar arasi SLA ve freshness gereksinimleri tanimli mi?",
        ],
        "order": 1,
        "is_active": True,
    },
    {
        "workstream": "lakehouse",
        "area": "unity_catalog_governance",
        "text": "Unity Catalog kullaniliyor mu? Catalog-schema-tablo hiyerarsisi nasil organize edilmis, erisim kontrolleri kim tarafindan yonetiliyor?",
        "follow_ups": [
            "Row-level ve column-level guvenlik (dynamic views) uygulaniy or mu?",
            "PII veri siniflandirma etiketleri tanimli mi?",
            "Service principal ve grup bazli izin yonetimi var mi?",
        ],
        "order": 2,
        "is_active": True,
    },
    {
        "workstream": "lakehouse",
        "area": "delta_lake_table_management",
        "text": "Delta Lake tablo yasam dongusu nasil yonetiliyor? Z-ordering, liquid clustering veya OPTIMIZE komutlari otomatize edilmis mi?",
        "follow_ups": [
            "VACUUM politikasi nedir, kac gunluk gecmis saklaniy or?",
            "Time travel aktif olarak kullaniliyor mu?",
            "Buyuk tablolar icin partition stratejisi nedir?",
        ],
        "order": 3,
        "is_active": True,
    },
    {
        "workstream": "lakehouse",
        "area": "teradata_migration",
        "text": "Teradata'dan Databricks'e migrasyon sureci nerede? Hangi is yukler tasindy, hangilerinin tasinmasi planlaniy or?",
        "follow_ups": [
            "BTEQ/SQL uyumluluk sorunlari nasil yonetiliyor?",
            "Reconciliation (dogrulama) stratejisi nedir?",
            "Dual-run sureci var mi ve ne kadar surmesi bekleniyor?",
        ],
        "order": 4,
        "is_active": True,
    },
    {
        "workstream": "lakehouse",
        "area": "streaming_integration",
        "text": "Kafka'dan Databricks'e gercek zamanli veri akisi var mi? Delta Live Tables veya Structured Streaming kullaniliyor mu?",
        "follow_ups": [
            "Exactly-once semantics nasil garanti ediliyor?",
            "Stream-batch birlesik pipeline var mi?",
            "Gecikme (latency) ve throughput SLA nedir?",
        ],
        "order": 5,
        "is_active": True,
    },
    {
        "workstream": "lakehouse",
        "area": "compute_cost_optimization",
        "text": "Databricks cluster yonetimi ve maliyet optimizasyonu nasil yapiliyor? Spot instance, auto-terminate, cluster policy kullaniliyor mu?",
        "follow_ups": [
            "DBU (Databricks Unit) harcamasi nasil izleniyor?",
            "Photon engine aktif mi?",
            "Job Cluster vs All-Purpose Cluster ayrimi uygulaniy or mu?",
        ],
        "order": 6,
        "is_active": True,
    },
    {
        "workstream": "lakehouse",
        "area": "data_quality_dlt",
        "text": "Databricks ortaminda veri kalitesi nasil olcuIuyor? DLT expectations veya dbt tests kullaniliyor mu?",
        "follow_ups": [
            "Kalite ihlalinde pipeline durdurma mi karantina mi?",
            "DQ metrikleri merkezi izleniyor mu?",
            "OpenMetadata DQ entegrasyonu planlandi mi?",
        ],
        "order": 7,
        "is_active": True,
    },
    {
        "workstream": "lakehouse",
        "area": "bi_ml_integration",
        "text": "Lakehouse uzerinden Power BI, ML modelleri ve feature store entegrasyonu nasil calisiyor?",
        "follow_ups": [
            "Power BI Direct Lake modu mu import modu mu kullaniliyor?",
            "MLflow experiment tracking bagli mi?",
            "Feature store ile online serving entegrasyonu var mi?",
        ],
        "order": 8,
        "is_active": True,
    },
]


async def main():
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30) as client:
        payload = {
            "workstream": "lakehouse",
            "replace": True,
            "questions": LAKEHOUSE_QUESTIONS,
        }
        resp = await client.post("/api/v1/question-bank/bulk", json=payload)
        if resp.status_code == 201:
            data = resp.json()
            print(f"Lakehouse sorulari yuklendi: {data.get('loaded')} soru, workstream={data.get('workstream')}")
        else:
            print(f"HATA {resp.status_code}: {resp.text}")


if __name__ == "__main__":
    asyncio.run(main())
