import { useEffect, useState } from 'react';
import { Check, X, ArrowRightLeft, MessageCircle, RefreshCw, Star, Clock3 } from 'lucide-react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

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
  const [rows, setRows] = useState([]);
  const [tab, setTab] = useState('all');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [actionId, setActionId] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // IMPORTANT: this effect itself is synchronous and returns a cleanup function.
  // Never make a React effect callback async or return an Axios Promise.
  useEffect(() => {
    let active = true;

    const fetchSwaps = async () => {
      if (!user?.id) {
        if (active) setLoading(false);
        return;
      }

      try {
        if (active) {
          setLoading(true);
          setError('');
        }

        const response = await api.get('/swaps');
        const data = Array.isArray(response.data) ? response.data : [];

        if (active) setRows(data.map(normalizeSwap));
      } catch (err) {
        if (!active) return;
        const detail = err?.response?.data?.detail;
        setError(
          typeof detail === 'string'
            ? detail
            : 'Could not load your swaps. Make sure the FastAPI backend is running.'
        );
        setRows([]);
      } finally {
        if (active) setLoading(false);
      }
    };

    fetchSwaps();

    return () => {
      active = false;
    };
  }, [user?.id]);

  const load = async () => {
    if (!user?.id || refreshing) return;
    setRefreshing(true);
    setError('');
    try {
      const response = await api.get('/swaps');
      const data = Array.isArray(response.data) ? response.data : [];
      setRows(data.map(normalizeSwap));
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Could not refresh your swaps.');
    } finally {
      setRefreshing(false);
    }
  };

  const update = async (id, status) => {
    setActionId(id);
    setError('');
    setSuccess('');

    try {
      await api.patch(`/swaps/${id}`, { status });
      setSuccess(`Swap ${status}.`);

      const response = await api.get('/swaps');
      const data = Array.isArray(response.data) ? response.data : [];
      setRows(data.map(normalizeSwap));
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'The swap could not be updated. Please try again.');
    } finally {
      setActionId(null);
    }
  };

  const filtered = tab === 'all' ? rows : rows.filter((row) => row.status === tab);
  const counts = rows.reduce(
    (acc, row) => ({ ...acc, [row.status]: (acc[row.status] || 0) + 1 }),
    { all: rows.length }
  );

  return (
    <main className="container">
      <div className="pageintro">
        <div>
          <div className="eyebrow"><ArrowRightLeft size={15} /> Exchange center</div>
          <h1>Your skill swaps</h1>
          <p>Track proposals, accepted exchanges and completed connections.</p>
        </div>
        <button className="ghost small" onClick={load} disabled={refreshing || loading}>
          <RefreshCw size={15} className={refreshing ? 'spin' : ''} />
          {refreshing ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="errorbox card">
          <div><strong>Swaps could not be loaded</strong><span>{error}</span></div>
          <button className="button small" onClick={load} disabled={refreshing}>Try again</button>
        </div>
      )}

      {success && <div className="successbox"><Check size={16} /><span>{success}</span></div>}

      <div className="swap-tabs card">
        {STATUS_TABS.map(([value, label]) => (
          <button key={value} className={tab === value ? 'active' : ''} onClick={() => setTab(value)}>
            {label}<b>{counts[value] || 0}</b>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading">Loading your exchanges…</div>
      ) : (
        <div className="stack">
          {filtered.map((swap) => {
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
                    <div className="avatar">{other.full_name?.[0] || '?'}</div>
                    <div>
                      <strong>{other.full_name || 'Unknown user'}</strong>
                      <span>{incoming ? 'wants your help' : 'you proposed a swap'}</span>
                    </div>
                  </div>
                  <div className="exchange">
                    <b>{swap.offered_skill.title}</b>
                    <span>↔</span>
                    <b>{swap.requested_skill.title}</b>
                  </div>
                  <span className={`status ${swap.status}`}>{swap.status}</span>
                </div>

                {swap.message && <p className="swapmsg">“{swap.message}”</p>}

                <div className="swapmeta">
                  <span><Clock3 size={13} /> {swap.created_at ? new Date(swap.created_at).toLocaleString() : 'Recently'}</span>
                  <span>Swap #{swap.id}</span>
                </div>

                <div className="swapactions">
                  {canAccept && <>
                    <button className="button small" disabled={busy} onClick={() => update(swap.id, 'accepted')}>
                      <Check size={15} /> {busy ? 'Updating…' : 'Accept'}
                    </button>
                    <button className="danger small" disabled={busy} onClick={() => update(swap.id, 'rejected')}>
                      <X size={15} /> Decline
                    </button>
                  </>}

                  {canComplete && (
                    <button className="button small" disabled={busy} onClick={() => update(swap.id, 'completed')}>
                      <Check size={15} /> {busy ? 'Saving…' : 'Mark completed'}
                    </button>
                  )}

                  {canCancel && (
                    <button className="ghost small" disabled={busy} onClick={() => update(swap.id, 'cancelled')}>
                      Cancel
                    </button>
                  )}

                  {other.id && (
                    <Link className="ghost small" to={`/messages/${other.id}`}>
                      <MessageCircle size={15} /> Message
                    </Link>
                  )}

                  {(swap.status === 'accepted' || swap.status === 'completed') && other.id && (
                    <Link className="ghost small" to={`/sessions?swap=${swap.id}&user=${other.id}`}>
                      Schedule session
                    </Link>
                  )}

                  {swap.status === 'completed' && (
                    <span className="verified"><Star size={14} /> Exchange complete</span>
                  )}
                </div>
              </article>
            );
          })}

          {!filtered.length && !error && (
            <div className="empty card">
              <ArrowRightLeft size={30} />
              <h3>{tab === 'all' ? 'No swaps yet' : `No ${tab} swaps`}</h3>
              <p>{tab === 'all' ? 'Find a skill and propose your first exchange.' : 'Try another status filter or explore more skills.'}</p>
              <Link className="button small" to="/feed">Explore skills</Link>
            </div>
          )}
        </div>
      )}
    </main>
  );
}
