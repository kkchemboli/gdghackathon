// API Service for EdTube Features - Python Backend Compatible
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api' // Update with your Python backend URL

// Helper function for API requests
const apiRequest = async (url, options = {}) => {
  const defaultHeaders = {
    'Content-Type': 'application/json',
    // Add authentication token if needed
    // 'Authorization': `Bearer ${localStorage.getItem('token')}`
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      }
    })

    if (!response.ok) {
      throw new Error(`HTTP Error: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error('API Request Error:', error)
    throw error
  }
}

// Quiz API
export const fetchQuiz = async (videoId) => {
  try {
    const data = await apiRequest(`${API_BASE_URL}/quiz/${videoId}`)
    return data
  } catch (error) {
    console.error('Quiz Error:', error)
    throw error
  }
}

// Flashcard API
export const fetchFlashcards = async (videoId) => {
  try {
    const data = await apiRequest(`${API_BASE_URL}/flashcards/${videoId}`)
    return data
  } catch (error) {
    console.error('Flashcard Error:', error)
    throw error
  }
}

// Important Topics API
export const fetchImportantTopics = async (videoId) => {
  try {
    const data = await apiRequest(`${API_BASE_URL}/important-topics/${videoId}`)
    return data
  } catch (error) {
    console.error('Topics Error:', error)
    throw error
  }
}

// Chat/AI API
export const fetchChatResponse = async (message, videoId) => {
  try {
    const data = await apiRequest(`${API_BASE_URL}/chat`, {
      method: 'POST',
      body: JSON.stringify({
        message: message,
        video_id: videoId,
      })
    })
    return data.reply || data.response || data.message
  } catch (error) {
    console.error('Chat Error:', error)
    throw error
  }
}

// Video Upload/Processing
export const processVideo = async (videoUrl) => {
  try {
    const data = await apiRequest(`${API_BASE_URL}/process-video`, {
      method: 'POST',
      body: JSON.stringify({
        video_url: videoUrl,
      })
    })
    return data
  } catch (error) {
    console.error('Video Processing Error:', error)
    throw error
  }
}

// PDF Processing
export const processPdf = async (formData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/process-pdf`, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header, browser will set it automatically with boundary
      headers: {
        // 'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })

    if (!response.ok) {
      throw new Error(`HTTP Error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('PDF Processing Error:', error)
    throw error
  }
}
