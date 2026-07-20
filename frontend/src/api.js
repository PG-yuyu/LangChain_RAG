const API_BASE = ''

export async function healthCheck() {
  const response = await fetch(`${API_BASE}/api/health`)
  return readJson(response)
}

export async function listDocuments(knowledgeBaseId = 'kb_demo') {
  const response = await fetch(`${API_BASE}/api/documents?knowledge_base_id=${encodeURIComponent(knowledgeBaseId)}`)
  return readJson(response)
}

export async function uploadDocument(file, knowledgeBaseId = 'kb_demo') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('knowledge_base_id', knowledgeBaseId)

  const response = await fetch(`${API_BASE}/api/documents/upload`, {
    method: 'POST',
    body: formData
  })
  return readJson(response)
}

export async function askQuestion(payload) {
  const response = await fetch(`${API_BASE}/api/answer`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })
  return readJson(response)
}

async function readJson(response) {
  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.detail || data.message || '请求失败')
  }
  return data
}

