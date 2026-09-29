export interface Agent {
  id: string
  hostname: string
  os: 'windows' | 'linux' | 'darwin'
  ip_address?: string
  status: 'online' | 'offline' | 'busy'
  version?: string
  cert_fingerprint?: string
  tags: string[]
  last_seen: string
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

export interface Job {
  id: string
  script_id?: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  target_agents: string[]
  created_at: string
  completed_at?: string
}

export interface Artifact {
  id: string
  job_id: string
  agent_id: string
  type: string
  data: Record<string, unknown>
  collected_at: string
}

export interface Detection {
  id: string
  job_id?: string
  agent_id: string
  rule: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  evidence: Record<string, unknown>
  explanation?: string
  detected_at: string
}

export interface HealthStatus {
  status: string
  service: string
  version?: string
}
