import React from 'react'
import './home.css'
import Sidebar from '../../component/Sidebar/sidebar.jsx'
import video_demo from '../../assets/demo.mp4'
import { Zap, BookOpen, Sparkles } from "lucide-react";


const Home = () => {
  return (
    <>
      <Sidebar />
      <div className="home-main">
        <h1>Welcome to EdTube</h1>
        <p>Your gateway to educational videos and resources.</p>
        <div className="home-content">
          Turn YouTube Videos And PDF into
        </div>
        <span className="home-content-span">Interative Learing</span>
        <p>Paste any YouTube URL or PDF and instantly generate quizzes , flashcards ,important notes
          from the video content. Study smarter, not harder.</p>
        <div className="home-content-lower">
          <h2>How It Works</h2>

          <div className="video-wrapper">
            <video
              src={video_demo}
              controls
              autoPlay
              muted
              loop
              playsInline
            />
          </div>

          <div className="features-container">

            <div className="feature-card">
              <div className="feature-icon">
                <Zap size={32} />
              </div>
              <h3 className="feature-title">Instant Generation</h3>
              <p className="feature-desc">
                Get your quizzes and flashcards in seconds. No waiting, no hassle.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <BookOpen size={32} />
              </div>
              <h3 className="feature-title">Smart Extraction</h3>
              <p className="feature-desc">
                AI identifies key concepts and important information automatically.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <Sparkles size={32} />
              </div>
              <h3 className="feature-title">Interactive Learning</h3>
              <p className="feature-desc">
                Engage with quizzes and flashcards for better retention.
              </p>
            </div>

          </div>

        </div>
      </div>


    </>
  )
}

export default Home