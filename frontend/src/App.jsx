import {lazy,Suspense,useEffect} from 'react';
import {BrowserRouter,Routes,Route,Navigate,useLocation} from 'react-router-dom';
import {AuthProvider} from './context/AuthContext';
import {RealtimeProvider} from './context/RealtimeContext';
import Protected from './components/Protected';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import ErrorBoundary from './components/ErrorBoundary';
import Landing from './pages/Landing';
import {Login,Register} from './pages/Auth';
import './styles.css';
import './collaboration.css';
import './premium.css';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Feed = lazy(() => import('./pages/Feed'));
const AddSkill = lazy(() => import('./pages/AddSkill'));
const SkillDetail = lazy(() => import('./pages/SkillDetail'));
const Swaps = lazy(() => import('./pages/Swaps'));
const Messages = lazy(() => import('./pages/Messages'));
const Profile = lazy(() => import('./pages/Profile'));
const Coach = lazy(() => import('./pages/Coach'));
const Leaderboard = lazy(() => import('./pages/Leaderboard'));
const Sessions = lazy(() => import('./pages/Sessions'));
const VideoSession = lazy(() => import('./pages/VideoSession'));
const Innovation = lazy(() => import('./pages/Innovation'));
const JudgeMode = lazy(() => import('./pages/JudgeMode'));
const Legal = lazy(() => import('./pages/Legal'));
const MemberProfile = lazy(() => import('./pages/MemberProfile'));

function ScrollPosition() {
  const {pathname, hash} = useLocation();
  useEffect(() => {
    if (hash) {
      const timer = setTimeout(() => document.getElementById(hash.slice(1))?.scrollIntoView({behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}), 100);
      return () => clearTimeout(timer);
    }
    window.scrollTo(0, 0);
  }, [pathname, hash]);
  return null;
}

const privatePage = Page => <Protected><Page/></Protected>;

const LoadingFallback = () => (
  <div className="container loading page-transition" role="status">
    <span className="loading-orbit" style={{margin: '0 auto 16px', display: 'block', width: 28, height: 28}} />
    Opening your learning space…
  </div>
);

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <RealtimeProvider>
            <a className="skip-link" href="#app-content">Skip to content</a>
            <Navbar/>
            <ScrollPosition/>
            <div id="app-content">
              <Suspense fallback={<LoadingFallback/>}>
                <Routes>
                  <Route path="/" element={<Landing/>}/>
                  <Route path="/login" element={<Login/>}/>
                  <Route path="/register" element={<Register/>}/>
                  <Route path="/privacy" element={<Legal type="privacy"/>}/>
                  <Route path="/terms" element={<Legal type="terms"/>}/>
                  <Route path="/feed" element={<Feed/>}/>
                  <Route path="/members/:id" element={<MemberProfile/>}/>
                  <Route path="/skill/:id" element={privatePage(SkillDetail)}/>
                  <Route path="/dashboard" element={privatePage(Dashboard)}/>
                  <Route path="/add-skill" element={privatePage(AddSkill)}/>
                  <Route path="/swaps" element={privatePage(Swaps)}/>
                  <Route path="/messages/:otherId?" element={privatePage(Messages)}/>
                  <Route path="/profile" element={privatePage(Profile)}/>
                  <Route path="/coach" element={privatePage(Coach)}/>
                  <Route path="/leaderboard" element={privatePage(Leaderboard)}/>
                  <Route path="/sessions" element={privatePage(Sessions)}/>
                  <Route path="/sessions/:sessionId/call" element={privatePage(VideoSession)}/>
                  <Route path="/innovation" element={privatePage(Innovation)}/>
                  <Route path="/judge" element={privatePage(JudgeMode)}/>
                  <Route path="*" element={<Navigate to="/" replace/>}/>
                </Routes>
              </Suspense>
            </div>
            <Footer/>
          </RealtimeProvider>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
