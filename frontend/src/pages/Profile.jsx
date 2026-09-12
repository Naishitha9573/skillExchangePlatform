import {useEffect,useState} from 'react';
import {Save,LogOut,Camera,Star,Check} from 'lucide-react';
import {useNavigate} from 'react-router-dom';
import api,{errorMessage} from '../services/api';
import {useAuth} from '../context/AuthContext';

export default function Profile() {
  const {user,logout,updateUser} = useAuth();
  const navigate = useNavigate();
  const [form,setForm] = useState({
    full_name: user.full_name,
    bio: user.bio || '',
    location: user.location || '',
    avatar_url: user.avatar_url || ''
  });
  const [saved,setSaved] = useState(false);
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState('');
  const [ratings,setRatings] = useState([]);

  useEffect(() => {
    api.get('/ratings').then(r => setRatings(r.data)).catch(() => {});
  }, []);

  const change = (key,value) => { setForm(c => ({...c,[key]:value})); setSaved(false); };

  const save = async event => {
    event.preventDefault();
    setBusy(true); setError('');
    try {
      const response = await api.put('/users/me', form);
      updateUser(response.data);
      setSaved(true);
    } catch(e) {
      setError(errorMessage(e,'Could not save your profile.'));
    } finally {
      setBusy(false);
    }
  };

  const avgRating = ratings.length
    ? (ratings.reduce((s,r) => s+r.score,0) / ratings.length).toFixed(1)
    : null;

  return (
    <main className="container narrow page-transition">
      <div className="profilehead">
        <div className="profile-avatar-wrap">
          <div className="avatar large">{user.full_name[0]}</div>
          {user.avatar_url && (
            <img
              className="avatar-img large"
              src={user.avatar_url}
              alt={user.full_name}
              onError={e => { e.target.style.display='none'; }}
            />
          )}
        </div>
        <div>
          <h1>{user.full_name}</h1>
          <p>{user.email}</p>
          {avgRating && (
            <span className="profile-rating">
              <Star size={13} fill="currentColor"/> {avgRating} rating · {ratings.length} review{ratings.length!==1?'s':''}
            </span>
          )}
        </div>
      </div>

      <form className="card form" onSubmit={save}>
        <label className="field">
          <span>Full name</span>
          <input required minLength={2} maxLength={120} value={form.full_name} onChange={e => change('full_name',e.target.value)}/>
        </label>
        <label className="field">
          <span>Location</span>
          <input maxLength={120} placeholder="City or time zone" value={form.location} onChange={e => change('location',e.target.value)}/>
        </label>
        <label className="field">
          <span>Bio <small>Tell your future learning partners who you are</small></span>
          <textarea rows={5} maxLength={2000} placeholder="What do you love to teach and learn?" value={form.bio} onChange={e => change('bio',e.target.value)}/>
        </label>
        <label className="field">
          <span><Camera size={13}/> Avatar URL <small>optional</small></span>
          <input type="url" maxLength={500} placeholder="https://..." value={form.avatar_url} onChange={e => change('avatar_url',e.target.value)}/>
        </label>

        {error && <div className="error" role="alert">{error}</div>}
        {saved && (
          <div className="successbox" role="status">
            <Check size={15}/> Your profile is up to date.
          </div>
        )}

        <button className="button full" disabled={busy}>
          <Save size={16}/>{busy ? 'Saving…' : 'Save profile'}
        </button>
        <button type="button" className="danger full" onClick={() => { logout(); navigate('/'); }}>
          <LogOut size={16}/> Log out
        </button>
      </form>
    </main>
  );
}
