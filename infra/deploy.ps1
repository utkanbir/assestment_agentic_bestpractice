# AAKP - Deploy Script (Sprint 0 + Sprint 1)
# Usage: .\deploy.ps1 -Action <step>
# Steps: repos | namespaces | rbac | data | information | knowledge | agent | gateway | monitoring | services | ingress | healthcheck | all

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
    helm repo add minio-official       https://charts.min.io/
    helm repo add kong                 https://charts.konghq.com
    helm repo add qdrant               https://qdrant.github.io/qdrant-helm
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo add grafana              https://grafana.github.io/helm-charts
    helm repo add strimzi              https://strimzi.io/charts/
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
    Write-Info "MinIO (official chart)..."
    helm upgrade --install aakp-minio minio-official/minio `
        -n aakp-data `
        -f "$InfraDir\helm\data-layer\minio-values.yaml" `
        --wait --timeout 5m
    Write-Info "Kafka (official apache/kafka image)..."
    kubectl apply -f "$InfraDir\helm\data-layer\kafka-manifest.yaml"
    Write-OK "Data layer deployed"
}

function Step-Information {
    Write-Step "Deploying Information Layer (PostgreSQL + Qdrant) -> aakp-information"
    Write-Info "PostgreSQL (official image)..."
    kubectl apply -f "$InfraDir\helm\information-layer\postgresql-manifest.yaml"
    Write-Info "Qdrant (official chart)..."
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
    kubectl apply -f "$InfraDir\helm\agent-layer\redis-manifest.yaml"
    Write-OK "Agent layer deployed"
}

function Step-Gateway {
    Write-Step "Deploying Kong Gateway -> aakp-gateway"
    helm upgrade --install aakp-kong kong/kong `
        -n aakp-gateway `
        -f "$InfraDir\gateway\kong-values.yaml" `
        --skip-crds `
        --wait --timeout 5m
    Write-OK "Kong Gateway deployed - proxy on NodePort 30080"
}

function Step-Monitoring {
    Write-Step "Deploying Monitoring Stack -> aakp-monitoring"
    Write-Info "Prometheus + Grafana (kube-prometheus-stack)..."
    helm upgrade --install aakp-prometheus prometheus-community/kube-prometheus-stack `
        -n aakp-monitoring `
        -f "$InfraDir\helm\monitoring\prometheus-values.yaml" `
        --timeout 10m
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
    Write-OK "Monitoring stack deployed - Grafana on NodePort 30300"
    Write-Info "NOTE: LangFuse deferred to Sprint 1 (requires ghcr.io auth + PostgreSQL wiring)"
}

function Step-Services {
    Write-Step "Deploying AAKP Services (API + MCP Server + K8s Agent) -> Sprint 1"
    Write-Info "FastAPI + MCP Server (aakp-information)..."
    kubectl apply -f "$InfraDir\helm\information-layer\api-manifest.yaml"
    Write-Info "Kubernetes Agent (aakp-agent)..."
    kubectl apply -f "$InfraDir\helm\agent-layer\kubernetes-agent-manifest.yaml"
    Write-OK "Services deployed - waiting for pods..."
    kubectl rollout status deployment/aakp-api -n aakp-information --timeout=120s
    kubectl rollout status deployment/aakp-kubernetes-agent -n aakp-agent --timeout=120s
}

function Step-Ingress {
    Write-Step "Applying Kong Ingress rules"
    kubectl apply -f "$InfraDir\gateway\kong-ingress.yaml"
    Write-OK "Ingress rules applied - API available at http://localhost:30080/api/v1/health"
}

function Step-Healthcheck {
    Write-Step "Healthcheck - pod status"
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
    "services"    { Step-Services }
    "ingress"     { Step-Ingress }
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
    "sprint1" {
        Step-Services
        Step-Ingress
        Step-Healthcheck
        Write-Host "`nSprint 1 services deployed." -ForegroundColor Green
    }
    default {
        Write-Host "Usage: .\deploy.ps1 -Action [repos|namespaces|rbac|data|information|knowledge|agent|gateway|monitoring|services|ingress|healthcheck|all|sprint1]"
    }
}
