import {useEffect,useState} from 'react';
import {Search,SlidersHorizontal,BrainCircuit} from 'lucide-react';
import api,{errorMessage} from '../services/api';
import SkillCard from '../components/SkillCard';
import {SkeletonCard} from '../components/Skeleton';

export default function Feed() {
  const [skills,setSkills] = useState([]);
  const [search,setSearch] = useState('');
  const [category,setCategory] = useState('');
  const [type,setType] = useState('');
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState('');
  const [retry,setRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError('');
    const timer = setTimeout(() =>
      api.get('/skills', {params:{search,category,skill_type:type}, signal:controller.signal})
        .then(r => setSkills(r.data))
        .catch(e => { if (!controller.signal.aborted) setError(errorMessage(e,'Could not load opportunities. Please try again.')); })
        .finally(() => { if (!controller.signal.aborted) setLoading(false); }),
    250);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [search,category,type,retry]);

  return (
    <main className="container page-transition">
      <div className="pageintro">
        <div>
          <div className="eyebrow"><BrainCircuit size={15}/> Discover</div>
          <h1>Find your next skill exchange</h1>
          <p>Search real people offering and requesting skills.</p>
        </div>
      </div>

      <div className="filters card">
        <label className="search">
          <Search size={18}/>
          <input
            aria-label="Search skills"
            placeholder="Search React, design, Python…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </label>
        <select aria-label="Category" value={category} onChange={e => setCategory(e.target.value)}>
          <option value="">All categories</option>
          {['Technology','Design','Languages','Communication','Business','Creative','Fitness','Cooking','Other']
            .map(v => <option key={v}>{v}</option>)}
        </select>
        <select aria-label="Skill type" value={type} onChange={e => setType(e.target.value)}>
          <option value="">Offer + request</option>
          <option value="Offering">Offering</option>
          <option value="Requesting">Requesting</option>
        </select>
        <SlidersHorizontal size={18}/>
      </div>

      {error ? (
        <div className="errorbox card" role="alert">
          <span>{error}</span>
          <button className="button small" onClick={() => setRetry(n => n+1)}>Try again</button>
        </div>
      ) : loading ? (
        <div className="grid">
          {Array.from({length: 6}, (_,i) => <SkeletonCard key={i}/>)}
        </div>
      ) : (
        <div className="grid">
          {skills.map(s => <SkillCard key={s.id} skill={s}/>)}
        </div>
      )}

      {!loading && !error && !skills.length && (
        <div className="empty card">
          <h3>No matches yet</h3>
          <p>Try a broader search or another category.</p>
        </div>
      )}
    </main>
  );
}
