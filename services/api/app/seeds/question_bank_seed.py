"""
S3-BA-005: 8 workstream question bank seed data (Kubernetes + 7 new).

Run via: POST /api/v1/question-bank/bulk  (replace=True)
Or call seed_all() directly during startup / management command.
"""

QUESTION_BANKS: dict[str, list[dict]] = {

    # ─── Already in MCP resources (hardcoded) — now API-backed ───────────────
    "kubernetes": [
        {"area": "cluster_architecture",
         "text": "Mevcut Kubernetes cluster mimarinizi açıklar mısınız? Kaç node var, hangi Kubernetes versiyonu kullanılıyor?",
         "follow_ups": ["Node tipleri neler (master/worker)?", "Managed mi (EKS/GKE/AKS) yoksa self-hosted mı?"]},
        {"area": "workload_management",
         "text": "Hangi workload tipleri çalışıyor? (Deployment, StatefulSet, DaemonSet, Job/CronJob)",
         "follow_ups": ["Stateful uygulamalar nasıl yönetiliyor?", "PersistentVolume stratejisi nedir?"]},
        {"area": "networking",
         "text": "CNI plugin olarak ne kullanıyorsunuz? NetworkPolicy tanımlı mı?",
         "follow_ups": ["Service mesh var mı (Istio/Linkerd)?", "Ingress controller nedir?"]},
        {"area": "security",
         "text": "RBAC politikaları nasıl tanımlanmış? Pod Security Standards uygulanıyor mu?",
         "follow_ups": ["Secret yönetimi nasıl yapılıyor?", "Image scanning süreci var mı?"]},
        {"area": "observability",
         "text": "Cluster ve workload metrikleri nasıl izleniyor? Hangi observability stack kullanılıyor?",
         "follow_ups": ["Log aggregation çözümü nedir?", "Alert mekanizması var mı?"]},
        {"area": "capacity",
         "text": "Resource request/limit tanımları yapılmış mı? HPA/VPA kullanılıyor mu?",
         "follow_ups": ["Cluster autoscaler aktif mi?", "Resource quota namespace bazında tanımlı mı?"]},
        {"area": "disaster_recovery",
         "text": "etcd yedekleme stratejisi nedir? Cluster restore prosedürü test edildi mi?",
         "follow_ups": ["RTO ve RPO hedefleri nedir?", "Multi-region/AZ dağılımı var mı?"]},
        {"area": "cicd",
         "text": "Deployment pipeline nasıl çalışıyor? GitOps (ArgoCD/Flux) kullanılıyor mu?",
         "follow_ups": ["Rollback süreci nasıl işliyor?", "Blue/green veya canary deployment var mı?"]},
    ],

    # ─── S3-AA-001: Cloud Strategy ───────────────────────────────────────────
    "cloud_strategy": [
        {"area": "cloud_vision",
         "text": "Kurumun cloud transformation vizyonu ve stratejik hedefleri nelerdir? 3 yıllık roadmap var mı?",
         "follow_ups": ["Hangi iş fonksiyonları öncelikli olarak cloud'a taşınacak?", "Cloud-first mi yoksa hybrid mi?"]},
        {"area": "provider_strategy",
         "text": "Hangi cloud sağlayıcılarını kullanıyorsunuz veya değerlendiriyorsunuz? Multi-cloud stratejiniz var mı?",
         "follow_ups": ["AWS, Azure, GCP arasındaki tercih kriterleri neler?", "Vendor lock-in riski nasıl yönetiliyor?"]},
        {"area": "cost_management",
         "text": "Cloud harcamaları nasıl izleniyor ve optimize ediliyor? FinOps pratikleri uygulanıyor mu?",
         "follow_ups": ["Chargeback/showback modeli var mı?", "Reserved instance veya savings plan kullanılıyor mu?"]},
        {"area": "landing_zone",
         "text": "Cloud landing zone tasarımı nasıl yapılmış? Account/subscription yapısı nedir?",
         "follow_ups": ["Network topology (hub-spoke, mesh)?", "Policy-as-code (Terraform, Pulumi) kullanılıyor mu?"]},
        {"area": "security_compliance",
         "text": "Cloud güvenlik mimarisi nasıl tasarlanmış? Compliance gereksinimleri (KVKK, ISO 27001) nasıl karşılanıyor?",
         "follow_ups": ["IAM/RBAC yapısı nasıl organize edilmiş?", "CSPM araçları kullanılıyor mu?"]},
        {"area": "migration",
         "text": "Mevcut on-prem workload'larının cloud migration stratejisi nedir? (6R: Rehost, Replatform, Refactor...)",
         "follow_ups": ["Migration wave planlaması yapıldı mı?", "Bağımlılık analizi nasıl yapılıyor?"]},
        {"area": "governance",
         "text": "Cloud governance modeli nasıl işliyor? CCoE (Cloud Center of Excellence) yapısı var mı?",
         "follow_ups": ["Cloud policy enforcement mekanizması nedir?", "Tagging/labeling standartları tanımlı mı?"]},
        {"area": "skills_organization",
         "text": "Ekiplerin cloud yetkinlik seviyesi nedir? Cloud skill gap analizi yapıldı mı?",
         "follow_ups": ["Sertifikasyon hedefleri var mı?", "External partner ile iç kapasite dengesi nasıl?"]},
    ],

    # ─── S3-AA-002: Ingestion (NiFi, Kafka, DataStage) ───────────────────────
    "ingestion": [
        {"area": "architecture",
         "text": "Veri ingestion mimarinizi açıklar mısınız? Hangi araçlar kullanılıyor (NiFi, Kafka, DataStage, Airbyte)?",
         "follow_ups": ["Batch mi streaming mi öncelikli?", "Real-time veri ihtiyaçları neler?"]},
        {"area": "sources",
         "text": "Kaç farklı kaynak sistemden veri alınıyor? En kritik kaynaklar hangileri?",
         "follow_ups": ["Kaynak sistemlerin API/CDC/file bazlı dağılımı nedir?", "Kaynak şema değişiklikleri nasıl yönetiliyor?"]},
        {"area": "throughput_latency",
         "text": "Günlük/saatlik veri hacmi ve gecikme gereksinimleri nelerdir?",
         "follow_ups": ["Peak load senaryoları nasıl handle ediliyor?", "SLA'lar tanımlı mı?"]},
        {"area": "data_quality",
         "text": "Ingestion sürecinde veri kalitesi kontrolleri nasıl yapılıyor?",
         "follow_ups": ["Rejection/quarantine mekanizması var mı?", "DQ metrikleri izleniyor mu?"]},
        {"area": "error_handling",
         "text": "Hata yönetimi ve yeniden deneme (retry) stratejisi nasıl tasarlanmış?",
         "follow_ups": ["Dead letter queue kullanılıyor mu?", "Alarm/alert mekanizması nedir?"]},
        {"area": "security",
         "text": "Veri aktarımı sırasında şifreleme ve erişim kontrolü nasıl sağlanıyor?",
         "follow_ups": ["Hassas veriler (PII) ingestion'da maskeleniyor mu?", "Audit log tutuluyor mu?"]},
        {"area": "monitoring",
         "text": "Ingestion pipeline'larının izlenmesi ve operasyonel yönetimi nasıl yapılıyor?",
         "follow_ups": ["Pipeline metadata/lineage takip ediliyor mu?", "Kapasite planlaması yapılıyor mu?"]},
        {"area": "cdc",
         "text": "Change Data Capture (CDC) kullanılıyor mu? Hangi sistemlerde ve nasıl?",
         "follow_ups": ["Debezium, Oracle GoldenGate gibi araçlar var mı?", "Binlog/WAL bazlı mı snapshot bazlı mı?"]},
    ],

    # ─── S3-AA-003: Teradata DR ───────────────────────────────────────────────
    "teradata_dr": [
        {"area": "architecture",
         "text": "Teradata ortamınızın mimarisini açıklar mısınız? Kaç node, hangi versiyon, hangi platform (on-prem/cloud)?",
         "follow_ups": ["Teradata Vantage mi yoksa legacy mi?", "Active-active mi active-passive mi?"]},
        {"area": "disaster_recovery",
         "text": "Teradata için DR stratejiniz nedir? RTO ve RPO hedefleri nelerdir?",
         "follow_ups": ["DR test sıklığı nedir?", "Failover prosedürü otomatik mi manuel mi?"]},
        {"area": "backup",
         "text": "Yedekleme stratejisi nedir? Tam yedek ve artımlı yedek sıklığı nedir?",
         "follow_ups": ["BAR (Backup and Restore) araçları kullanılıyor mu?", "Yedekler nerede saklanıyor?"]},
        {"area": "replication",
         "text": "Teradata replikasyon mekanizması (TDGSS, QueryGrid, DSA) nasıl yapılandırılmış?",
         "follow_ups": ["Cross-site replikasyon gecikme toleransı nedir?", "Replikasyon izleme mekanizması var mı?"]},
        {"area": "performance",
         "text": "Teradata performans yönetimi nasıl yapılıyor? TASM/TDWM kullanılıyor mu?",
         "follow_ups": ["Sorgu optimizasyon pratiği nedir?", "Büyük tablolar için partitioning stratejisi?"]},
        {"area": "migration_path",
         "text": "Teradata'dan modern lakehouse/cloud DW'a migrasyon planı var mı?",
         "follow_ups": ["Hangi workload'lar öncelikli taşınacak?", "Geçiş sürecinde paralel çalışma planı?"]},
        {"area": "workload",
         "text": "Teradata üzerinde kaç ETL job/query çalışıyor? Kritik iş akışları hangileri?",
         "follow_ups": ["Gece batch penceresine sığıyor mu?", "Uzun süren sorgu optimizasyonu yapılıyor mu?"]},
        {"area": "licensing_cost",
         "text": "Teradata lisans maliyeti ve yenileme planı nedir?",
         "follow_ups": ["Kapasite planlaması yapıldı mı?", "Cloud Teradata veya alternatif değerlendiriliyor mu?"]},
    ],

    # ─── S3-KA-001: Lakehouse (Migros/Databricks bağlamına göre güncellendi) ───
    # Ontoloji hizalaması: d:capability/lakehouse, d:gap/lakehouse-governance
    # Referans sistem: d:system/databricks (Databricks Delta Lake)
    "lakehouse": [
        {"area": "medallion_architecture",
         "text": "Databricks ortamınızda Bronze-Silver-Gold (medallion) katmanları nasıl tanımlanmış? Her katmanın sorumluluğu ve veri dönüşüm kuralları nelerdir?",
         "follow_ups": [
             "Bronze'dan Silver'a geçişte hangi temizleme ve zenginleştirme adımları uygulanıyor?",
             "Gold katmanında kaç iş alanına ait aggregate tablo var?",
             "Katmanlar arası SLA ve taze veri (freshness) gereksinimleri tanımlı mı?",
         ]},
        {"area": "unity_catalog_governance",
         "text": "Unity Catalog kullanılıyor mu? Catalog, schema ve tablo hiyerarşisi nasıl organize edilmiş? Erişim kontrolleri kim tarafından ve nasıl yönetiliyor?",
         "follow_ups": [
             "Row-level ve column-level güvenlik (dynamic views/masking) uygulanıyor mu?",
             "Veri sınıflandırma etiketleri (PII, hassas, genel) tanımlı mı?",
             "Service principal ve grup bazlı izin yönetimi uygulanıyor mu?",
         ]},
        {"area": "delta_lake_table_management",
         "text": "Delta Lake tablo yaşam döngüsü nasıl yönetiliyor? Z-ordering, liquid clustering veya OPTIMIZE komutları planlanmış ve otomatize edilmiş mi?",
         "follow_ups": [
             "VACUUM politikası nedir? Kaç günlük geçmişi saklıyor?",
             "Tablo versiyonlama ve time travel aktif olarak kullanılıyor mu?",
             "Büyük tablolar için partition stratejisi nedir?",
         ]},
        {"area": "teradata_migration",
         "text": "Teradata'dan Databricks'e migrasyon süreci nerede? Hangi iş yükleri taşındı, hangilerinin taşınması planlanıyor?",
         "follow_ups": [
             "SQL uyumluluk sorunları (Teradata BTEQ → Spark SQL) nasıl yönetiliyor?",
             "Migrasyon doğrulama (reconciliation) stratejisi nedir?",
             "Paralel çalışma (dual-run) süreci var mı ve ne kadar sürmesi bekleniyor?",
         ]},
        {"area": "streaming_integration",
         "text": "Kafka'dan Databricks'e gerçek zamanlı veri akışı var mı? Delta Live Tables veya Structured Streaming kullanılıyor mu?",
         "follow_ups": [
             "Exactly-once semantics nasıl garanti ediliyor?",
             "Stream-batch birleşik (unified) pipeline'lar var mı?",
             "Gecikme (latency) ve throughput SLA'ları nelerdir?",
         ]},
        {"area": "compute_cost_optimization",
         "text": "Databricks cluster yönetimi ve maliyet optimizasyonu nasıl yapılıyor? Spot instance, auto-terminate ve cluster policy kullanılıyor mu?",
         "follow_ups": [
             "DBU (Databricks Unit) harcaması nasıl izleniyor ve raporlanıyor?",
             "Photon engine aktif mi? Ne kadarlık hız kazanımı gözlemlendi?",
             "İş yükleri cluster türüne göre (All-Purpose vs Job Cluster) ayrıştırılmış mı?",
         ]},
        {"area": "data_quality_dlt",
         "text": "Databricks ortamında veri kalitesi nasıl ölçülüyor? Delta Live Tables expectations veya dbt tests kullanılıyor mu?",
         "follow_ups": [
             "Kalite kuralları ihlalinde pipeline durdurma mı yoksa karantina mı uygulanıyor?",
             "Veri kalitesi metrikleri (completeness, validity, consistency) merkezi olarak izleniyor mu?",
             "OpenMetadata ile veri kalitesi entegrasyonu planlandı mı?",
         ]},
        {"area": "bi_ml_integration",
         "text": "Lakehouse üzerinden Power BI, ML modelleri ve feature store entegrasyonu nasıl çalışıyor?",
         "follow_ups": [
             "Power BI Direct Lake modu mu yoksa import modu mu kullanılıyor?",
             "MLflow veya başka bir experiment tracking aracı bağlı mı?",
             "Feature store ile online serving entegrasyonu var mı?",
         ]},
    ],

    # ─── S3-AA-005: Governance ───────────────────────────────────────────────
    "governance": [
        {"area": "data_catalog",
         "text": "Veri kataloğu çözümünüz var mı? (Collibra, Alation, OpenMetadata, DataHub) Kaç veri varlığı kataloglandı?",
         "follow_ups": ["İş tanımları ve teknik metadatayı birleştirebiliyor musunuz?", "Kullanıcı benimseme oranı nedir?"]},
        {"area": "data_ownership",
         "text": "Veri sahipliği ve stewardship modeli nasıl tanımlı? Data owner, steward, custodian rolleri var mı?",
         "follow_ups": ["Sorumluluklar RACI ile belgelenmiş mi?", "Sahipsiz veri seti oranı nedir?"]},
        {"area": "data_quality",
         "text": "Kurumsal veri kalitesi yönetimi nasıl yapılıyor? Hangi DQ araçları kullanılıyor?",
         "follow_ups": ["DQ boyutları (doğruluk, bütünlük, tutarlılık) ölçülüyor mu?", "DQ SLA'ları tanımlı mı?"]},
        {"area": "lineage",
         "text": "Uçtan uca veri lineage nasıl izleniyor? Etki analizi yapılabiliyor mu?",
         "follow_ups": ["Lineage otomatik mi manuel mi?", "Downstream etkilerin tespiti ne kadar süre alıyor?"]},
        {"area": "master_data",
         "text": "Master Data Management (MDM) stratejiniz nedir? Golden record oluşturuluyor mu?",
         "follow_ups": ["Müşteri, ürün, konum masterleri var mı?", "MDM hub'ı hangi sistemlerle entegre?"]},
        {"area": "privacy_compliance",
         "text": "KVKK/GDPR uyum süreci nasıl yönetiliyor? Kişisel veri envanteri var mı?",
         "follow_ups": ["Silinme/unutulma talepleri nasıl karşılanıyor?", "Veri minimizasyonu prensibi uygulanıyor mu?"]},
        {"area": "access_control",
         "text": "Veriye erişim yönetimi nasıl kontrol ediliyor? Role-based access control uygulanıyor mu?",
         "follow_ups": ["Dinamik veri maskeleme var mı?", "Erişim audit log'ları tutulmakta mı?"]},
        {"area": "policy_enforcement",
         "text": "Veri politikaları nasıl tanımlanıyor ve hayata geçiriliyor?",
         "follow_ups": ["Politika ihlalleri nasıl tespit ediliyor?", "Otomatik politika uygulama araçları var mı?"]},
    ],

    # ─── S3-AA-006: Data Product ─────────────────────────────────────────────
    "data_product": [
        {"area": "strategy",
         "text": "Data product stratejiniz nedir? Data mesh yaklaşımı benimseniyor mu?",
         "follow_ups": ["Domain-oriented ownership uygulanıyor mu?", "Data product owner rolleri tanımlı mı?"]},
        {"area": "product_definition",
         "text": "Mevcut data product'larınızı tanımlar mısınız? Kaç data product publish edilmiş durumda?",
         "follow_ups": ["SLA'lar ve kalite garantileri var mı?", "Versioning stratejisi nasıl?"]},
        {"area": "discoverability",
         "text": "Data product'lar nasıl keşfedilebilir hale getiriliyor? Data marketplace veya portal var mı?",
         "follow_ups": ["Arama ve filtreleme yetenekleri yeterli mi?", "Kullanıcı deneyimi nasıl değerlendiriliyor?"]},
        {"area": "api_access",
         "text": "Data product'lara API erişimi nasıl sağlanıyor? REST, GraphQL, gRPC?",
         "follow_ups": ["API versioning ve backward compatibility yönetimi?", "Rate limiting uygulanıyor mu?"]},
        {"area": "quality_sla",
         "text": "Data product SLA'ları (freshness, availability, accuracy) nasıl ölçülüyor ve raporlanıyor?",
         "follow_ups": ["SLA ihlallerinde uyarı mekanizması var mı?", "Müşteri geri bildirim döngüsü nasıl?"]},
        {"area": "monetization",
         "text": "Data product'lar içeriden veya dışarıdan para kazandırma modeliniz var mı?",
         "follow_ups": ["Chargeback modeli uygulanıyor mu?", "External data marketplace planı?"]},
        {"area": "platform",
         "text": "Data product'ları oluşturmak için kullanılan platform ve araçlar nelerdir?",
         "follow_ups": ["Self-serve analytics yetenekleri var mı?", "CI/CD pipeline'ları veri ürünleri için nasıl?"]},
        {"area": "team_structure",
         "text": "Data product ekipleri nasıl organize edilmiş? Federated mi merkezi mi?",
         "follow_ups": ["Platform ekibi ile domain ekibi iş birliği nasıl?", "Yetkinlik transferi nasıl yapılıyor?"]},
    ],

    # ─── S3-AA-007: CDP (Customer Data Platform) ─────────────────────────────
    "cdp": [
        {"area": "platform_overview",
         "text": "CDP platformunuzu tanımlar mısınız? Hangi ürün kullanılıyor veya değerlendiriliyor?",
         "follow_ups": ["Packaged CDP mi composable CDP mi?", "Mevcut MarTech stack ile entegrasyon durumu?"]},
        {"area": "identity_resolution",
         "text": "Kimlik çözümleme (identity resolution) nasıl yapılıyor? Deterministic mi probabilistic mi?",
         "follow_ups": ["Kaç kaynaktan kimlik birleştiriliyor?", "Match rate ve doğruluk oranı nedir?"]},
        {"area": "data_sources",
         "text": "CDP'ye hangi kaynaklardan veri akıyor? (CRM, e-ticaret, mobil uygulama, POS, web analytics)",
         "follow_ups": ["Gerçek zamanlı event stream var mı?", "Offline veri (mağaza, çağrı merkezi) entegrasyonu?"]},
        {"area": "segmentation",
         "text": "Müşteri segmentasyonu nasıl yapılıyor? ML-based segmentler var mı?",
         "follow_ups": ["Segment güncellik (freshness) ne kadar?", "Segment sayısı ve karmaşıklığı?"]},
        {"area": "activation",
         "text": "CDP verisi hangi kanallara aktive ediliyor? (E-posta, push, ücretli medya, kişiselleştirme)",
         "follow_ups": ["Kanal bağlantıları (connectors) sayısı ve kapsamı?", "Real-time vs batch activation dağılımı?"]},
        {"area": "privacy_consent",
         "text": "KVKK uyum ve onay yönetimi CDP'de nasıl ele alınıyor?",
         "follow_ups": ["Opt-in/opt-out tercihleri gerçek zamanlı güncelleniyor mu?", "Veri silme talepleri nasıl karşılanıyor?"]},
        {"area": "analytics",
         "text": "CDP üzerinde müşteri analitiği nasıl yapılıyor? LTV, churn tahmin modelleri var mı?",
         "follow_ups": ["Attribution modelleme yapılıyor mu?", "A/B test altyapısı entegre mi?"]},
        {"area": "roi_measurement",
         "text": "CDP yatırım getirisi (ROI) nasıl ölçülüyor? Hangi KPI'lar izleniyor?",
         "follow_ups": ["Kişiselleştirme gelir etkisi ölçülüyor mu?", "CDP maliyeti vs kazanım analizi?"]},
    ],
}


async def seed_all(api_base_url: str) -> dict:
    """Seed all workstream question banks via the REST API."""
    import httpx
    results = {}
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30) as client:
        for workstream, questions in QUESTION_BANKS.items():
            payload = {
                "workstream": workstream,
                "replace": True,
                "questions": [
                    {
                        "workstream": workstream,
                        "area": q["area"],
                        "text": q["text"],
                        "follow_ups": q.get("follow_ups"),
                        "order": i + 1,
                        "is_active": True,
                    }
                    for i, q in enumerate(questions)
                ],
            }
            resp = await client.post("/api/v1/question-bank/bulk", json=payload)
            results[workstream] = resp.json() if resp.status_code == 201 else {"error": resp.text}
    return results
