// Mock API Service - Use this for testing without backend
// Replace with real API calls when backend is ready

// Mock Quiz Data
const mockQuizData = {
  questions: [
    "What is the main topic of this video?",
    "Explain the key concepts discussed",
    "How would you apply this in real life?",
    "What are the limitations of this approach?",
    "Can you summarize the key points?"
  ]
}

// Mock Flashcards
const mockFlashcards = {
  cards: [
    { front: "Definition 1", back: "The fundamental concept that forms the basis of this topic" },
    { front: "Concept A", back: "This refers to the primary principle explained in the video" },
    { front: "Term B", back: "An important application of the concepts discussed" },
    { front: "Key Point", back: "The most critical takeaway from this lesson" },
    { front: "Example", back: "A real-world scenario demonstrating the concepts" }
  ]
}

// Mock Important Topics
const mockTopics = {
  topics: [
    "Foundational Concepts",
    "Core Principles",
    "Key Definitions",
    "Practical Applications",
    "Common Misconceptions",
    "Advanced Topics",
    "Real-world Examples"
  ]
}

// Mock Chat Responses
const mockChatResponses = [
  "That's a great question! Based on the video, the answer involves understanding the core principles discussed.",
  "This concept is important because it forms the foundation for more advanced topics.",
  "You can apply this by considering the practical examples shown in the video.",
  "The key difference is that this approach is more efficient than the traditional method.",
  "Excellent observation! This ties directly to what was mentioned in the middle section.",
  "To clarify, this particular aspect relates to the main topic introduced at the start."
]

// Mock Quiz API
export const fetchQuiz = async (videoId) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(mockQuizData)
    }, 500)
  })
}

// Mock Flashcards API
export const fetchFlashcards = async (videoId) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(mockFlashcards)
    }, 500)
  })
}

// Mock Important Topics API
export const fetchImportantTopics = async (videoId) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(mockTopics)
    }, 500)
  })
}

// Mock Chat API
export const fetchChatResponse = async (message, videoId) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const randomResponse = mockChatResponses[Math.floor(Math.random() * mockChatResponses.length)]
      resolve(randomResponse)
    }, 800)
  })
}

// These are the real API functions - uncomment when backend is ready
/*
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api'

const apiRequest = async (url, options = {}) => {
  const defaultHeaders = {
    'Content-Type': 'application/json',
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

export const fetchQuiz = async (videoId) => {
  try {
    const data = await apiRequest(`${API_BASE_URL}/quiz/${videoId}`)
    return data
  } catch (error) {
    console.error('Quiz Error:', error)
    throw error
  }
}

export const fetchFlashcards = async (videoId) => {
  try {
    const data = await apiRequest(`${API_BASE_URL}/flashcards/${videoId}`)
    return data
  } catch (error) {
    console.error('Flashcard Error:', error)
    throw error
  }
}

export const fetchImportantTopics = async (videoId) => {
  try {
    const data = await apiRequest(`${API_BASE_URL}/important-topics/${videoId}`)
    return data
  } catch (error) {
    console.error('Topics Error:', error)
    throw error
  }
}

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
*/
