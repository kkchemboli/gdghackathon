import React from 'react'
import './sidebar.css'
import video_icon from '../../assets/video.png'
import pdf_icon from '../../assets/pdf.png'
import { Link, useLocation } from 'react-router-dom'

const Sidebar = () => {
  const location = useLocation();

  return (
    <div className="sidebar-main">
      <div className="sidebar-upper">

        <Link to="/video" className={`sidebar-link ${location.pathname.includes('/video') ? 'active' : ''}`}>
          <div className="sidebar-item">
            <div className="box">
              <img src={video_icon} alt="video icon" />
            </div>
            <span>Video</span>
          </div>
        </Link>

        <Link to="/pdf" className={`sidebar-link ${location.pathname.includes('/pdf') ? 'active' : ''}`}>
          <div className="sidebar-item">
            <div className="box">
              <img src={pdf_icon} alt="pdf icon" />
            </div>
            <span>PDF</span>
          </div>
        </Link>

      </div>

      <div className="sidebar-history">
        <h3>HISTORY</h3>
        {/* History items would go here */}
      </div>
    </div>
  );
};

export default Sidebar;
