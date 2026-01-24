import React from 'react'
import './sidebar.css'
import home_icon from '../../assets/home.png'
import video_icon from'../../assets/video.png'
import pdf_icon from '../../assets/pdf.png'
import { Link } from 'react-router-dom'
const Sidebar = () => {
  return (
    <div className="sidebar-main">
      <div className="sidebar-upper">

        {/* <Link to="/" className="sidebar-link">
          <div className="sidebar-item">
            <div className="box">
              <img src={home_icon} alt="home icon" />
            </div>
            <span>HOME</span>
          </div>
        </Link> */}

        <Link to="/video" className="sidebar-link">
          <div className="sidebar-item">
            <div className="box">
              <img src={video_icon} alt="video icon" />
            </div>
            <span>VIDEO</span>
          </div>
        </Link>

        <Link to="/video/any/any" className="sidebar-link">
          <div className="sidebar-item">
            <div className="box">
              <img src={pdf_icon} alt="pdf icon" />
            </div>
            <span>PDF</span>
          </div>
        </Link>

      </div>

      <hr className="sidebar-divider" />

      <div className="sidebar-lower">
        <h3>HISTORY</h3>
      </div>
    </div>
  );
};

export default Sidebar;


