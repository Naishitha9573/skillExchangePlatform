import {ArrowRightLeft,CalendarDays,Check,CheckCheck,Mic,PhoneOff,Star,Video} from 'lucide-react';
import {Avatar} from './MemberCard';

export const productFeatures = [
  {id:'matching',label:'Smart matching',title:'A good fit goes both ways.',text:'Discover people who can teach what you want to learn, and want something you can share.',link:'/innovation',action:'Find your matches'},
  {id:'chat',label:'Real-time chat',title:'Turn a match into a conversation.',text:'Say hello, agree on a small learning goal, and keep your ideas in one shared conversation.',link:'/messages',action:'Open your conversations'},
  {id:'schedule',label:'Session scheduling',title:'Make learning part of your week.',text:'Choose a time together. Your session, partner, and private video room stay connected.',link:'/sessions',action:'Plan a learning session'},
  {id:'video',label:'Video learning',title:'Less setup. More “now I get it.”',text:'Join your private learning room from your schedule. Talk through a concept and put it into practice together.',link:'/sessions',action:'Visit your learning rooms'},
  {id:'reviews',label:'Progress & reviews',title:'Every exchange adds up.',text:'Complete a session, share useful feedback, and build a reputation through the knowledge you give.',link:'/dashboard',action:'See your progress'},
];

export default function ProductPreview({type='matching',member}) {
  const name=member?.full_name?.split(' ')[0]||'Your partner';
  const teaching=member?.skills?.find(s=>s.type==='Offering')?.title||'Python';
  return <div className={`product-preview preview-${type}`}>
    <div className="preview-toolbar"><span><i/><i/><i/></span><b>SkillSwap / {productFeatures.find(f=>f.id===type)?.label}</b><small>Preview</small></div>
    <div className="preview-body">
      {type==='matching'&&<><div className="preview-member"><Avatar person={member||{full_name:'Learning Partner',id:1}}/><div><strong>{member?.full_name||'A new perspective'}</strong><small>{member?.location||'Your learning community'}</small></div><ArrowRightLeft size={22}/></div><div className="preview-pair"><div><small>THEY TEACH</small><strong>{teaching}</strong><span>A skill you want to learn</span></div><div><small>YOU BRING</small><strong>Your know-how</strong><span>Something worth sharing</span></div></div><div className="preview-check"><Check size={16}/> Find the overlap in your goals</div><div className="preview-check"><Check size={16}/> Explore experience and availability</div></>}
      {type==='chat'&&<><div className="preview-member"><Avatar person={member||{full_name:'Learning Partner',id:1}}/><div><strong>{name}</strong><small>Your exchange conversation</small></div><Video size={18}/></div><div className="preview-bubble">What would you like to work on in our first session?</div><div className="preview-bubble own">Let’s build something small together. I learn best by doing!</div><div className="preview-delivered"><CheckCheck size={13}/> Read</div><div className="preview-composer">A new idea starts here… <span>↑</span></div></>}
      {type==='schedule'&&<><div className="preview-calendar-head"><CalendarDays size={19}/><strong>A little time to grow</strong><span>60 min</span></div><div className="preview-week">{['M','T','W','T','F','S','S'].map((day,i)=><span key={i} className={i===3?'chosen':''}><small>{day}</small><b>{12+i}</b></span>)}</div><div className="preview-booking"><span className="preview-calendar-icon"><Video size={23}/></span><div><strong>{teaching}, together</strong><small>With {name} · Your local time</small></div><Check size={17}/></div><div className="preview-check"><Check size={15}/> Private video room included</div></>}
      {type==='video'&&<><div className="preview-video-grid"><div className="preview-video-person"><Avatar person={member||{full_name:'Learning Partner',id:1}}/><span>{name}</span></div><div className="preview-video-person you"><Avatar person={{full_name:'You',id:2}}/><span>You</span></div></div><div className="preview-call-controls"><span><Mic size={16}/></span><span><Video size={16}/></span><span className="end"><PhoneOff size={16}/></span></div><p className="preview-room-note">Your own space to ask, try, and learn.</p></>}
      {type==='reviews'&&<><div className="preview-complete"><span><Check size={25}/></span><div><small>ONE MORE STEP FORWARD</small><strong>Exchange completed</strong></div></div><div className="preview-stars">{[1,2,3,4,5].map(n=><Star key={n} size={23}/>)}</div><p className="preview-reflection">What helped you learn? Share a thoughtful reflection with your partner.</p><div className="preview-progress-label"><span>Your learning journey</span><b>Keep growing ↗</b></div><div className="preview-progress"><span/></div></>}
    </div>
  </div>;
}
