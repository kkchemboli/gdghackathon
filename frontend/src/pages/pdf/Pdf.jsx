import React, { useState } from 'react'
import './pdf.css'
import { Link } from 'react-router-dom'

const Pdf = () => {
  const [input, setInput] = useState('')
  const [pdfUrl, setPdfUrl] = useState('')
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [chatMessages, setChatMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [activeFeature, setActiveFeature] = useState(null)
  const [featureOutput, setFeatureOutput] = useState('')

  const handleProcess = () => {
    if (input && input[0]) {
      const file = input[0]
      const reader = new FileReader()
      reader.onload = (e) => {
        setPdfUrl(e.target.result)
      }
      reader.readAsDataURL(file)
      console.log('Loading PDF:', file.name)
    }
  }

  const handleSendMessage = () => {
    if (chatInput.trim()) {
      setChatMessages([...chatMessages, { type: 'user', text: chatInput }])
      setChatInput('')
      setTimeout(() => {
        setChatMessages(prev => [...prev, { type: 'bot', text: 'This is a sample response about the PDF.' }])
      }, 500)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage()
    }
  }

  const handleFeatureClick = (feature) => {
    setActiveFeature(feature)
    switch(feature) {
      case 'quiz':
        setFeatureOutput(`📋 Quiz Questions:\n\n1. What is the main topic?\n2. Explain the concept\n3. Apply the learning\n\nClick to attempt the quiz!`)
        break
      case 'flashcard':
        setFeatureOutput(`🎴 Flashcards Loaded:\n\nCard 1: Front\n→ Back explanation\n\nCard 2: Key Point\n→ Definition\n\nCard 3: Concept\n→ Application\n\nSwipe to navigate!`)
        break
      case 'important':
        setFeatureOutput(`⭐ Important Topics:\n\n✓ Core Concept 1\n✓ Key Definition\n✓ Main Application\n✓ Important Formula\n✓ Real-world Example\n\nThese are critical for understanding!`)
        break
      default:
        setFeatureOutput('')
    }
  }

  return (
    <div className="pdf-container">
      <div className="pdf-header">
        <Link to="/video" className="back-btn">←</Link>
        <h1>📄 EdTube PDF Learning</h1>
        <div className="forward-btn">→</div>
      </div>

      {/* File Upload Section */}
      <div className="url-input-section">
        <div className="input-group">
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setInput(e.target.files)}
            className="file-input"
          />
          <button className="process-btn" onClick={handleProcess}>
            📤 Upload
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

      {/* Feature Output Display */}
      {activeFeature && featureOutput && (
        <div className="feature-output">
          <button className="close-feature" onClick={() => { setActiveFeature(null); setFeatureOutput(''); }}>✕</button>
          <div className="feature-content">
            {featureOutput.split('\n').map((line, idx) => (
              <div key={idx} className="output-line">{line}</div>
            ))}
          </div>
        </div>
      )}

      {/* PDF Viewer Section */}
      {pdfUrl && (
        <div className="pdf-viewer-section">
          <h2>PDF Document</h2>
          <embed
            src={pdfUrl}
            type="application/pdf"
            width="100%"
            height="600px"
            style={{ borderRadius: '8px', marginTop: '20px' }}
          />
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
                placeholder="Ask a question about the PDF..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyPress={handleKeyPress}
              />
              <button className="send-btn" onClick={handleSendMessage}>
                Send
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Pdf