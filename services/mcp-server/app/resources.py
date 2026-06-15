KUBERNETES_QUESTION_BANK = [
    {
        "id": "k8s-001",
        "area": "cluster_architecture",
        "text": "Mevcut Kubernetes cluster mimarinizi açıklar mısınız? Kaç node var, hangi Kubernetes versiyonu kullanılıyor?",
        "follow_ups": ["Node tipleri neler (master/worker)?", "Managed mi (EKS/GKE/AKS) yoksa self-hosted mı?"],
    },
    {
        "id": "k8s-002",
        "area": "workload_management",
        "text": "Hangi workload tipleri çalışıyor? (Deployment, StatefulSet, DaemonSet, Job/CronJob)",
        "follow_ups": ["Stateful uygulamalar nasıl yönetiliyor?", "PersistentVolume stratejisi nedir?"],
    },
    {
        "id": "k8s-003",
        "area": "networking",
        "text": "CNI plugin olarak ne kullanıyorsunuz? NetworkPolicy tanımlı mı?",
        "follow_ups": ["Service mesh var mı (Istio/Linkerd)?", "Ingress controller nedir?"],
    },
    {
        "id": "k8s-004",
        "area": "security",
        "text": "RBAC politikaları nasıl tanımlanmış? Pod Security Standards uygulanıyor mu?",
        "follow_ups": ["Secret yönetimi nasıl yapılıyor?", "Image scanning süreci var mı?"],
    },
    {
        "id": "k8s-005",
        "area": "observability",
        "text": "Cluster ve workload metrikleri nasıl izleniyor? Hangi observability stack kullanılıyor?",
        "follow_ups": ["Log aggregation çözümü nedir?", "Alert mekanizması var mı?"],
    },
    {
        "id": "k8s-006",
        "area": "capacity",
        "text": "Resource request/limit tanımları yapılmış mı? HPA/VPA kullanılıyor mu?",
        "follow_ups": ["Cluster autoscaler aktif mi?", "Resource quota namespace bazında tanımlı mı?"],
    },
    {
        "id": "k8s-007",
        "area": "disaster_recovery",
        "text": "etcd yedekleme stratejisi nedir? Cluster restore prosedürü test edildi mi?",
        "follow_ups": ["RTO ve RPO hedefleri nedir?", "Multi-region/AZ dağılımı var mı?"],
    },
    {
        "id": "k8s-008",
        "area": "cicd",
        "text": "Deployment pipeline nasıl çalışıyor? GitOps (ArgoCD/Flux) kullanılıyor mu?",
        "follow_ups": ["Rollback süreci nasıl işliyor?", "Blue/green veya canary deployment var mı?"],
    },
]
