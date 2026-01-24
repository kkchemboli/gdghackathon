import React, { useState } from 'react'
import { getUserConversations } from '../../../services/apiService'
import { Conversation } from './types'

interface ConversationSelectorProps {
    userId: string
    videoUrl?: string
    selectedConversation?: Conversation | null
    onConversationSelect: (conversation: Conversation | null) => void
    className?: string
}

const ConversationSelector: React.FC<ConversationSelectorProps> = ({
    userId,
    videoUrl,
    selectedConversation,
    onConversationSelect,
    className = ''
}) => {
    const [conversations, setConversations] = useState<Conversation[]>([])
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [isOpen, setIsOpen] = useState(false)
    const [conversationsLoaded, setConversationsLoaded] = useState(false)

    const loadConversations = async () => {
        try {
            setIsLoading(true)
            setError(null)
            const userConversations = await getUserConversations(userId)
            setConversations(userConversations || [])
        } catch (err) {
            setError(err.message)
            console.error('Failed to load conversations:', err)
        } finally {
            setIsLoading(false)
        }
    }

    const handleConversationSelect = (conversation: Conversation | null) => {
        onConversationSelect(conversation)
        setIsOpen(false)
    }

    const handleDropdownClick = async () => {
        // Only load conversations if not already loaded and user is available
        if (!conversationsLoaded && userId) {
            console.log('ConversationSelector - Loading conversations on dropdown click')
            await loadConversations()
            setConversationsLoaded(true)
        }
        setIsOpen(!isOpen)
    }

    const formatDate = (dateString: string) => {
        const date = new Date(dateString)
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    const getVideoTitle = (conversation: Conversation) => {
        if (conversation.title) return conversation.title
        // Extract video ID from URL for display
        const urlMatch = conversation.video_url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&]+)/)
        return urlMatch ? `Video: ${urlMatch[1]}` : 'Video'
    }

    const currentVideoConversation = conversations.find(conv => conv.video_url === videoUrl)

    return (
        <div className={`conversation-selector ${className}`}>
            <div className="relative">
                <button
                    onClick={handleDropdownClick}
                    className="w-full flex items-center justify-between px-3 py-2 text-sm bg-white/10 hover:bg-white/20 rounded-lg transition-colors text-white"
                    disabled={isLoading}
                >
                    <span className="truncate">
                        {selectedConversation
                            ? getVideoTitle(selectedConversation)
                            : currentVideoConversation
                                ? `${getVideoTitle(currentVideoConversation)} (Current)`
                                : isLoading
                                    ? 'Loading Conversations...'
                                    : 'Select Conversation'
                        }
                    </span>
                    <svg
                        className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                </button>

                {isOpen && (
                    <div className="absolute top-full left-0 right-0 mt-1 bg-[#2a2a2a] border border-white/10 rounded-lg shadow-lg z-50 max-h-64 overflow-y-auto">
                        <div className="p-2">
                            <button
                                onClick={() => handleConversationSelect(null)}
                                className={`w-full text-left px-3 py-2 text-sm rounded hover:bg-white/10 transition-colors ${!selectedConversation ? 'bg-white/10' : ''
                                    }`}
                            >
                                <div className="text-white">New Conversation</div>
                                <div className="text-[#cdcdcd] text-xs">Start fresh</div>
                            </button>

                            {currentVideoConversation && currentVideoConversation.id !== selectedConversation?.id && (
                                <button
                                    onClick={() => handleConversationSelect(currentVideoConversation)}
                                    className="w-full text-left px-3 py-2 text-sm rounded hover:bg-white/10 transition-colors mt-1"
                                >
                                    <div className="text-white">
                                        {getVideoTitle(currentVideoConversation)}
                                        <span className="ml-2 text-xs bg-blue-500/20 text-blue-300 px-1 py-0.5 rounded">Current</span>
                                    </div>
                                    <div className="text-[#cdcdcd] text-xs">
                                        {formatDate(currentVideoConversation.created_at)}
                                    </div>
                                </button>
                            )}

                            <div className="border-t border-white/10 my-2"></div>

                            <div className="text-[#cdcdcd] text-xs px-3 py-1 font-medium">
                                Previous Conversations
                            </div>

                            {conversations
                                .filter(conv => conv.id !== currentVideoConversation?.id)
                                .map((conversation) => (
                                    <button
                                        key={conversation.id}
                                        onClick={() => handleConversationSelect(conversation)}
                                        className={`w-full text-left px-3 py-2 text-sm rounded hover:bg-white/10 transition-colors ${selectedConversation?.id === conversation.id ? 'bg-white/10' : ''
                                            }`}
                                    >
                                        <div className="text-white truncate">
                                            {getVideoTitle(conversation)}
                                        </div>
                                        <div className="text-[#cdcdcd] text-xs">
                                            {formatDate(conversation.created_at)}
                                        </div>
                                    </button>
                                ))}

                            {conversations.filter(conv => conv.id !== currentVideoConversation?.id).length === 0 && (
                                <div className="text-[#cdcdcd] text-xs px-3 py-2 text-center">
                                    No previous conversations
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {error && (
                <div className="text-red-400 text-xs mt-1">
                    Error: {error}
                </div>
            )}
        </div>
    )
}

export default ConversationSelector