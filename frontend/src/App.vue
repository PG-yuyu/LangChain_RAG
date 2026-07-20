<script setup>
import { computed, onMounted, ref } from 'vue'
import { askQuestion, healthCheck, listDocuments, uploadDocument } from './api'

const knowledgeBaseId = 'kb_demo'
const sessionId = `session_${Math.random().toString(16).slice(2, 14)}`

const authMode = ref('login')
const authMessage = ref('')
const currentUser = ref(localStorage.getItem('rag_current_user') || '')
const authForm = ref({
  username: '',
  password: ''
})
const documents = ref([])
const selectedDocumentIds = ref([])
const uploadStatus = ref('点击文件可加入本次 RAG 知识库。')
const fileInput = ref(null)
const health = ref('连接中')
const question = ref('')
const isUploading = ref(false)
const isAsking = ref(false)
const messages = ref([
  {
    role: 'assistant',
    content: '上传并选择左侧文件后，在底部输入问题开始检索问答。'
  }
])
const conversations = ref([])
const activeConversationId = ref('')

const selectedCount = computed(() => selectedDocumentIds.value.length)
const isAuthed = computed(() => Boolean(currentUser.value))
const historyKey = computed(() => `rag_conversations_${currentUser.value || 'guest'}`)

onMounted(async () => {
  await Promise.all([refreshHealth(), refreshDocuments()])
  if (currentUser.value) {
    loadConversations()
  }
})

async function refreshHealth() {
  try {
    const result = await healthCheck()
    health.value = result.status
  } catch (error) {
    health.value = 'offline'
  }
}

async function refreshDocuments() {
  documents.value = await listDocuments(knowledgeBaseId)
}

async function onFileChange(event) {
  const files = Array.from(event.target.files || [])
  event.target.value = ''
  if (!files.length) {
    uploadStatus.value = '请先选择要上传的文件。'
    return
  }

  isUploading.value = true
  uploadStatus.value = '正在上传并处理文档...'
  try {
    for (const file of files) {
      const document = await uploadDocument(file, knowledgeBaseId)
      if (!selectedDocumentIds.value.includes(document.document_id)) {
        selectedDocumentIds.value = [...selectedDocumentIds.value, document.document_id]
      }
    }
    uploadStatus.value = '上传成功，点击文件可加入本次 RAG 知识库。'
    await refreshDocuments()
  } catch (error) {
    uploadStatus.value = `上传失败：${error.message}`
  } finally {
    isUploading.value = false
  }
}

function openFilePicker() {
  fileInput.value?.click()
}

function toggleDocument(documentId) {
  if (selectedDocumentIds.value.includes(documentId)) {
    selectedDocumentIds.value = selectedDocumentIds.value.filter((id) => id !== documentId)
  } else {
    selectedDocumentIds.value = [...selectedDocumentIds.value, documentId]
  }
}

function toggleAllDocuments() {
  if (selectedDocumentIds.value.length === documents.value.length) {
    selectedDocumentIds.value = []
  } else {
    selectedDocumentIds.value = documents.value.map((doc) => doc.document_id)
  }
}

async function sendQuestion() {
  const text = question.value.trim()
  if (!text || isAsking.value) return

  messages.value.push({ role: 'user', content: text })
  question.value = ''
  isAsking.value = true

  try {
    const response = await askQuestion({
      query: text,
      session_id: sessionId,
      knowledge_base_id: knowledgeBaseId,
      selected_document_ids: selectedDocumentIds.value,
      top_k: 5,
      max_hops: 2,
      enable_query_rewrite: true
    })
    messages.value.push({
      role: 'assistant',
      content: response.answer
    })
    saveActiveConversation(text)
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      content: `请求失败：${error.message}`
    })
    saveActiveConversation(text)
  } finally {
    isAsking.value = false
  }
}

function handleKeydown(event) {
  if (event.ctrlKey && event.key === 'Enter') {
    sendQuestion()
  }
}

function switchAuthMode(mode) {
  authMode.value = mode
  authMessage.value = ''
}

function submitAuth() {
  const username = authForm.value.username.trim()
  const password = authForm.value.password.trim()

  if (!username || !password) {
    authMessage.value = '请输入用户名和密码。'
    return
  }

  if (password.length < 6) {
    authMessage.value = '密码长度不能小于 6 位。'
    return
  }

  const users = JSON.parse(localStorage.getItem('rag_users') || '{}')

  if (authMode.value === 'register') {
    if (users[username]) {
      authMessage.value = '该用户名已注册。'
      return
    }
    users[username] = { password }
    localStorage.setItem('rag_users', JSON.stringify(users))
    localStorage.setItem('rag_current_user', username)
    currentUser.value = username
    loadConversations()
    authMessage.value = ''
    return
  }

  if (!users[username] || users[username].password !== password) {
    authMessage.value = '用户名或密码错误。'
    return
  }

  localStorage.setItem('rag_current_user', username)
  currentUser.value = username
  loadConversations()
  authMessage.value = ''
}

function logout() {
  localStorage.removeItem('rag_current_user')
  currentUser.value = ''
  conversations.value = []
  activeConversationId.value = ''
  authForm.value.password = ''
}

function defaultMessages() {
  return [
    {
      role: 'assistant',
      content: '上传并选择左侧文件后，在底部输入问题开始检索问答。'
    }
  ]
}

function loadConversations() {
  conversations.value = JSON.parse(localStorage.getItem(historyKey.value) || '[]')
  if (conversations.value.length) {
    openConversation(conversations.value[0].id)
  } else {
    newConversation()
  }
}

function persistConversations() {
  localStorage.setItem(historyKey.value, JSON.stringify(conversations.value))
}

function newConversation() {
  const conversation = {
    id: `conv_${Date.now()}`,
    title: '新建对话',
    updatedAt: new Date().toLocaleString(),
    messages: defaultMessages()
  }
  conversations.value = [conversation, ...conversations.value]
  activeConversationId.value = conversation.id
  messages.value = conversation.messages.map((item) => ({ ...item }))
  persistConversations()
}

function openConversation(conversationId) {
  const conversation = conversations.value.find((item) => item.id === conversationId)
  if (!conversation) return
  activeConversationId.value = conversation.id
  messages.value = conversation.messages.map((item) => ({ ...item }))
}

function saveActiveConversation(latestQuestion = '') {
  if (!activeConversationId.value) {
    newConversation()
  }

  const title = latestQuestion.slice(0, 20) || '新建对话'
  conversations.value = conversations.value.map((item) => {
    if (item.id !== activeConversationId.value) return item
    return {
      ...item,
      title: item.title === '新建对话' ? title : item.title,
      updatedAt: new Date().toLocaleString(),
      messages: messages.value.map((message) => ({ ...message }))
    }
  })
  persistConversations()
}
</script>

<template>
  <div v-if="!isAuthed" class="auth-page">
    <div class="auth-panel">
      <div class="auth-brand">
        <div class="brand">GraphRAG</div>
        <p>基于 LangChain + GraphDB 的 RAG 文档问答系统</p>
      </div>

      <div class="auth-switch">
        <button :class="{ active: authMode === 'login' }" @click="switchAuthMode('login')">登录</button>
        <button :class="{ active: authMode === 'register' }" @click="switchAuthMode('register')">注册</button>
      </div>

      <form class="auth-form" @submit.prevent="submitAuth">
        <label>
          用户名
          <input v-model="authForm.username" placeholder="请输入用户名" />
        </label>
        <label>
          密码
          <input v-model="authForm.password" placeholder="至少 6 位" type="password" />
        </label>
        <p v-if="authMessage" class="auth-error">{{ authMessage }}</p>
        <button type="submit">{{ authMode === 'login' ? '登录' : '注册并登录' }}</button>
      </form>
    </div>
  </div>

  <div v-else class="app-shell">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div>
          <div class="brand">GraphRAG</div>
          <div class="sub-brand">文档知识库</div>
        </div>
        <button class="logout-pill" @click="logout">退出登录</button>
      </div>

      <section class="library-card" :class="{ 'has-files': documents.length }">
        <input
          ref="fileInput"
          class="hidden-file-input"
          type="file"
          multiple
          accept=".pdf,.docx,.txt,.md"
          @change="onFileChange"
        />

        <div class="uploaded-panel">
          <button class="new-chat-btn" @click="newConversation">新建对话</button>

          <div class="dashed-box history-box">
            <div class="history-title">对话历史</div>
            <div class="history-list">
              <button
                v-for="conversation in conversations"
                :key="conversation.id"
                class="history-item"
                :class="{ active: activeConversationId === conversation.id }"
                @click="openConversation(conversation.id)"
              >
                <strong>{{ conversation.title }}</strong>
                <span>{{ conversation.updatedAt }}</span>
              </button>
            </div>
          </div>

          <div class="dashed-box files-box">
            <div class="section-title">
              <span>已上传文件</span>
              <small>{{ selectedCount }} 个已选择</small>
            </div>

            <div class="file-list">
              <button
                class="file-item all-files"
                :class="{ active: documents.length && selectedDocumentIds.length === documents.length }"
                @click="toggleAllDocuments"
              >
                <span
                  class="checkbox"
                  :class="{ checked: documents.length && selectedDocumentIds.length === documents.length }"
                ></span>
                <span class="file-meta">
                  <strong>所有文件</strong>
                </span>
              </button>
              <button
                v-for="doc in documents"
                :key="doc.document_id"
                class="file-item"
                :class="{ active: selectedDocumentIds.includes(doc.document_id) }"
                @click="toggleDocument(doc.document_id)"
              >
                <span class="checkbox" :class="{ checked: selectedDocumentIds.includes(doc.document_id) }"></span>
            <span class="file-meta">
              <strong>{{ doc.filename }}</strong>
            </span>
          </button>
            </div>
          </div>
        </div>

        <div class="status">{{ uploadStatus }}</div>
        <button class="upload-action" :disabled="isUploading" @click="openFilePicker">
          {{ isUploading ? '上传中...' : '上传文件' }}
        </button>
      </section>
    </aside>

    <main class="main">
      <header class="topbar">
        <div class="title-group">
          <h1>RAG 文档问答</h1>
        </div>

        <div class="right-controls">
          <div class="info-card user-only">
            <span>用户名</span>
            <strong>{{ currentUser }}</strong>
          </div>
          <div class="info-card">
            <span>知识库</span>
            <strong>{{ knowledgeBaseId }}</strong>
          </div>
          <div class="info-card status-card">
            <span>运行状态</span>
            <strong>{{ health }}</strong>
          </div>
        </div>
      </header>

      <section class="chat-area">
        <div class="messages">
          <div
            v-for="(message, index) in messages"
            :key="index"
            class="message-row"
            :class="message.role"
          >
            <div v-if="message.role === 'assistant'" class="avatar">AI</div>
            <div class="bubble">{{ message.content }}</div>
            <div v-if="message.role === 'user'" class="avatar user-avatar">我</div>
          </div>
        </div>
      </section>

      <footer class="composer">
        <textarea
          v-model="question"
          placeholder="输入消息，Ctrl + Enter 发送"
          @keydown="handleKeydown"
        ></textarea>
        <button class="send-btn" :disabled="isAsking" @click="sendQuestion">
          {{ isAsking ? '生成中' : '发送' }}
        </button>
      </footer>
    </main>
  </div>
</template>
