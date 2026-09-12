import {useCallback,useEffect,useRef,useState} from 'react';
import {Bell,Check} from 'lucide-react';
import api from '../services/api';
import {useRealtime} from '../context/RealtimeContext';
import {dateTime} from '../services/dates';

export default function NotificationBell() {
  const {subscribe, status} = useRealtime();
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState([]);
  const [error, setError] = useState('');
  const ref = useRef(null);

  const load = useCallback(() =>
    api.get('/notifications').then(r => { setRows(r.data); setError(''); }).catch(() => setError('Could not refresh notifications.')),
  []);

  useEffect(() => { load(); return subscribe(event => { if (['ready', 'notifications.changed'].includes(event.type)) load(); }); }, [load, subscribe]);
  useEffect(() => { if (status === 'connected') return; const timer = setInterval(load, 30000); return () => clearInterval(timer); }, [status, load]);
  useEffect(() => {
    const close = e => { if (!ref.current?.contains(e.target)) setOpen(false); };
    const escape = e => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('pointerdown', close);
    document.addEventListener('keydown', escape);
    return () => { document.removeEventListener('pointerdown', close); document.removeEventListener('keydown', escape); };
  }, []);

  const mark = async n => {
    if (n.read) return;
    try { await api.patch(`/notifications/${n.id}/read`); setRows(current => current.map(x => x.id === n.id ? {...x, read: true} : x)); }
    catch { setError('Could not mark notification as read.'); }
  };

  const unread = rows.filter(n => !n.read).length;

  return (
    <div className="notifwrap" ref={ref}>
      <button
        className={`notifbtn ${unread > 0 ? 'has-unread' : ''}`}
        aria-label={`Notifications${unread ? `, ${unread} unread` : ''}`}
        aria-expanded={open}
        onClick={() => { setOpen(!open); if (!open) load(); }}
      >
        <Bell size={19}/>
        {unread > 0 && <b>{unread}</b>}
      </button>

      {open && (
        <div className="notifpanel" style={{animation: 'notif-slide .2s ease'}}>
          <div className="notifhead">
            <strong>Notifications</strong>
            <span>{unread} new</span>
          </div>

          {error && (
            <div className="notifempty" role="alert">
              {error}
              <button className="ghost small" onClick={load}>Retry</button>
            </div>
          )}

          {rows.length ? rows.map(n => (
            <button className={`notification ${!n.read ? 'unread' : ''}`} key={n.id} onClick={() => mark(n)}>
              <span className="notifdot"/>
              <span>
                <strong>{n.title}</strong>
                <small>{n.body}</small>
                <em>{dateTime(n.created_at)}</em>
              </span>
              {n.read && <Check size={14}/>}
            </button>
          )) : !error && (
            <div className="notifempty">You're all caught up.</div>
          )}
        </div>
      )}
    </div>
  );
}
