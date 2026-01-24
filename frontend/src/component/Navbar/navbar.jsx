import './navbar.css'
import DialpadIcon from '@/components/ui/dialpad-icon'
import DotsHorizontalIcon from '@/components/ui/dots-horizontal-icon'
import UserIcon from '@/components/ui/user-icon'


const Navbar = () => {
  return (
    <nav className="nav-flex">
      <div className="nav-left">
        <DialpadIcon className="menu-icon" />
      </div>

      <div className="nav-center">
        <h1>EdTube</h1>
      </div>
      <div className="nav-right">
        <DotsHorizontalIcon className="more-icon" /><span>MORE</span>
        <UserIcon className="profile-icon" /><span>SIGN-IN</span>
      </div>
    </nav>
  )
}

export default Navbar