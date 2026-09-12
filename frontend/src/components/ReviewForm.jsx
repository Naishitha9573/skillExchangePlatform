import {useState} from 'react';
import {Star} from 'lucide-react';
import api,{errorMessage} from '../services/api';
import Modal from './Modal';
export default function ReviewForm({swap,onClose,onSaved}){
  const [score,setScore]=useState(5),[review,setReview]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const submit=async event=>{event.preventDefault();setBusy(true);setError('');try{await api.post(`/ratings/${swap.id}`,{score,review:review.trim()});onSaved({swap_id:swap.id,score,review:review.trim()});}catch(e){setError(errorMessage(e,'Could not submit your review.'));}finally{setBusy(false);}};
  return <Modal title="A little feedback goes a long way." onClose={onClose} busy={busy}><form className="review-form" onSubmit={submit}><p>How was your exchange? Help your partner grow and future learners connect.</p><fieldset className="review-stars"><legend>Your rating</legend>{[1,2,3,4,5].map(n=><label key={n}><input type="radio" name="rating" aria-label={`${n} star${n>1?'s':''}`} value={n} checked={score===n} onChange={()=>setScore(n)}/><Star size={30} fill={n<=score?'currentColor':'none'}/></label>)}</fieldset><label className="field"><span>Your reflection (optional)</span><textarea rows={4} maxLength={2000} value={review} onChange={e=>setReview(e.target.value)} placeholder="What helped you learn? What would you share with the next learner?"/></label>{error&&<p className="error" role="alert">{error}</p>}<div className="dialog-actions"><button type="button" className="ghost" disabled={busy} onClick={onClose}>Maybe later</button><button className="button" disabled={busy}>{busy?'Sharing…':'Share review'}</button></div></form></Modal>;
}
