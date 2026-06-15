# AAKP - Docker Image Build Script (Sprint 1)
# Builds all service images into the local Docker daemon shared with Docker Desktop K8s
# Usage: .\build.ps1 [-Service <name>] [-Tag <tag>]
# Service: api | mcp-server | kubernetes-agent | all (default)

param(
    [string]$Service = "all",
    [string]$Tag     = "latest"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent

function Write-Step { param([string]$Msg) Write-Host "`n=== $Msg ===" -ForegroundColor Cyan }
function Write-OK   { param([string]$Msg) Write-Host "OK  $Msg" -ForegroundColor Green }

function Build-Api {
    Write-Step "Building aakp/api:$Tag"
    docker build -t "aakp/api:$Tag" "$Root\services\api"
    Write-OK "aakp/api:$Tag ready"
}

function Build-McpServer {
    Write-Step "Building aakp/mcp-server:$Tag"
    docker build -t "aakp/mcp-server:$Tag" "$Root\services\mcp-server"
    Write-OK "aakp/mcp-server:$Tag ready"
}

function Build-KubernetesAgent {
    Write-Step "Building aakp/kubernetes-agent:$Tag"
    docker build -t "aakp/kubernetes-agent:$Tag" "$Root\agents\kubernetes-agent"
    Write-OK "aakp/kubernetes-agent:$Tag ready"
}

function Build-Frontend {
    Write-Step "Building aakp/frontend:$Tag"
    docker build -t "aakp/frontend:$Tag" "$Root\frontend"
    Write-OK "aakp/frontend:$Tag ready"
}

switch ($Service) {
    "api"                { Build-Api }
    "mcp-server"         { Build-McpServer }
    "kubernetes-agent"   { Build-KubernetesAgent }
    "frontend"           { Build-Frontend }
    "all" {
        Build-Api
        Build-McpServer
        Build-KubernetesAgent
        Build-Frontend
        Write-Host "`nAll images built." -ForegroundColor Green
        Write-Host "Images are available to Docker Desktop K8s without push (shared daemon)." -ForegroundColor Gray
    }
    default {
        Write-Host "Usage: .\build.ps1 [-Service api|mcp-server|kubernetes-agent|frontend|all] [-Tag latest]"
    }
}
