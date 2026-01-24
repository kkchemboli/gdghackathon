export type MessageRole = 'user' | 'assistant'

export interface Message {
    role: MessageRole
    content: string
    timestamp?: string
}

export interface QueryRequest {
    query: string
}

export interface QueryResponse {
    answer: string
    timestamp: string
}

// Conversation Management Types
export interface Conversation {
    id: string
    user_id: string
    video_url: string
    title?: string
    notes_url?: string
    created_at: string
    updated_at: string
}

export interface ConversationCreate {
    user_id: string
    video_url: string
    title?: string
}

export interface MessageResponse {
    id: string
    conversation_id: string
    user_id: string
    content: string
    message_type: string
    timestamp: string
    metadata?: {
        timestamp?: string
    }
}

export interface MessageCreate {
    conversation_id: string
    user_id: string
    content: string
    message_type: string
    metadata?: {
        timestamp?: string
    }
}

// Pagination Types
export interface PaginatedMessages {
    messages: MessageResponse[]
    currentPage: number
    totalPages: number
    totalMessages: number
    hasNextPage: boolean
    hasPreviousPage: boolean
}

export interface ConversationState {
    currentConversation: Conversation | null
    messages: MessageResponse[]
    isLoading: boolean
    error: string | null
    currentPage: number
    hasNextPage: boolean
}

// Chatbox Props
export interface ChatboxProps {
    isOpen: boolean
    isProcessing?: boolean
    userId?: string
    videoUrl?: string
    conversationId?: string
    conversation?: Conversation | null
    onConversationChange?: (conversation: Conversation | null) => void
}
