import React, { useState, useEffect } from 'react'
import {
    AssistantRuntimeProvider,
    ThreadPrimitive,
    ComposerPrimitive,
    MessagePrimitive,
    useMessage,
} from '@assistant-ui/react'

import { useFastApiRuntime, setCurrentConversation, getConversationState } from '../../runtime/fastapiRuntime'
import ConversationSelector from './ConversationSelector'
import { Conversation, ChatboxProps } from './types'

/**
 * Simple Avatar component
 */
const Avatar: React.FC<{ children: React.ReactNode; className?: string }> = ({
    children,
    className = '',
}) => {
    return (
        <div className={`flex h-8 w-8 items-center justify-center rounded-full border border-white/15 ${className}`}>
            {children}
        </div>
    )
}

/**
 * Arrow Up Icon SVG
 */
const ArrowUpIcon: React.FC<{ className?: string }> = ({ className = '' }) => {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
        >
            <path d="m5 12 7-7 7 7" />
            <path d="M12 19V5" />
        </svg>
    )
}

/**
 * Custom Assistant Message component that extracts and displays timestamps
 */
const AssistantMessage: React.FC = () => {
    const message = useMessage()
    const content = message.content
        .filter((part) => part.type === 'text')
        .map((part) => part.text)
        .join('')

    // Extract timestamp from metadata first, then fallback to content pattern
    // @ts-ignore - metadata field varies by version
    const timestamp = message.metadata?.timestamp || null
    const timestampMatch = content.match(/\[Timestamp:\s*([^\]]+)\]/)
    const fallbackTimestamp = timestampMatch ? timestampMatch[1] : null
    const finalTimestamp = timestamp || fallbackTimestamp

    const displayContent = timestampMatch
        ? content.replace(/\[Timestamp:\s*([^\]]+)\]\s*/g, '').trim()
        : content
    return (
        <MessagePrimitive.Root className="flex gap-3 px-3 py-4">
            <Avatar className="shrink-0">
                <span className="text-white text-xs">AI</span>
            </Avatar>
            <div className="flex flex-col gap-1 flex-1 min-w-0">
                <div className="text-white whitespace-pre-wrap text-sm">{displayContent}</div>
                {finalTimestamp && (
                    <div className="text-[#cdcdcd] text-xs mt-1">
                        Timestamp: {finalTimestamp}
                    </div>
                )}
            </div>
        </MessagePrimitive.Root>
    )
}

/**
 * Custom User Message component
 */
const UserMessage: React.FC = () => {
    const message = useMessage()
    const content = message.content
        .filter((part) => part.type === 'text')
        .map((part) => part.text)
        .join('')

    return (
        <MessagePrimitive.Root className="flex gap-3 px-3 py-4">
            <div className="flex flex-col gap-1 flex-1 items-end ml-auto">
                <div className="text-white whitespace-pre-wrap bg-white/10 rounded-2xl px-3 py-2 text-sm">
                    {content}
                </div>
            </div>
        </MessagePrimitive.Root>
    )
}

/**
 * Edit Composer component (for editing messages)
 */
const EditComposer: React.FC = () => {
    return (
        <MessagePrimitive.Root className="flex gap-3 px-3 py-4">
            <Avatar>
                <span className="text-white text-xs">AI</span>
            </Avatar>
            <div className="flex-1">
                <ComposerPrimitive.Root className="flex flex-col gap-2">
                    <ComposerPrimitive.Input className="h-10 max-h-40 flex-grow resize-none bg-white/5 rounded-lg p-2 text-white outline-none placeholder:text-white/50 text-sm" />
                    <div className="flex gap-2">
                        <ComposerPrimitive.Send className="px-3 py-1 bg-white/10 text-white rounded-lg hover:bg-white/20 text-xs">
                            Save
                        </ComposerPrimitive.Send>
                        <ComposerPrimitive.Cancel className="px-3 py-1 bg-white/5 text-white rounded-lg hover:bg-white/10 text-xs">
                            Cancel
                        </ComposerPrimitive.Cancel>
                    </div>
                </ComposerPrimitive.Root>
            </div>
        </MessagePrimitive.Root>
    )
}

/**
 * Enhanced ChatboxInner with conversation management
 */
interface ChatboxInnerProps {
    isOpen: boolean
    isProcessing?: boolean
    userId?: string
    videoUrl?: string
    selectedConversation?: Conversation | null
    onConversationSelect: (conversation: Conversation | null) => void
    isLoadingConversation?: boolean
}

const ChatboxInner: React.FC<ChatboxInnerProps> = ({
    isOpen,
    isProcessing,
    userId,
    videoUrl,
    selectedConversation,
    onConversationSelect,
    isLoadingConversation
}) => {
    if (!isOpen) return null;

    const [showLoadMore, setShowLoadMore] = useState(false)
    const [isLoadingMore, setIsLoadingMore] = useState(false)
    const conversationState = getConversationState()
    const runtime = useFastApiRuntime()
    const isAiResponding = runtime.isAiResponding?.() || false
    const lastError = runtime.lastError?.()

    const { setMessages } = runtime

    // Loading indicator component
    const LoadingIndicator = () => (
        <div className="flex gap-3 px-3 py-4">
            <Avatar className="shrink-0">
                <span className="text-white text-xs">AI</span>
            </Avatar>
            <div className="flex flex-col gap-1 flex-1 min-w-0">
                <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <div className="text-white text-sm">AI is thinking...</div>
                </div>
            </div>
        </div>
    )

    // Retry button component
    const RetryButton = ({ onRetry }: { onRetry: () => void }) => (
        <div className="flex gap-3 px-3 py-4">
            <Avatar className="shrink-0">
                <span className="text-white text-xs">AI</span>
            </Avatar>
            <div className="flex flex-col gap-1 flex-1 min-w-0">
                <div className="flex items-center gap-2">
                    <div className="text-red-400 text-sm">Failed to get response</div>
                    <button
                        onClick={onRetry}
                        className="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white text-xs rounded-lg transition-colors"
                    >
                        Retry
                    </button>
                </div>
            </div>
        </div>
    )

    const handleLoadMore = async () => {
        if (!selectedConversation || isLoadingMore) return

        try {
            setIsLoadingMore(true)
            await runtime.loadConversationMessages(selectedConversation.id, conversationState.currentPage + 1, setMessages)
        } catch (error) {
            console.error('Failed to load more messages:', error)
        } finally {
            setIsLoadingMore(false)
        }
    }

    // Check if we should show load more button
    useEffect(() => {
        setShowLoadMore(conversationState.hasNextPage && conversationState.messages.length > 0)
    }, [conversationState.hasNextPage, conversationState.messages.length])

    return (
        <ThreadPrimitive.Root className="flex flex-col h-full bg-[#212121] text-foreground rounded-b-xl overflow-hidden">
            {/* Conversation Header */}
            {userId && (
                <div className="border-b border-white/10 p-3">
                    <ConversationSelector
                        userId={userId}
                        videoUrl={videoUrl}
                        selectedConversation={selectedConversation}
                        onConversationSelect={onConversationSelect}
                    />
                    {selectedConversation && (
                        <div className="mt-2 text-[#cdcdcd] text-xs">
                            Started: {new Date(selectedConversation.created_at).toLocaleString()}
                        </div>
                    )}
                </div>
            )}

            <ThreadPrimitive.Viewport className="flex flex-grow flex-col gap-4 overflow-y-auto p-2 scrollbar-hide">
                {isLoadingConversation ? (
                    <div className="flex flex-grow flex-col items-center justify-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
                        <p className="mt-4 text-white text-sm">Loading conversation...</p>
                    </div>
                ) : (
                    <>
                        {/* Load More Button */}
                        {showLoadMore && (
                            <div className="flex justify-center py-2">
                                <button
                                    onClick={handleLoadMore}
                                    disabled={isLoadingMore}
                                    className="px-3 py-1 bg-white/10 hover:bg-white/20 text-white text-xs rounded-lg transition-colors disabled:opacity-50"
                                >
                                    {isLoadingMore ? 'Loading...' : 'Load Earlier Messages'}
                                </button>
                            </div>
                        )}

                        <ThreadPrimitive.Empty>
                            <div className="flex flex-grow flex-col items-center justify-center py-8">
                                <Avatar className="h-12 w-12">
                                    <span className="text-white">AI</span>
                                </Avatar>
                                <p className="mt-4 text-white text-sm">
                                    {isProcessing
                                        ? "Indexing video transcript..."
                                        : selectedConversation
                                            ? "Conversation loaded. Ask a question to continue."
                                            : "How can I help you today?"
                                    }
                                </p>
                            </div>
                        </ThreadPrimitive.Empty>

                        <ThreadPrimitive.Messages
                            components={{ UserMessage, EditComposer, AssistantMessage }}
                        />

                        {/* Loading indicator */}
                        {isAiResponding && <LoadingIndicator />}

                        {/* Retry button for errors */}
                        {lastError && (
                            <RetryButton
                                onRetry={() => runtime.retryLastQuery?.()}
                            />
                        )}
                    </>
                )}
            </ThreadPrimitive.Viewport>

            <div className="p-3 bg-[#212121]">
                <ComposerPrimitive.Root className="flex w-full items-end rounded-2xl bg-white/5 pl-2 relative">
                    <ComposerPrimitive.Input
                        placeholder={isProcessing
                            ? "Please wait for indexing..."
                            : isAiResponding
                                ? "AI is responding..."
                                : selectedConversation
                                    ? "Continue the conversation..."
                                    : "Ask about the video..."
                        }
                        disabled={isProcessing || isAiResponding}
                        className="h-10 max-h-32 flex-grow resize-none bg-transparent p-2.5 text-white outline-none placeholder:text-white/50 text-sm pr-10 disabled:opacity-50 disabled:cursor-not-allowed"
                    />
                    <ComposerPrimitive.Send
                        disabled={isProcessing || isAiResponding}
                        className="absolute right-1 bottom-1 p-1.5 flex items-center justify-center rounded-full bg-white disabled:opacity-30 hover:bg-gray-200 transition-colors cursor-pointer"
                    >
                        <ArrowUpIcon className="h-4 w-4 text-black" />
                    </ComposerPrimitive.Send>
                </ComposerPrimitive.Root>
                <p className="pt-2 text-center text-[#cdcdcd] text-[10px]">
                    AI can make mistakes. Check important info.
                </p>
            </div>
        </ThreadPrimitive.Root>
    )
}

/**
 * Main Chatbox component with runtime provider and conversation management
 */
const Chatbox: React.FC<ChatboxProps> = ({
    isOpen,
    isProcessing,
    userId,
    videoUrl,
    conversationId,
    conversation,
    onConversationChange
}) => {
    const runtime = useFastApiRuntime()
    const { setMessages } = runtime
    const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null)
    const [isLoadingConversation, setIsLoadingConversation] = useState(false)

    // Use provided conversation object if available, otherwise fetch from API
    useEffect(() => {
        const handleConversationChange = async () => {
            if (isOpen) {
                if (conversation) {
                    setSelectedConversation(conversation)
                    await setCurrentConversation(conversation, setMessages)
                    onConversationChange?.(conversation)
                } else if (conversationId && userId && videoUrl) {
                    loadCurrentConversation()
                } else {
                    setSelectedConversation(null)
                    await setCurrentConversation(null, setMessages)
                    onConversationChange?.(null)
                }
            }
        }

        handleConversationChange()
    }, [isOpen, userId, videoUrl, conversationId, conversation])

    const loadCurrentConversation = async () => {
        if (!conversationId) {
            setSelectedConversation(null)
            await setCurrentConversation(null, setMessages)
            onConversationChange?.(null)
            return
        }

        try {
            setIsLoadingConversation(true)

            const minimalConversation: Conversation = {
                id: conversationId,
                user_id: userId || '',
                video_url: videoUrl || '',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            }

            setSelectedConversation(minimalConversation)
            await setCurrentConversation(minimalConversation, setMessages)
            onConversationChange?.(minimalConversation)
        } catch (error) {
            console.error('Failed to load conversation:', error)
        } finally {
            setIsLoadingConversation(false)
        }
    }

    const handleConversationSelect = async (conversation: Conversation | null) => {
        setSelectedConversation(conversation)
        await setCurrentConversation(conversation, setMessages)
        onConversationChange?.(conversation)
    }

    return (
        <AssistantRuntimeProvider runtime={runtime}>
            <ChatboxInner
                isOpen={isOpen}
                isProcessing={isProcessing}
                userId={userId}
                videoUrl={videoUrl}
                selectedConversation={selectedConversation}
                onConversationSelect={handleConversationSelect}
                isLoadingConversation={isLoadingConversation}
            />
        </AssistantRuntimeProvider>
    )
}

Chatbox.displayName = 'Chatbox'

export default Chatbox
