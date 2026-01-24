import React, { useState } from 'react'
import './video.css'
import { Link } from 'react-router-dom'
import QuizDisplay from '../../components/QuizDisplay'
import ReactMarkdown from 'react-markdown'
import { fetchQuiz, fetchFlashcards, fetchImportantTopics, processVideo, createRevisionDoc, learnFromMistakes } from '../../services/apiService'
import Chatbox from '../../components/Chatbox'
import { Spinner } from '../../components/ui/spinner'

const Video = () => {
  const [input, setInput] = useState('')
  const [videoUrl, setVideoUrl] = useState('')
  const [videoId, setVideoId] = useState(null)
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [activeFeature, setActiveFeature] = useState(null)
  const [featureOutput, setFeatureOutput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
const [wrongAnswers, setWrongAnswers] = useState([]) // Track wrong answers for revision

  // New state for progress tracking
  const [isProcessing, setIsProcessing] = useState(false)
  const [indexingProgress, setIndexingProgress] = useState(0)
  const [processingStatus, setProcessingStatus] = useState('')

  // Conversation management state
  const [currentConversation, setCurrentConversation] = useState(null)
  const [userId] = useState('demo-user') // In a real app, this would come from auth

const handleProcess = async () => {
    if (!input) return;
    setVideoUrl(input)
    // Extract video ID from URL (example: YouTube video ID)
    const id = input.split('v=')[1] || input.split('/').pop()
    setVideoId(id)
    console.log('Playing video:', input)

    setIsProcessing(true)
    setIndexingProgress(0)
    setProcessingStatus('Starting indexing...')
    setError(null)
    setActiveFeature(null)
    setCurrentConversation(null) // Reset conversation when processing new video

    try {
      const result = await processVideo(input, (data) => {
        if (data.status === 'progress') {
          setIndexingProgress(data.progress)
          setProcessingStatus(data.message)
        } else if (data.type === 'conversation_info') {
          // Immediately set the conversation when we receive the info
          const newConversation = {
            id: data.conversation_id,
            user_id: userId,
            video_url: input,
            created_at: new Date().toISOString()
          }
          console.log('Video page - About to set conversation:', newConversation)
          setCurrentConversation(newConversation)
          console.log('Video page - Conversation set immediately:', newConversation)
          
          // Update status message based on conversation status
          if (data.status === 'existing_conversation') {
            setProcessingStatus('Using existing conversation, reprocessing video...')
          } else {
            setProcessingStatus('Created new conversation, processing video...')
          }
        }
      }, userId)
      
      console.log('Video processed successfully', result)
      setProcessingStatus('Indexing complete!')
      
      // Ensure conversation is set even if we didn't capture it from stream
      if (result.conversationId && !currentConversation) {
        const newConversation = {
          id: result.conversationId,
          user_id: userId,
          video_url: input,
          created_at: new Date().toISOString()
        }
        setCurrentConversation(newConversation)
        console.log('Conversation set from result:', newConversation)
      }
    } catch (err) {
      console.error('Failed to process video:', err)
      setError('Failed to process video for AI features: ' + err.message)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleFeatureClick = async (feature) => {
    if (!videoId) {
      setError('Please load a video first')
      return
    }

    if (isProcessing) {
      alert("Please wait for the transcript to finish indexing.")
      return
    }

    setActiveFeature(feature)
    setIsLoading(true)
    setError(null)
    setFeatureOutput('')

    try {
      let data
      switch (feature) {
        case 'quiz':
          data = await fetchQuiz(videoId)
          // Don't format quiz output as string, keep it as object/array for the component
          setFeatureOutput(data.questions)
          break
        case 'flashcard':
          data = await fetchFlashcards(videoId)
          setFeatureOutput(formatFlashcardOutput(data))
          break
        case 'important':
          data = await fetchImportantTopics(videoId)
          setFeatureOutput(URL.createObjectURL(data))
          break
        default:
          setFeatureOutput('')
      }
    } catch (err) {
      setError(`Failed to load ${feature}. Please try again.`)
      setFeatureOutput(`❌ Error: ${err.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const formatQuizOutput = (data) => {
    if (Array.isArray(data.questions)) {
      return data.questions.map((q, i) => `${i + 1}. ${q}`).join('\n')
    }
    return data.questions || 'Quiz data format error'
  }

  const formatFlashcardOutput = (data) => {
    if (Array.isArray(data.cards)) {
      return data.cards.map((card, i) => `Card ${i + 1}: ${card.front}\n→ ${card.back}`).join('\n\n')
    }
    return data.cards || 'Flashcard format error'
  }

  const formatTopicsOutput = (data) => {
    if (Array.isArray(data.topics)) {
      return '⭐ Important Topics:\n\n' + data.topics.map(t => `✓ ${t}`).join('\n')
    }
    return data.topics || 'Topics format error'
  }

  const handleWrongAnswer = (questionObj) => {
    console.log("Wrong answer recorded:", questionObj)
    setWrongAnswers(prev => {
      if (prev.some(w => w.question === questionObj.question)) return prev;
      return [...prev, questionObj]
    });
  }

  const handleCreateRevision = async () => {
    if (wrongAnswers.length === 0) {
      alert("Great job! No wrong answers to revise.");
      return;
    }

    setIsLoading(true);
    try {
      const response = await createRevisionDoc(wrongAnswers);
      // Response logic: assuming response.markdown_content contains the markdown
      setFeatureOutput(response.markdown_content);
      setActiveFeature('revision'); // Switch to revision view
    } catch (err) {
      setError("Failed to generate revision document.");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }

const handleMoreQuestions = async () => {
    setIsLoading(true);
    try {
      let data;
      if (wrongAnswers.length > 0) {
        // Iterative learning: generate new questions based on mistakes
        data = await learnFromMistakes(wrongAnswers);
      } else {
        // General refresh if no mistakes
        data = await fetchQuiz(videoId);
      }

      // Reset wrong answers for the new session *after* generating remedial quiz
      setWrongAnswers([]);

      setFeatureOutput(data.questions);
      setActiveFeature('quiz');
    } catch (err) {
      setError("Failed to load more questions.");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }

  const handleConversationChange = (conversation) => {
    setCurrentConversation(conversation)
    console.log('Conversation changed:', conversation)
  }

  return (
    <div className="video-container">
      <div className="video-header">
        <Link to="/" className="back-btn">←</Link>
        <h1>🎥 EdTube Video Learning</h1>
        <Link to="/video/:categoryId/:videoId" className="forward-btn">→</Link>
      </div>

      {/* URL Bar Section */}
      <div className="url-input-section">
        <div className="input-group">
          <input
            className="url-input"
            placeholder="Paste video URL here..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button className="process-btn" onClick={handleProcess}>
            ▶ Play
          </button>
        </div>

        {/* Feature Icons on Right */}
        <div className="icon-toolbar">
          <div
            className={`icon-btn ${activeFeature === 'quiz' ? 'active' : ''}`}
            onClick={() => handleFeatureClick('quiz')}
            title="Quiz"
          >
            ❓
          </div>
          <div
            className={`icon-btn ${activeFeature === 'flashcard' ? 'active' : ''}`}
            onClick={() => handleFeatureClick('flashcard')}
            title="Flashcard"
          >
            🎴
          </div>
          <div
            className={`icon-btn ${activeFeature === 'important' ? 'active' : ''}`}
            onClick={() => handleFeatureClick('important')}
            title="Important Topics"
          >
            ⭐
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      {isProcessing && (
        <div className="progress-container" style={{ maxWidth: '800px', margin: '20px auto', padding: '0 20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span>{processingStatus}</span>
            <span>{indexingProgress}%</span>
          </div>
          <progress value={indexingProgress} max="100" style={{ width: '100%', height: '24px' }}></progress>
        </div>
      )}

      {/* Feature Output Display */}
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {activeFeature && (
        <div className="feature-output">
          <button className="close-feature" onClick={() => { setActiveFeature(null); setFeatureOutput(''); setError(null); }}>✕</button>
          {isLoading ? (
            <div className="flex flex-col items-center justify-center p-8 gap-2">
              <Spinner size="lg" />
              <p className="text-muted-foreground">Loading...</p>
            </div>
          ) : (
            <div className="feature-content">
              {activeFeature === 'quiz' ? (
                <QuizDisplay
                  questions={featureOutput}
                  onWrongAnswer={handleWrongAnswer}
                  onCreateRevision={handleCreateRevision}
                />
              ) : activeFeature === 'revision' ? (
                <div className="revision-container">
                  <ReactMarkdown>{featureOutput}</ReactMarkdown>
                  <div className="quiz-footer">
                    <button className="revision-btn" onClick={handleMoreQuestions}>
                      🔄 Attempt More Questions
                    </button>
                  </div>
                </div>
              ) : activeFeature === 'important' ? (
                <iframe src={featureOutput} width="100%" height="600px" title="Important Topics PDF" style={{ border: 'none' }} />
              ) : (
                // For other features (text based)
                typeof featureOutput === 'string' ? featureOutput.split('\n').map((line, idx) => (
                  <div key={idx} className="output-line">{line}</div>
                )) : JSON.stringify(featureOutput)
              )}
            </div>
          )}
        </div>
      )}

      {/* Video Player Section */}
      {videoId && (
        <div className="video-player-section">
          <h2>Now Playing</h2>
          <iframe
            width="100%"
            height="500"
            src={`https://www.youtube.com/embed/${videoId}`}
            title="YouTube video player"
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            style={{ maxWidth: '900px', margin: '20px auto', display: 'block' }}
          ></iframe>
        </div>
      )}

      {/* Chat Box */}
      <div className={`chat-box ${isChatOpen ? 'open' : 'closed'}`}>
        <div className="chat-header" onClick={() => setIsChatOpen(!isChatOpen)}>
          <span className="chat-toggle">💬</span>
          <span className="chat-title">Ask Questions</span>
        </div>

<div className="chat-content-container" style={{ height: 'calc(100% - 60px)' }}>
          <Chatbox 
            isOpen={isChatOpen} 
            key={videoId} 
            isProcessing={isProcessing}
            userId={userId}
            videoUrl={videoUrl}
            conversationId={currentConversation?.id}
            conversation={currentConversation}
            onConversationChange={handleConversationChange}
          />
        </div>
      </div>
    </div>
  )
}

export default Video