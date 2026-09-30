export interface Agent {
  id: string
  hostname: string
  os: 'windows' | 'linux' | 'darwin' | string
  ip_address?: string
  status: 'online' | 'offline' | 'busy' | 'enrolled' | string
  version?: string
  cert_fingerprint?: string
  tags: string[]
  last_seen: string
}

export interface AgentListResponse {
  total: number
  items: Agent[]
}

export interface JockyScript {
  id: string
  name: string
  description?: string
  body: string
  created_by: string
  created_at: string
  updated_at: string
}

export interface ScriptValidateResponse {
  valid: boolean
  ast_summary?: {
    statements?: number
    plan_version?: string
    [key: string]: unknown
  }
  estimated_artifacts: string[]
  errors: string[]
}

export interface Job {
  id: string
  script_id?: string
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | string
  target_agents: string[]
  plan?: {
    plan_version?: string
    collectors?: Array<{ target: string; [key: string]: unknown }>
    checks?: Array<Record<string, unknown>>
    [key: string]: unknown
  }
  created_at: string
  completed_at?: string
}

export interface JobCreatePayload {
  script_id?: string
  script_body?: string
  target_agent_ids: string[]
  target_tags?: string[]
}

export interface JobCreateResponse {
  job_id: string
  status: string
  agent_count: number
  created_at: string
}

export interface Artifact {
  id: string
  job_id: string
  agent_id: string
  type: 'process' | 'connection' | 'autorun' | 'scheduled_task' | 'user' | 'session' | string
  data: Record<string, any>
  collected_at: string
}

export interface ArtifactListResponse {
  total: number
  items: Artifact[]
}

export interface EvidenceReference {
  artifact_id: string
  type: string
  details?: Record<string, any>
}

export interface Detection {
  id: string
  agent_id: string
  job_id?: string
  severity: 'low' | 'medium' | 'high' | 'critical' | string
  title: string
  description?: string
  rule_id: string
  status: 'open' | 'acknowledged' | 'resolved' | 'false_positive' | string
  evidence: EvidenceReference[]
  created_at: string
}

export interface DetectionListResponse {
  total: number
  items: Detection[]
}

export interface HealthStatus {
  status: string
  service: string
  version?: string
  timestamp?: string
}

export interface WebSocketMessage {
  event: 'connected' | 'artifact_collected' | 'threat_detected' | 'job_status' | 'error' | string
  job_id?: string
  agent_id?: string
  message?: string
  timestamp?: string
  status?: string
  payload?: any
  detection?: Detection
}
