import { useEffect, useState } from 'react';
import { Check, X, ArrowRightLeft, MessageCircle, RefreshCw, Star, Clock3 } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useRealtime } from '../context/RealtimeContext';
import ReviewForm from '../components/ReviewForm';
import { dateTime } from '../services/dates';
import { SkeletonCard } from '../components/Skeleton';

const STATUS_TABS = [
  ['all', 'All'],
  ['pending', 'Pending'],
  ['accepted', 'Accepted'],
  ['completed', 'Completed'],
  ['rejected', 'Rejected'],
  ['cancelled', 'Cancelled'],
];

function normalizeSwap(item) {
  return {
    ...item,
    requester: item.requester || { id: null, full_name: 'Unknown user' },
    receiver: item.receiver || { id: null, full_name: 'Unknown user' },
    offered_skill: item.offered_skill || { id: null, title: 'Offered skill' },
    requested_skill: item.requested_skill || { id: null, title: 'Requested skill' },
    status: String(item.status || 'pending').toLowerCase(),
  };
}

export default function Swaps() {
  const { user } = useAuth();
  const { subscribe } = useRealtime();
  const [params, setParams] = useSearchParams();
  const [ratings, setRatings] = useState([]);
  const [reviewSwap, setReviewSwap] = useState(null);
  const [rows, setRows] = useState([]);
  const [tab, setTab] = useState('all');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [actionId, setActionId] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const load = async () => {
    if (refreshing) return;
    setRefreshing(true); setError('');
    try {
      const [a,b] = await Promise.all([api.get('/swaps'), api.get('/ratings')]);
      setRows((Array.isArray(a.data) ? a.data : []).map(normalizeSwap));
      setRatings(b.data);
    } catch(err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Could not refresh your swaps.');
    } finally {
      setRefreshing(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    let active = true;
    const fetchSwaps = async () => {
      if (!user?.id) { setLoading(false); return; }
      try {
        setLoading(true); setError('');
        const [a,b] = await Promise.all([api.get('/swaps'), api.get('/ratings')]);
        if (active) {
          setRows((Array.isArray(a.data) ? a.data : []).map(normalizeSwap));
          setRatings(b.data);
        }
      } catch(err) {
        if (!active) return;
        const detail = err?.response?.data?.detail;
        setError(typeof detail === 'string' ? detail : 'Could not load your swaps. Make sure the backend is running.');
        setRows([]);
      } finally {
        if (active) setLoading(false);
      }
    };
    fetchSwaps();
    return () => { active = false; };
  }, [user?.id]);

  // Real-time refresh
  useEffect(() => {
    const refresh = () => Promise.all([api.get('/swaps'), api.get('/ratings')]).then(([a,b]) => {
      setRows(a.data.map(normalizeSwap)); setRatings(b.data);
    }).catch(() => setError('Could not refresh your exchanges.'));
    const unsubscribe = subscribe(event => { if (['ready','swaps.changed'].includes(event.type)) refresh(); });
    window.addEventListener('focus', refresh);
    return () => { unsubscribe(); window.removeEventListener('focus', refresh); };
  }, [subscribe]);

  // Deep-link ?review=swap_id
  useEffect(() => {
    const requested = params.get('review');
    if (!requested || loading) return;
    const swap = rows.find(row => String(row.id) === requested && row.status === 'completed');
    if (swap && !ratings.some(r => r.swap_id === swap.id)) setReviewSwap(swap);
    setParams({}, {replace: true});
  }, [params, setParams, rows, loading, ratings]);

  const update = async (id, status) => {
    setActionId(id); setError(''); setSuccess('');
    try {
      await api.patch(`/swaps/${id}`, { status });
      setSuccess(`Swap ${status}.`);
      const [a,b] = await Promise.all([api.get('/swaps'), api.get('/ratings')]);
      setRows((Array.isArray(a.data) ? a.data : []).map(normalizeSwap));
      setRatings(b.data);
    } catch(err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'The swap could not be updated. Please try again.');
    } finally {
      setActionId(null);
    }
  };

  const filtered = tab === 'all' ? rows : rows.filter(row => row.status === tab);
  const counts = rows.reduce((acc,row) => ({ ...acc, [row.status]: (acc[row.status]||0)+1 }), { all: rows.length });

  return (
    <main className="container page-transition">
      <div className="pageintro">
        <div>
          <div className="eyebrow"><ArrowRightLeft size={15}/> Exchange center</div>
          <h1>Your skill swaps</h1>
          <p>Track proposals, accepted exchanges and completed connections.</p>
        </div>
        <button className="ghost small" onClick={load} disabled={refreshing||loading}>
          <RefreshCw size={15} className={refreshing ? 'spin' : ''}/>
          {refreshing ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="errorbox card">
          <div><strong>Swaps could not be loaded</strong><span>{error}</span></div>
          <button className="button small" onClick={load} disabled={refreshing}>Try again</button>
        </div>
      )}
      {success && <div className="successbox"><Check size={16}/><span>{success}</span></div>}

      <div className="swap-tabs card">
        {STATUS_TABS.map(([value,label]) => (
          <button key={value} className={tab===value?'active':''} onClick={() => setTab(value)}>
            {label}<b>{counts[value]||0}</b>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="stack">
          {Array.from({length: 4}, (_,i) => <SkeletonCard key={i} lines={2}/>)}
        </div>
      ) : (
        <div className="stack">
          {filtered.map(swap => {
            const incoming = Number(swap.receiver.id) === Number(user?.id);
            const other = incoming ? swap.requester : swap.receiver;
            const canAccept = incoming && swap.status === 'pending';
            const canCancel = !incoming && swap.status === 'pending';
            const canComplete = swap.status === 'accepted';
            const busy = actionId === swap.id;
            return (
              <article className="swap card" key={swap.id}>
                <div className="swapmain">
                  <div className="swappeople">
                    <div className="avatar">{other.full_name?.[0]||'?'}</div>
                    <div>
                      <strong>{other.full_name||'Unknown user'}</strong>
                      <span>{incoming?'wants your help':'you proposed a swap'}</span>
                    </div>
                  </div>
                  <div className="exchange">
                    <b>{swap.offered_skill.title}</b>
                    <span>↔</span>
                    <b>{swap.requested_skill.title}</b>
                  </div>
                  <span className={`status ${swap.status}`}>{swap.status}</span>
                </div>

                {swap.message && <p className="swapmsg">"{swap.message}"</p>}

                <div className="swapmeta">
                  <span><Clock3 size={13}/> {swap.created_at ? dateTime(swap.created_at) : 'Recently'}</span>
                  <span>Swap #{swap.id}</span>
                </div>

                <div className="swapactions">
                  {canAccept && <>
                    <button className="button small" disabled={busy} onClick={() => update(swap.id,'accepted')}>
                      <Check size={15}/> {busy?'Updating…':'Accept'}
                    </button>
                    <button className="danger small" disabled={busy} onClick={() => update(swap.id,'rejected')}>
                      <X size={15}/> Decline
                    </button>
                  </>}
                  {canComplete && (
                    <button className="button small" disabled={busy} onClick={() => update(swap.id,'completed')}>
                      <Check size={15}/> {busy?'Saving…':'Mark completed'}
                    </button>
                  )}
                  {canCancel && (
                    <button className="ghost small" disabled={busy} onClick={() => update(swap.id,'cancelled')}>Cancel</button>
                  )}
                  {other.id && (
                    <Link className="ghost small" to={`/messages/${other.id}`}>
                      <MessageCircle size={15}/> Message
                    </Link>
                  )}
                  {(swap.status==='accepted'||swap.status==='completed') && other.id && (
                    <Link className="ghost small" to={`/sessions?swap=${swap.id}&user=${other.id}`}>
                      Schedule session
                    </Link>
                  )}
                  {swap.status==='completed' && (
                    ratings.some(r => r.swap_id===swap.id)
                      ? <span className="verified"><Star size={14}/> Review shared</span>
                      : <button className="button secondary small" onClick={() => setReviewSwap(swap)}>
                          <Star size={14}/> Leave a review
                        </button>
                  )}
                </div>
              </article>
            );
          })}

          {!filtered.length && !error && (
            <div className="empty card">
              <ArrowRightLeft size={30}/>
              <h3>{tab==='all'?'No swaps yet':`No ${tab} swaps`}</h3>
              <p>{tab==='all'?'Find a skill and propose your first exchange.':'Try another status filter or explore more skills.'}</p>
              <Link className="button small" to="/feed">Explore skills</Link>
            </div>
          )}
        </div>
      )}

      {reviewSwap && (
        <ReviewForm
          swap={reviewSwap}
          onClose={() => setReviewSwap(null)}
          onSaved={rating => {
            setRatings(current => [...current, rating]);
            setReviewSwap(null);
            setSuccess('Review shared. Thank you for helping your partner grow.');
          }}
        />
      )}
    </main>
  );
}
