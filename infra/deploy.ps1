# AAKP - Sprint 0 Deploy Script
# Run from: infra/ directory
# Usage: .\deploy.ps1 [-Action <step>]
# Steps: repos | namespaces | rbac | data | information | knowledge | agent | gateway | monitoring | healthcheck | all

param(
    [string]$Action = "all"
)

$ErrorActionPreference = "Stop"
$InfraDir = $PSScriptRoot

function Write-Step { param([string]$Msg) Write-Host "`n=== $Msg ===" -ForegroundColor Cyan }
function Write-OK   { param([string]$Msg) Write-Host "OK  $Msg" -ForegroundColor Green }
function Write-Info { param([string]$Msg) Write-Host "    $Msg" -ForegroundColor Gray }

function Step-Repos {
    Write-Step "Adding Helm repositories"
    helm repo add bitnami              https://charts.bitnami.com/bitnami
    helm repo add kong                 https://charts.konghq.com
    helm repo add qdrant               https://qdrant.github.io/qdrant-helm
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo add grafana              https://grafana.github.io/helm-charts
    helm repo add langfuse             https://langfuse.com/helm/charts
    helm repo update
    Write-OK "Helm repos ready"
}

function Step-Namespaces {
    Write-Step "Creating namespaces"
    kubectl apply -f "$InfraDir\namespaces\namespaces.yaml"
    Write-OK "6 namespaces created"
}

function Step-RBAC {
    Write-Step "Applying RBAC policies"
    kubectl apply -f "$InfraDir\rbac\rbac.yaml"
    Write-OK "RBAC applied"
}

function Step-Data {
    Write-Step "Deploying Data Layer (MinIO + Kafka) -> aakp-data"
    Write-Info "MinIO..."
    helm upgrade --install aakp-minio bitnami/minio `
        -n aakp-data `
        -f "$InfraDir\helm\data-layer\minio-values.yaml" `
        --wait --timeout 5m
    Write-Info "Kafka (KRaft)..."
    helm upgrade --install aakp-kafka bitnami/kafka `
        -n aakp-data `
        -f "$InfraDir\helm\data-layer\kafka-values.yaml" `
        --wait --timeout 10m
    Write-OK "Data layer deployed"
}

function Step-Information {
    Write-Step "Deploying Information Layer (PostgreSQL + Qdrant) -> aakp-information"
    Write-Info "PostgreSQL..."
    helm upgrade --install aakp-postgresql bitnami/postgresql `
        -n aakp-information `
        -f "$InfraDir\helm\information-layer\postgresql-values.yaml" `
        --wait --timeout 5m
    Write-Info "Qdrant..."
    helm upgrade --install aakp-qdrant qdrant/qdrant `
        -n aakp-information `
        -f "$InfraDir\helm\information-layer\qdrant-values.yaml" `
        --wait --timeout 5m
    Write-OK "Information layer deployed"
}

function Step-Knowledge {
    Write-Step "Deploying Knowledge Layer (Apache Jena Fuseki) -> aakp-knowledge"
    helm upgrade --install aakp-fuseki "$InfraDir\helm\knowledge-layer" `
        -n aakp-knowledge `
        --wait --timeout 5m
    Write-OK "Knowledge layer deployed"
}

function Step-Agent {
    Write-Step "Deploying Agent Layer (Redis) -> aakp-agent"
    helm upgrade --install aakp-redis bitnami/redis `
        -n aakp-agent `
        -f "$InfraDir\helm\agent-layer\redis-values.yaml" `
        --wait --timeout 5m
    Write-OK "Agent layer deployed"
}

function Step-Gateway {
    Write-Step "Deploying Kong Gateway -> aakp-gateway"
    helm upgrade --install aakp-kong kong/kong `
        -n aakp-gateway `
        -f "$InfraDir\gateway\kong-values.yaml" `
        --wait --timeout 5m
    Write-OK "Kong Gateway deployed — proxy on NodePort 30080"
}

function Step-Monitoring {
    Write-Step "Deploying Monitoring Stack -> aakp-monitoring"
    Write-Info "Prometheus + Grafana (kube-prometheus-stack)..."
    helm upgrade --install aakp-prometheus prometheus-community/kube-prometheus-stack `
        -n aakp-monitoring `
        -f "$InfraDir\helm\monitoring\prometheus-values.yaml" `
        --wait --timeout 10m
    Write-Info "Loki (log aggregation)..."
    helm upgrade --install aakp-loki grafana/loki `
        -n aakp-monitoring `
        -f "$InfraDir\helm\monitoring\loki-values.yaml" `
        --wait --timeout 5m
    Write-Info "Tempo (distributed tracing)..."
    helm upgrade --install aakp-tempo grafana/tempo `
        -n aakp-monitoring `
        -f "$InfraDir\helm\monitoring\tempo-values.yaml" `
        --wait --timeout 5m
    Write-Info "LangFuse (LLM observability)..."
    helm upgrade --install aakp-langfuse langfuse/langfuse `
        -n aakp-monitoring `
        -f "$InfraDir\helm\monitoring\langfuse-values.yaml" `
        --wait --timeout 5m
    Write-OK "Monitoring stack deployed — Grafana on NodePort 30300, LangFuse on 30333"
}

function Step-Healthcheck {
    Write-Step "Healthcheck — pod status"
    kubectl get pods -A --field-selector=status.phase!=Running 2>$null | Where-Object { $_ -match "aakp" }
    Write-Host ""
    kubectl get pods -n aakp-data
    Write-Host ""
    kubectl get pods -n aakp-information
    Write-Host ""
    kubectl get pods -n aakp-knowledge
    Write-Host ""
    kubectl get pods -n aakp-agent
    Write-Host ""
    kubectl get pods -n aakp-gateway
    Write-Host ""
    kubectl get pods -n aakp-monitoring
}

switch ($Action) {
    "repos"       { Step-Repos }
    "namespaces"  { Step-Namespaces }
    "rbac"        { Step-RBAC }
    "data"        { Step-Data }
    "information" { Step-Information }
    "knowledge"   { Step-Knowledge }
    "agent"       { Step-Agent }
    "gateway"     { Step-Gateway }
    "monitoring"  { Step-Monitoring }
    "healthcheck" { Step-Healthcheck }
    "all" {
        Step-Repos
        Step-Namespaces
        Step-RBAC
        Step-Data
        Step-Information
        Step-Knowledge
        Step-Agent
        Step-Gateway
        Step-Monitoring
        Step-Healthcheck
        Write-Host "`nSprint 0 complete." -ForegroundColor Green
    }
    default {
        Write-Host "Usage: .\deploy.ps1 -Action [repos|namespaces|rbac|data|information|knowledge|agent|gateway|monitoring|healthcheck|all]"
    }
}
