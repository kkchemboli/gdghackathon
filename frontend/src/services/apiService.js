// API Service for EdTube Features - Python Backend Compatible

const PYTHON_API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Helper function for API requests
const apiRequest = async (url, options = {}) => {
  const defaultHeaders = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
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
export const fetchQuiz = async (videoId, userId) => {
  try {
    // The backend endpoint is /create_quiz and it now expects user_id
    const data = await apiRequest(`${PYTHON_API_BASE_URL}/api/create_quiz`, {
      method: 'POST',
      body: JSON.stringify({})
    })
    return data
  } catch (error) {
    console.error('Quiz Error:', error)
    throw error
  }
}

export const createRevisionDoc = async (mistakes, userId) => {
  try {
    const data = await apiRequest(`${PYTHON_API_BASE_URL}/api/revision_doc`, {
      method: 'POST',
      body: JSON.stringify({ mistakes }),
    })
    return data
  } catch (error) {
    console.error('Revision Doc Error:', error)
    throw error
  }
}

export const learnFromMistakes = async (mistakes) => {
  try {
    const data = await apiRequest(`${PYTHON_API_BASE_URL}/api/learn_from_mistakes`, {
      method: 'POST',
      body: JSON.stringify({ mistakes }),
    })
    return data
  } catch (error) {
    console.error('Learn From Mistakes Error:', error)
    throw error
  }
}

// Flashcard API
export const fetchFlashcards = async () => {
  try {
    const data = await apiRequest(`${PYTHON_API_BASE_URL}/flashcards/`)
    return data
  } catch (error) {
    console.error('Flashcard Error:', error)
    throw error
  }
}

// Important Topics API
export const fetchImportantTopics = async (videoId, userId, conversationId) => {
  try {
    const response = await fetch(`${PYTHON_API_BASE_URL}/api/important_notes?conversation_id=${conversationId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      }
    })
    if (!response.ok) throw new Error('Failed to fetch important notes')
    return await response.blob()
  } catch (error) {
    console.error('Topics Error:', error)
    throw error
  }
}

// Chat/AI API
export const fetchChatResponse = async (message) => {
  try {
    const data = await apiRequest(`${PYTHON_API_BASE_URL}/api/query`, {
      method: 'POST',
      body: JSON.stringify({
        query: message,
      })
    })
    return data.answer
  } catch (error) {
    console.error('Chat Error:', error)
    throw error
  }
}

// Send user query to backend for processing with RAG
export const sendUserQuery = async (query, userId, conversationId) => {
  try {
    const data = await apiRequest(`${PYTHON_API_BASE_URL}/api/query`, {
      method: 'POST',
      body: JSON.stringify({
        query: query,
        conversation_id: conversationId
      })
    })
    return data // {answer: string, timestamp: string}
  } catch (error) {
    console.error('Query Error:', error)
    throw error
  }
}

// Video Upload/Processing
export const processVideo = async (videoUrl, onProgress, userId) => {
  try {
    // Generate a simple ID from the URL if not provided
    const videoId = videoUrl.split('v=')[1] || videoUrl.split('/').pop() || 'unknown'

    const response = await fetch(`${PYTHON_API_BASE_URL}/api/video`, {
      method: 'POST',
      body: JSON.stringify({
        url: videoUrl,
      }),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      }
    })

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP Error: ${response.status} ${response.statusText} - ${errorText}`)
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let conversationId = null;
    let conversationStatus = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;

      const lines = buffer.split('\n');
      // Keep the last possibly incomplete line in the buffer
      buffer = lines.pop();

      for (const line of lines) {
        if (line.trim()) {
          try {
            const data = JSON.parse(line);

            // Capture conversation info from the first message
            if (data.type === 'conversation_info' && !conversationId) {
              conversationId = data.conversation_id;
              conversationStatus = data.status;
              console.log('Conversation info received:', { conversationId, conversationStatus });
            }

            if (onProgress) {
              onProgress(data);
            }
            if (data.status === 'error') {
              throw new Error(data.message);
            }
          } catch (e) {
            console.error('Error parsing JSON from stream:', e);
          }
        }
      }
    }

    // Process any remaining buffer
    if (buffer.trim()) {
      try {
        const data = JSON.parse(buffer);

        // Capture conversation info from the final message if not already captured
        if (data.type === 'conversation_info' && !conversationId) {
          conversationId = data.conversation_id;
          conversationStatus = data.status;
          console.log('Conversation info received from buffer:', { conversationId, conversationStatus });
        }

        if (onProgress) onProgress(data);
        if (data.status === 'error') {
          throw new Error(data.message);
        }
      } catch (e) {
        console.error('Error parsing JSON from valid buffer:', e);
      }
    }

    return {
      status: 'success',
      conversationId,
      conversationStatus
    }
  } catch (error) {
    console.error('Video Processing Error:', error)
    throw error
  }
}

// Conversation Management APIs
export const getUserConversations = async (userId) => {
  try {
    const data = await apiRequest(`${PYTHON_API_BASE_URL}/api/conversations/${userId}`)
    return data
  } catch (error) {
    console.error('Get User Conversations Error:', error)
    throw error
  }
}

export const getConversationMessages = async (conversationId, page = 1, limit = 50) => {
  try {
    const data = await apiRequest(`${PYTHON_API_BASE_URL}/api/messages/${conversationId}?page=${page}&limit=${limit}`)
    return data
  } catch (error) {
    console.error('Get Conversation Messages Error:', error)
    throw error
  }
}

export const createConversation = async (conversationData) => {
  try {
    const data = await apiRequest(`${PYTHON_API_BASE_URL}/api/conversations`, {
      method: 'POST',
      body: JSON.stringify(conversationData)
    })
    return data
  } catch (error) {
    console.error('Create Conversation Error:', error)
    throw error
  }
}

export const getCurrentConversation = async (videoUrl, userId) => {
  // DEPRECATED: This function should not be used anymore
  // Conversation objects should be provided by parent components
  // This function was making incorrect API calls to /conversations/{userId}
  console.warn('getCurrentConversation is deprecated - conversation should be provided by parent')
  return null
}

// PDF Processing
export const processPdf = async (formData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/process-pdf`, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header, browser will set it automatically with boundary
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

// User Preference/Feedback API
export const submitFeedback = async (userId, feedbackText) => {
  try {
    const data = await apiRequest(`${PYTHON_API_BASE_URL}/api/feedback`, {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        feedback_text: feedbackText
      })
    })
    return data
  } catch (error) {
    console.error('Feedback Submission Error:', error)
    throw error
  }
}
