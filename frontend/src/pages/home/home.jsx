import React from 'react'
import './home.css'
import Sidebar from '../../component/Sidebar/sidebar.jsx'
import video_demo from '../../assets/demo.mp4' // Using existing asset as placeholder for the visual
import { Link } from 'react-router-dom'
import { Play, FileText } from "lucide-react";


const Home = () => {
  return (
    <>
     <Sidebar />
     <div className="home-main">
        
        {/* Hero Section */}
        <div className="hero-section">
          <h1>
            Turn YouTube Videos & PDFs into <br />
            <span className="highlight-text">Interactive Learning</span>
          </h1>
          <p className="hero-subtitle">Quizzes, flashcards & notes — generated instantly</p>
          
          <div className="hero-buttons">
            <Link to="/video" className="btn-primary">
              <Play size={18} fill="currentColor" />
              Paste YouTube Link
            </Link>
            
            <Link to="/pdf" className="btn-secondary">
              <FileText size={18} />
              Upload PDF
            </Link>
          </div>
        </div>

        {/* How It Works Section */}
        <div className="how-it-works-section">
           <h2>How It Works</h2>
           
           <div className="how-it-works-content">
              <div className="steps-container">
                <div className="step-item">
                  <div className="step-number">1</div>
                  <div className="step-text">
                    <h3>Paste a YouTube link or upload a PDF</h3>
                  </div>
                </div>
                <div className="step-line"></div>
                
                <div className="step-item">
                  <div className="step-number">2</div>
                  <div className="step-text">
                    <h3>Generate quizzes, flashcards & notes</h3>
                  </div>
                </div>
                <div className="step-line"></div>

                <div className="step-item">
                   <div className="step-number">3</div>
                   <div className="step-text">
                     <h3>Study with interactive quizzes & flashcards</h3>
                   </div>
                </div>
              </div>

              <div className="visual-container">
                 <div className="app-window">
                    <div className="window-header">
                       <div className="dots">
                         <span></span><span></span><span></span>
                       </div>
                       <div className="address-bar">localhost:5173/video</div>
                    </div>
                    <div className="window-content">
                       <video 
                        src={video_demo} 
                        muted 
                        loop 
                        autoPlay 
                        playsInline
                        className="demo-video"
                       />
                    </div>
                 </div>
              </div>
           </div>
        </div>

     </div>
    </>
  )
}

export default Home
