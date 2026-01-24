import React from 'react'
import './sidebar.css'
import HomeIcon from '@/components/ui/home-icon'
import PlayerIcon from '@/components/ui/player-icon'
import FileDescriptionIcon from '@/components/ui/file-description-icon'
import { Link } from 'react-router-dom'

const Sidebar = () => {
    return (
        <div className="sidebar-main">
            <div className="sidebar-upper">
                <Link to="/">
                    <div>
                        <HomeIcon className="home-icon" />
                        <span>HOME</span>
                    </div>
                </Link>
                <Link to="/video">
                    <div>
                        <PlayerIcon className="video-icon" />
                        <span>VIDEO</span>
                    </div>
                </Link>
                <Link to="/video/any/any">
                    <div>
                        <FileDescriptionIcon className="pdf-icon" />
                        <span>PDF</span>
                    </div>
                </Link>
            </div>
            <hr className="sidebar-divider" />
            <div className="sidebar-lower">
                <h3>HISTORY</h3>
            </div>

        </div>
    )
}

export default Sidebar