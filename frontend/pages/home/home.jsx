import React from 'react'
import './home.css'
import Sidebar from '../../component/Sidebar/sidebar.jsx'

const Home = () => {
  return (
    <>
     <Sidebar />
     <div className="home-main">
        <h2>Welcome to EdTube</h2>
        <p>Your gateway to educational videos and resources.</p>
     </div>

    </>
  )
}

export default Home