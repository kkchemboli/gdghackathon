import React, { useState } from 'react'
import './video.css'
import { Link } from 'react-router-dom'
import quiz_icon from '../../assets/quiz.png'
import important_icon  from '../../assets/important.png'
import flascard_icon from '../../assets/flashcard.png'
import { fetchQuiz, fetchFlashcards, fetchImportantTopics, fetchChatResponse } from '../../services/mockApiService'

const Video = () => {
  const [input, setInput] = useState('')
  const [videoUrl, setVideoUrl] = useState('')
  const [videoId, setVideoId] = useState(null)
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [chatMessages, setChatMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [activeFeature, setActiveFeature] = useState(null)
  const [featureOutput, setFeatureOutput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleProcess = () => {
    setVideoUrl(input)
    // Extract video ID from URL (example: YouTube video ID)
    const id = input.split('v=')[1] || input.split('/').pop()
    setVideoId(id)
    console.log('Playing video:', input)
  }

  const handleSendMessage = async () => {
    if (chatInput.trim() && videoId) {
      setChatMessages([...chatMessages, { type: 'user', text: chatInput }])
      const message = chatInput
      setChatInput('')
      
      try {
        setIsLoading(true)
        const response = await fetchChatResponse(message, videoId)
        setChatMessages(prev => [...prev, { type: 'bot', text: response }])
      } catch (err) {
        setChatMessages(prev => [...prev, { type: 'bot', text: 'Sorry, I could not process your question.' }])
      } finally {
        setIsLoading(false)
      }
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isLoading) {
      handleSendMessage()
    }
  }

  const handleFeatureClick = async (feature) => {
    if (!videoId) {
      setError('Please load a video first')
      return
    }

    setActiveFeature(feature)
    setIsLoading(true)
    setError(null)
    setFeatureOutput('')

    try {
      let data
      switch(feature) {
        case 'quiz':
          data = await fetchQuiz(videoId)
          setFeatureOutput(formatQuizOutput(data))
          break
        case 'flashcard':
          data = await fetchFlashcards(videoId)
          setFeatureOutput(formatFlashcardOutput(data))
          break
        case 'important':
          data = await fetchImportantTopics(videoId)
          setFeatureOutput(formatTopicsOutput(data))
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
      return data.questions.map((q, i) => `${i+1}. ${q}`).join('\n')
    }
    return data.questions || 'Quiz data format error'
  }

  const formatFlashcardOutput = (data) => {
    if (Array.isArray(data.cards)) {
      return data.cards.map((card, i) => `Card ${i+1}: ${card.front}\n→ ${card.back}`).join('\n\n')
    }
    return data.cards || 'Flashcard format error'
  }

  const formatTopicsOutput = (data) => {
    if (Array.isArray(data.topics)) {
      return '⭐ Important Topics:\n\n' + data.topics.map(t => `✓ ${t}`).join('\n')
    }
    return data.topics || 'Topics format error'
  }

  return (
    <div className="video-container">
      <div className="video-header">
        <h1> EdTube Video Learning</h1>
      </div>
        <span className="video-h2"><h2> Insert The Video Url </h2></span>

    {/* URL Bar Section */}
<div className="url-input-section">

  {/* URL Input Container */}
  <div className="url-card">
    <input
      className="url-input"
      placeholder="Paste video URL here..."
      value={input}
      onChange={(e) => setInput(e.target.value)}
    />
<div className="play-card">
    <button className="process-btn" onClick={handleProcess}>
      ▶ Play
    </button>
  </div>
  </div>

</div>

  <div className="features-card">
    <div
      className={`icon-btn ${activeFeature === 'quiz' ? 'active' : ''}`}
      onClick={() => handleFeatureClick('quiz')}
      title="Quiz"
    >
      <img src={quiz_icon} alt="quiz" />
    </div>

    <div
      className={`icon-btn ${activeFeature === 'flashcard' ? 'active' : ''}`}
      onClick={() => handleFeatureClick('flashcard')}
      title="Flashcard"
    >
      <img src={flascard_icon} alt="flashcard" />
    </div>

    <div
      className={`icon-btn ${activeFeature === 'important' ? 'active' : ''}`}
      onClick={() => handleFeatureClick('important')}
      title="Important Topics"
    >
      <img src={important_icon} alt="important" />
    </div>
  </div>


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
            <div className="loading-spinner">Loading</div>

          ) : (
            <div className="feature-content">
              {featureOutput.split('\n').map((line, idx) => (
                <div key={idx} className="output-line">{line}</div>
              ))}
            </div>
          )}
        </div>
      )}
      {/* Video Player Section */}
      {videoUrl && (
        <div className="video-player-section">
          <h2>Now Playing</h2>
          <video
            controls
            width="100%"
            style={{ maxWidth: '900px', margin: '20px auto', display: 'block' }}
          >
            <source src={videoUrl} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        </div>
      )}


      {/* Chat Box */}
      <div className={`chat-box ${isChatOpen ? 'open' : 'closed'}`}>
        <div className="chat-header" onClick={() => setIsChatOpen(!isChatOpen)}>
          <span className="chat-toggle">💬</span>
          <span className="chat-title">Ask Questions</span>
        </div>

        {isChatOpen && (
          <div className="chat-content">
            <div className="messages-container">
              {chatMessages.map((msg, idx) => (
                <div key={idx} className={`message ${msg.type}`}>
                  {msg.text}
                </div>
              ))}
            </div>
            <div className="chat-input-section">
              <input
                type="text"
                className="chat-input"
                placeholder="Ask a question about the video..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
              />
              <button className="send-btn" onClick={handleSendMessage} disabled={isLoading}>
                {isLoading ? '⏳' : 'Send'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Video