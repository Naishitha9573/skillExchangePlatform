import {useEffect,useRef,useState} from 'react';
import {Link,useLocation,useNavigate} from 'react-router-dom';
import {Sparkles,LayoutDashboard,Compass,MessageCircle,ArrowRightLeft,UserCircle,LogOut,BrainCircuit,Trophy,CalendarDays,Presentation,Menu,X} from 'lucide-react';
import {useAuth} from '../context/AuthContext';
import {useRealtime} from '../context/RealtimeContext';
import NotificationBell from './NotificationBell';

const links=[
  ['/dashboard','Dashboard',LayoutDashboard],
  ['/feed','Explore',Compass],
  ['/swaps','Swaps',ArrowRightLeft],
  ['/messages','Messages',MessageCircle],
  ['/sessions','Sessions',CalendarDays],
  ['/coach','AI Coach',BrainCircuit],
  ['/leaderboard','Leaderboard',Trophy],
  ['/innovation','Innovation',Sparkles],
  ['/judge','Judge Demo',Presentation]
];

const bottomLinks = [
  ['/dashboard','Home',LayoutDashboard],
  ['/feed','Explore',Compass],
  ['/swaps','Swaps',ArrowRightLeft],
  ['/messages','Messages',MessageCircle],
  ['/sessions','Sessions',CalendarDays],
];

export default function Navbar() {
  const {user,logout} = useAuth();
  const {unread} = useRealtime();
  const location = useLocation();
  const navigate = useNavigate();
  const [open,setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => setOpen(false), [location.pathname]);

  useEffect(() => {
    const close = e => { if (!ref.current?.contains(e.target)) setOpen(false); };
    const escape = e => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('pointerdown', close);
    document.addEventListener('keydown', escape);
    return () => {
      document.removeEventListener('pointerdown', close);
      document.removeEventListener('keydown', escape);
    };
  }, []);

  const isActive = path => location.pathname === path || location.pathname.startsWith(path + '/');

  const navLink = ([path, title, Icon]) => (
    <Link key={path} className={isActive(path) ? 'active' : ''} to={path}>
      <Icon size={16}/>{title}
      {path === '/messages' && unread > 0 && (
        <b className="nav-unread" aria-label={`${unread} unread messages`}>{unread > 99 ? '99+' : unread}</b>
      )}
    </Link>
  );

  return (
    <>
      <header className="nav" ref={ref}>
        <Link to={user ? '/dashboard' : '/'} className="brand">
          <span className="brandIcon"><Sparkles size={17}/></span>
          SkillSwap<span className="ai">AI</span>
        </Link>

        {user ? (
          <nav className="navlinks" aria-label="Main navigation">
            {links.slice(0, 5).map(navLink)}
          </nav>
        ) : (
          <nav className="public-links">
            <Link to="/#how-it-works">How it works</Link>
            <Link to="/#why-skillswap">Why SkillSwap</Link>
          </nav>
        )}

        <div className="navright">
          {user ? (
            <>
              <NotificationBell/>
              <Link className="iconlink" aria-label="Your profile" to="/profile">
                <UserCircle size={20}/><span>{user.full_name.split(' ')[0]}</span>
              </Link>
              <button
                className="ghost icon-button nav-menu-button"
                aria-label={open ? 'Close navigation' : 'Open navigation'}
                aria-expanded={open}
                aria-controls="navigation-menu"
                onClick={() => setOpen(!open)}
              >
                {open ? <X size={20}/> : <Menu size={20}/>}
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="ghost">Log in</Link>
              <Link to="/register" className="button small">Get started <ArrowRightLeft size={14}/></Link>
            </>
          )}
        </div>

        {user && open && (
          <nav id="navigation-menu" className="navigation-menu card" aria-label="More navigation">
            {links.map(navLink)}
            <Link to="/profile"><UserCircle size={16}/> Your profile</Link>
            <button onClick={() => { logout(); navigate('/'); }}>
              <LogOut size={16}/> Sign out
            </button>
          </nav>
        )}
      </header>

      {/* Mobile bottom navigation */}
      {user && (
        <div className="mobile-bottom-nav">
          <nav aria-label="Mobile navigation">
            {bottomLinks.map(([path, title, Icon]) => (
              <Link key={path} to={path} className={isActive(path) ? 'active' : ''} aria-label={title}>
                <Icon size={19}/>
                <span>{title}</span>
                {path === '/messages' && unread > 0 && (
                  <b className="nav-unread" aria-label={`${unread} unread`}>{unread > 99 ? '99+' : unread}</b>
                )}
              </Link>
            ))}
          </nav>
        </div>
      )}
    </>
  );
}
