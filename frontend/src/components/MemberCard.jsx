import {Link} from 'react-router-dom';
import {ArrowUpRight,MapPin,Star} from 'lucide-react';

export function Avatar({person, className=''}) {
  const name=person?.full_name||'SkillSwap member';
  return <span className={`member-avatar ${className}`} data-tone={(person?.id||0)%4}>
    {name.split(' ').slice(0,2).map(n=>n[0]).join('')}
    {person?.avatar_url?.startsWith('https://')&&<img src={person.avatar_url} alt="" loading="lazy" onError={e=>{e.currentTarget.hidden=true;}}/>}
  </span>;
}

export default function MemberCard({member,match}) {
  const teaching=member.skills.filter(s=>s.type==='Offering'),learning=member.skills.filter(s=>s.type==='Requesting');
  return <article className="member-card" data-category={teaching[0]?.category}>
    <div className="member-top"><Avatar person={member}/><span className="member-rating"><Star size={13}/>{member.review_count?`${member.rating} (${member.review_count})`:'New member'}</span></div>
    <h3><Link to={`/members/${member.id}`}>{member.full_name}</Link></h3>
    <p className="member-location"><MapPin size={12}/>{member.location||'Learning from anywhere'}</p>
    <div className="member-skills"><small>CAN TEACH</small><div>{teaching.length?teaching.slice(0,3).map(s=><span key={s.id}>{s.title}</span>):<span>Building their teaching profile</span>}</div></div>
    <div className="member-skills wants"><small>WANTS TO LEARN</small><div>{learning.length?learning.slice(0,3).map(s=><span key={s.id}>{s.title}</span>):<span>Open to new ideas</span>}</div></div>
    <div className="member-bottom">{match!=null?<span>{match}% compatibility</span>:<span>Peer learning</span>}<Link to={`/members/${member.id}`}>View profile <ArrowUpRight size={15}/></Link></div>
  </article>;
}
