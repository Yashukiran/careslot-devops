{{- define "careslot.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{- define "careslot.labels" -}}
app.kubernetes.io/part-of: {{ include "careslot.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{/* selector labels for one component: backend / frontend / postgres */}}
{{- define "careslot.selectorLabels" -}}
app.kubernetes.io/name: {{ .component }}
app.kubernetes.io/instance: {{ .root.Release.Name }}
{{- end -}}

{{- define "careslot.fullname" -}}
{{- printf "%s-%s" .root.Release.Name .component | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "careslot.dbHost" -}}
{{- printf "%s-postgres" .Release.Name -}}
{{- end -}}
