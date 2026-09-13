import {ArrowRightLeft,Check,Code2,Camera,MessageCircle,Palette} from 'lucide-react';
import {Avatar} from './MemberCard';

export default function ExchangeVisual({compact=false}) {
  return <div className={`exchange-visual ${compact?'compact':''}`} aria-label="Illustrative exchange: you teach React and learn Python from a partner">
    <div className="network-disc" aria-hidden="true"/>
    <svg className="network-paths" viewBox="0 0 540 450" fill="none" aria-hidden="true"><path d="M110 100C270 100 180 215 270 215S430 185 430 90M270 215C200 310 400 280 410 360M270 215C180 235 210 350 95 355"/><circle cx="270" cy="215" r="165"/></svg>
    <div className="network-caption"><span className="live-dot"/> TWO PEOPLE. TWO POSSIBILITIES.</div>
    <div className="network-person network-you"><div className="network-person-head"><Avatar person={{full_name:'You',id:2}}/><div><strong>You bring the spark.</strong><small>Your exchange profile</small></div></div><div className="network-skill"><span>I can teach</span><strong><Code2 size={17}/> React</strong></div><div className="network-skill warm"><span>I want to learn</span><strong>Python <ArrowRightLeft size={16}/></strong></div></div>
    <div className="network-connector"><ArrowRightLeft size={23}/></div>
    <div className="network-person network-partner"><div className="network-person-head"><Avatar person={{full_name:'Learning Partner',id:1}}/><div><strong>They bring a new skill.</strong><small>Your next learning partner</small></div></div><div className="partner-skill"><span>Teaches <b>Python</b></span><span>Learns <b>React</b></span></div><div className="network-fit"><Check size={14}/> A two-way learning opportunity</div></div>
    <span className="network-chip chip-design"><Palette size={17}/> UI/UX Design</span>
    <span className="network-chip chip-photo"><Camera size={16}/> Photography</span>
    <span className="network-chip chip-talk"><MessageCircle size={16}/> Public speaking</span>
    <span className="visual-label">Illustrative exchange</span>
  </div>;
}
