import './navbar.css'
import menu_icon from '../../assets/menu.png'
import more_icon from '../../assets/more.png'
import profile_icon from '../../assets/profile.png'
import home_icon from '../../assets/home.png'
import { Link } from 'react-router-dom'


const Navbar = () => {
  return (
    <nav className="nav-flex">
      <div className="nav-left">
        <h1>EdTube</h1>
        {/* <img src={menu_icon} alt="menu icon" className="menu-icon"/> */}
      </div>

      <div className="nav-center">
        {/* <img src={home_icon} alt="home icon" class="home-icon"/> */}
      </div>

      <div className="nav-right">
        <Link to="/" className="sidebar-link">
          <div className="sidebar-item">
            <div className="box">
              <img src={home_icon} alt="home icon" />
            </div>
            <span>HOME</span>
          </div>
        </Link>
        <div className="box">
          <img src={more_icon} alt="more icon" className="more-icon" />
        </div>
        <span>MORE</span>

        <div className="box">
          <img src={profile_icon} alt="profile icon" className="profile-icon" />
        </div>
        <span>SIGN-IN</span>
      </div>
    </nav>
  )
}

export default Navbar