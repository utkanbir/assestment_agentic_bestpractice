{{- define "aakp-fuseki.name" -}}
{{- "aakp-fuseki" }}
{{- end }}

{{- define "aakp-fuseki.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/name: fuseki
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: aakp
{{- end }}

{{- define "aakp-fuseki.selectorLabels" -}}
app.kubernetes.io/name: fuseki
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
