{{- define "idea-board.labels" -}}
app.kubernetes.io/name: idea-board
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "idea-board.backend.labels" -}}
{{ include "idea-board.labels" . }}
app.kubernetes.io/component: backend
{{- end -}}

{{- define "idea-board.frontend.labels" -}}
{{ include "idea-board.labels" . }}
app.kubernetes.io/component: frontend
{{- end -}}
