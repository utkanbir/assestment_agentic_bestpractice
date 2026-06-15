# Deploy AAKP Ontology v0.2 to Fuseki
# Usage: .\deploy-ontology.ps1 [-FusekiUrl http://localhost:3030] [-Dataset aakp]

param(
    [string]$FusekiUrl = "http://localhost:3030",
    [string]$Dataset   = "aakp",
    [switch]$PortForward
)

$OntologyDir = "$PSScriptRoot\ontology"
$GraphBase   = "https://aakp.ai/graph"

$files = @(
    @{ file = "assessment.ttl";   graph = "$GraphBase/assessment"   },
    @{ file = "architecture.ttl"; graph = "$GraphBase/architecture" },
    @{ file = "maturity.ttl";     graph = "$GraphBase/maturity"     },
    @{ file = "organization.ttl"; graph = "$GraphBase/organization" }
)

if ($PortForward) {
    Write-Host "Port-forwarding Fuseki 3030..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "kubectl port-forward svc/aakp-fuseki 3030:3030 -n aakp-knowledge"
    Start-Sleep -Seconds 3
}

foreach ($entry in $files) {
    $path  = "$OntologyDir\$($entry.file)"
    $graph = $entry.graph
    $url   = "$FusekiUrl/$Dataset/data?graph=$graph"

    Write-Host "Uploading $($entry.file) -> $graph" -ForegroundColor Cyan
    try {
        $response = Invoke-RestMethod -Method Put -Uri $url `
            -InFile $path `
            -ContentType "text/turtle; charset=utf-8"
        Write-Host "  OK" -ForegroundColor Green
    } catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
    }
}

Write-Host "`nVerifying named graphs..." -ForegroundColor Cyan
$sparql = "SELECT ?g (COUNT(*) AS ?triples) WHERE { GRAPH ?g { ?s ?p ?o } FILTER(STRSTARTS(STR(?g), '$GraphBase')) } GROUP BY ?g"
$verify = Invoke-RestMethod -Method Get `
    -Uri "$FusekiUrl/$Dataset/sparql?query=$([Uri]::EscapeDataString($sparql))" `
    -Headers @{ Accept = "application/sparql-results+json" }

foreach ($result in $verify.results.bindings) {
    Write-Host "  $($result.g.value): $($result.triples.value) triples" -ForegroundColor Green
}
