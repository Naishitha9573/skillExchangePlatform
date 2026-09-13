import {useEffect,useState} from 'react';
import {Save,LogOut,Camera,Star,Check,Users,ArrowUpRight} from 'lucide-react';
import {Link,useNavigate} from 'react-router-dom';
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
  const [skills,setSkills] = useState([]);
  const [ratingAverage,setRatingAverage] = useState(null);

  useEffect(() => {
    api.get('/community/members/'+user.id).then(r => {setRatings(r.data.reviews);setSkills(r.data.skills);setRatingAverage(r.data.review_count?r.data.rating:null);}).catch(() => setError('Could not load your skills and received reviews. Refresh to try again.'));
  }, [user.id]);

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

  const avgRating = ratingAverage;
  const complete = [form.full_name,form.bio,form.location,skills.some(s=>s.type==='Offering'),skills.some(s=>s.type==='Requesting')].filter(Boolean).length;

  return (
    <main className="container profile-page page-transition">
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

      <div className="workspace-columns"><form className="card form" onSubmit={save}>
        <div className="sectionhead"><div><h2>Your exchange profile</h2><p>Help your future learning partners get to know you.</p></div></div>
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
      </form><aside className="workspace-aside"><section className="guide-card"><Users size={26}/><h2>A profile that opens doors.</h2><p>Share a little about yourself, where you learn from, and the skills you bring.</p><div className="profile-completeness" role="progressbar" aria-label="Exchange profile completeness" aria-valuenow={complete*20} aria-valuemin={0} aria-valuemax={100}><span style={{width:complete*20+'%'}}/></div><small>{complete} of 5 profile essentials ready</small>{[['Your teaching skills','Offering'],['Your learning goals','Requesting']].map(([title,type])=><div key={type} style={{marginTop:20}}><strong style={{fontSize:12}}>{title}</strong>{skills.filter(s=>s.type===type).map(s=><Link className="dashboard-mini-row" key={s.id} to={'/skill/'+s.id}><div><strong>{s.title}</strong><small>{s.level}</small></div><ArrowUpRight size={13}/></Link>)}<Link className="text-link" to={'/add-skill?type='+type}>Add {type==='Offering'?'a teaching skill':'a learning goal'} <ArrowUpRight size={13}/></Link></div>)}<Link className="text-link" to={'/members/'+user.id}>View your public profile <ArrowUpRight size={14}/></Link></section><section className="guide-card warm"><Star size={24}/><h2>What your partners say</h2>{ratings.length?ratings.slice(0,3).map(r=><article className="received-review" key={r.id}><strong>{r.author}</strong> <span>{r.score}/5</span><p>{r.review||'Rated your completed exchange.'}</p></article>):<p>Received reviews appear here after an exchange. A thoughtful first session is a great place to begin.</p>}</section></aside></div>
    </main>
  );
}
