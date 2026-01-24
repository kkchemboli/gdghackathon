import { useExternalStoreRuntime } from '@assistant-ui/react'
import { useState, useCallback } from 'react'
import { getConversationMessages, sendUserQuery } from '../services/apiService'
import { Conversation, MessageResponse } from '../components/Chatbox/types'

const API_BASE_URL = 'http://localhost:8000'

interface ConversationState {
    currentConversation: Conversation | null
    messages: any[]
    isLoading: boolean
    error: string | null
    currentPage: number
    hasNextPage: boolean
    isAiResponding: boolean
    lastError: any
    retryCount: number
    isProcessing: boolean
}

// Global conversation state
let conversationState: ConversationState = {
    currentConversation: null,
    messages: [],
    isLoading: false,
    error: null,
    currentPage: 1,
    hasNextPage: false,
    isAiResponding: false,
    lastError: null,
    retryCount: 0,
    isProcessing: false,
}

/**
 * Convert backend message format to assistant-ui message format
 */
const convertBackendMessageToAssistantUI = (backendMessage: any) => {
    // Ensure content is a string
    const contentText = backendMessage.content || ''

    const message = {
        id: backendMessage._id || backendMessage.id || Math.random().toString(36),
        role: backendMessage.message_type === 'user' ? 'user' : 'assistant',
        content: [{ type: 'text', text: String(contentText) }],
        createdAt: backendMessage.timestamp ? new Date(backendMessage.timestamp) : new Date(),
        // Include metadata for timestamp extraction in AssistantMessage component
        metadata: backendMessage.metadata || {},
        // Add status to prevent Assistant UI library error
        status: { type: "complete" }
    }

    return message
}

/**
 * Convert assistant-ui message format to backend message format
 */
const convertAssistantUIToBackendMessage = (uiMessage: any, conversationId: string, userId: string) => {
    const textContent = uiMessage.content
        .filter((part: any) => part.type === 'text')
        .map((part: any) => part.text)
        .join('')

    return {
        conversation_id: conversationId,
        user_id: userId,
        content: textContent,
        message_type: uiMessage.role,
        metadata: uiMessage.metadata || {}
    }
}

/**
 * Save message to backend
 */
const saveMessageToBackend = async (message: any, conversationId: string, userId: string) => {
    try {
        const backendMessage = convertAssistantUIToBackendMessage(message, conversationId, userId)
        const response = await fetch(`${API_BASE_URL}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(backendMessage)
        })

        if (!response.ok) {
            throw new Error(`Failed to save message: ${response.status}`)
        }

        return await response.json()
    } catch (error) {
        console.error('Error saving message to backend:', error)
        throw error
    }
}

/**
 * Load conversation messages from backend
 */
export const loadConversationMessages = async (conversationId: string, page = 1, setMessagesCallback?: (messages: any) => void) => {
    try {
        conversationState.isLoading = true
        conversationState.error = null

        const response = await getConversationMessages(conversationId, page)

        // The API returns messages array directly, not response.messages
        const messages = Array.isArray(response) ? response : []
        const convertedMessages = messages
            .filter(msg => msg && (msg._id || msg.id)) // Filter out null/undefined messages
            .map(msg => convertBackendMessageToAssistantUI(msg))

        // Update global state for reference
        if (page === 1) {
            conversationState.messages = convertedMessages
        } else {
            conversationState.messages = [...convertedMessages, ...conversationState.messages]
        }

        conversationState.currentPage = page
        conversationState.hasNextPage = messages.length === 50 // If we got a full page, there might be more

        // Update React state via callback if provided
        if (setMessagesCallback) {
            if (page === 1) {
                setMessagesCallback(convertedMessages)
            } else {
                setMessagesCallback((prev: any[]) => [...convertedMessages, ...prev])
            }
        }

        return { messages: convertedMessages, hasNextPage: conversationState.hasNextPage }
    } catch (error: any) {
        conversationState.error = error.message
        throw error
    } finally {
        conversationState.isLoading = false
    }
}

/**
 * Set current conversation and load its messages
 */
export const setCurrentConversation = async (conversation: Conversation | null, setMessagesCallback?: (messages: any) => void) => {
    conversationState.currentConversation = conversation
    conversationState.messages = []
    conversationState.currentPage = 1
    conversationState.hasNextPage = false

    if (conversation) {
        await loadConversationMessages(conversation.id, 1, setMessagesCallback)
    }
}

/**
 * Get current conversation state
 */
export const getConversationState = () => conversationState

/**
 * Create a custom FastAPI runtime that uses our external store
 */
export function useFastApiRuntime(options = {}) {
    const [messages, setMessages] = useState<any[]>([])
    const [isAiResponding, setIsAiResponding] = useState(false)
    const [lastError, setLastError] = useState<any>(null)

    /**
     * Clear processing lock
     */
    const clearProcessing = useCallback(() => {
        conversationState.isProcessing = false
    }, [])

    // Handler for new messages from assistant-ui
    const onNew = useCallback(async (message: any) => {
        // Prevent duplicate processing
        if (conversationState.isProcessing) {
            console.log('Already processing, skipping duplicate message')
            return
        }

        conversationState.isProcessing = true

        if (!conversationState.currentConversation) {
            conversationState.isProcessing = false
            throw new Error('No active conversation to save message to')
        }

        try {
            if (message.role === 'user') {
                const queryText = message.content
                    .filter((part: any) => part && part.type === 'text')
                    .map((part: any) => part.text || '')
                    .join('')

                // 1. Add user message immediately for instant display
                const convertedUserMessage = convertBackendMessageToAssistantUI({
                    _id: message.id,
                    message_type: 'user',
                    content: queryText,
                    timestamp: new Date().toISOString(),
                    metadata: message.metadata || {}
                })

                // 2. Set loading state and clear errors
                setIsAiResponding(true)
                setLastError(null)

                // 3. Update messages with user message
                setMessages(prev => [...prev, convertedUserMessage])

                // 4. Call query endpoint for AI response
                const response = await sendUserQuery(
                    queryText,
                    conversationState.currentConversation.user_id,
                    conversationState.currentConversation.id
                )

                // 5. Add AI response when ready
                const convertedAiMessage = convertBackendMessageToAssistantUI({
                    _id: `ai-${Date.now()}`, // Temporary local ID
                    message_type: 'assistant',
                    content: response.answer,
                    timestamp: response.timestamp,
                    metadata: { timestamp: response.timestamp }
                })

                // 6. Update messages with AI response and clear loading
                setMessages(prev => [...prev, convertedAiMessage])
                setIsAiResponding(false)
                conversationState.isProcessing = false

            } else {
                // For assistant messages (like during reload), use saveMessageToBackend
                await saveMessageToBackend(
                    message,
                    conversationState.currentConversation.id,
                    conversationState.currentConversation.user_id
                )

                // Convert to assistant-ui format and add to local state
                const messageText = message.content
                    ? message.content.filter((part: any) => part && part.type === 'text').map((part: any) => part.text || '').join('')
                    : ''

                const convertedMessage = convertBackendMessageToAssistantUI({
                    _id: message.id,
                    message_type: message.role,
                    content: messageText,
                    timestamp: new Date().toISOString(),
                    metadata: message.metadata || {}
                })

                setMessages(prev => [...prev, convertedMessage])
                conversationState.isProcessing = false
            }

        } catch (error) {
            console.error('Error handling new message:', error)
            setIsAiResponding(false)
            setLastError(error)
            conversationState.isProcessing = false
            // Don't throw error, let UI handle it with retry
        }
    }, [isAiResponding, lastError])

    // Add retry functionality
    const retryLastQuery = useCallback(async () => {
        if (!lastError || !messages.length) return

        // Get the last user message
        const lastUserMessage = [...messages]
            .reverse()
            .find(msg => msg.role === 'user')

        if (!lastUserMessage) return

        // Clear error and retry
        setLastError(null)
        conversationState.retryCount++

        try {
            // Simulate sending the same message again
            await onNew({
                id: `retry-${Date.now()}`,
                role: 'user',
                content: lastUserMessage.content,
                metadata: {}
            })
        } catch (error) {
            console.error('Retry failed:', error)
            setLastError(error)
        }
    }, [lastError, messages, onNew])

    // Validate and sanitize messages before passing to runtime
    const sanitizedMessages = Array.isArray(messages) ? messages.map(msg => {
        if (!msg) return null

        // Ensure role is valid
        const role = (msg.role === 'user' || msg.role === 'assistant') ? msg.role : 'assistant'

        // Sanitize content array
        let content = []
        if (Array.isArray(msg.content)) {
            content = msg.content
                .filter(part => part && typeof part === 'object' && part.type)
                .map(part => ({
                    type: part.type || 'text',
                    text: typeof part.text === 'string' ? part.text : String(part.text || '')
                }))
        } else {
            content = [{ type: 'text', text: String(msg.content || '') }]
        }

        // Ensure we have at least one content part
        if (content.length === 0) {
            content = [{ type: 'text', text: '' }]
        }

        const message = {
            id: msg.id || Math.random().toString(36),
            role: role,
            content: content,
            createdAt: msg.createdAt ? new Date(msg.createdAt) : new Date(),
            metadata: msg.metadata || {},
            // Add status to prevent Assistant UI library error
            status: { type: "complete" }
        }

        // Double-check status property
        if (!message.status || !message.status.type) {
            message.status = { type: "complete" }
        }

        return message
    }).filter(Boolean) : []

    // Add dummy message if array is empty to prevent lastMessage issues
    if (sanitizedMessages.length === 0) {
        sanitizedMessages.push({
            id: 'empty-state',
            role: 'assistant',
            content: [{ type: 'text', text: '' }],
            createdAt: new Date(),
            status: { type: 'complete' },
            metadata: {}
        })
    }

    // Create the external store runtime
    const runtime = useExternalStoreRuntime({
        // Use our local messages state with validation
        messages: sanitizedMessages,

        // Handle new messages
        onNew: onNew,

        // Optional: handle other operations
        onEdit: async (message) => {
            console.log('Edit message:', message)
        },

        onReload: async (parentId) => {
            console.log('Reload message with parent:', parentId)
        },
    })

    // Return runtime with conversation management functions
    return {
        ...runtime,
        setMessages,
        loadConversationMessages,
        setCurrentConversation,
        getConversationState,
        retryLastQuery,
        clearProcessing,
        isAiResponding: () => isAiResponding,
        lastError: () => lastError
    }
}
