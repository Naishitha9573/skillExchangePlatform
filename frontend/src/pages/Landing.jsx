import {useEffect,useRef} from 'react';
import {Link} from 'react-router-dom';
import {ArrowRight,ArrowUpRight,BrainCircuit,Check,Compass,Handshake,Layers3,ShieldCheck,Sparkles,Video} from 'lucide-react';
import AnimatedCounter from '../components/AnimatedCounter';

function useReveal() {
  const ref = useRef(null);
  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => entries.forEach(entry => {
        if (entry.isIntersecting) entry.target.classList.add('visible');
      }),
      { threshold: 0.15 }
    );
    ref.current?.querySelectorAll('.reveal').forEach(el => observer.observe(el));
    return () => observer.disconnect();
  }, []);
  return ref;
}

export default function Landing() {
  const root = useReveal();

  return (
    <main className="landing premium-landing" ref={root}>
      <section className="premium-hero">
        <div className="hero-copy">
          <div className="eyebrow"><Sparkles size={15}/> The peer learning network</div>
          <h1>Learn openly.<br/><em>Teach generously.</em></h1>
          <p>SkillSwap turns the skills you have into the skills you need. Find a person, trade knowledge, and grow together without a price tag.</p>
          <div className="heroactions">
            <Link className="button" to="/register">Get started <ArrowRight size={18}/></Link>
            <Link className="button secondary" to="/feed">Explore skills <Compass size={17}/></Link>
          </div>
          <div className="hero-proof">
            <span className="proof-avatars"><i>AM</i><i>JR</i><i>SK</i></span>
            <span>
              <strong>Built for curious people</strong>
              <small>No money. Just momentum.</small>
            </span>
          </div>
        </div>

        <div className="hero-visual">
          {/* Animated gradient orbs */}
          <div className="hero-orb hero-orb-1" aria-hidden="true" />
          <div className="hero-orb hero-orb-2" aria-hidden="true" />

          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />

          <div className="match-card">
            <div className="match-label"><span className="live-dot" /> A great exchange is forming</div>
            <div className="person-row">
              <div className="portrait portrait-a">AM</div>
              <div><strong>Alex teaches</strong><span>Product strategy</span></div>
              <span className="match-line"><Check size={14}/></span>
              <div className="portrait portrait-b">JR</div>
              <div><strong>Jordan learns</strong><span>React fundamentals</span></div>
            </div>
            <div className="match-footer">
              <span><ShieldCheck size={14}/> A shared learning goal</span>
              <b>Example exchange</b>
            </div>
          </div>

          <div className="floating-note note-top">
            <Layers3 size={16}/>
            <span><strong>Live conversations</strong><small>learning stays here</small></span>
          </div>
          <div className="floating-note note-bottom">
            <Video size={16}/>
            <span><strong>Next session</strong><small>Design critique · Today</small></span>
          </div>
        </div>
      </section>

      <section className="value-strip" id="how-it-works">
        <div className="reveal">
          <span className="value-number">01</span>
          <strong>Bring what you know</strong>
          <small>Teach a skill you are proud of.</small>
        </div>
        <div className="reveal delay-1">
          <span className="value-number">02</span>
          <strong>Find your next unlock</strong>
          <small>Discover people who fill the gap.</small>
        </div>
        <div className="reveal delay-2">
          <span className="value-number">03</span>
          <strong>Make progress together</strong>
          <small>Swap time, not money.</small>
        </div>
      </section>

      {/* Community stats with animated counters */}
      <section className="story-section" id="why-skillswap">
        <div className="community-stats reveal">
          <div className="community-stat">
            <strong><AnimatedCounter to={500} suffix="+" /></strong>
            <span>Skills exchanged</span>
          </div>
          <div className="community-stat">
            <strong><AnimatedCounter to={120} suffix="+" /></strong>
            <span>Active learners</span>
          </div>
          <div className="community-stat">
            <strong><AnimatedCounter to={850} suffix="h" /></strong>
            <span>Time spent learning</span>
          </div>
        </div>

        <div className="section-kicker reveal" style={{marginTop: 65}}>A better kind of marketplace</div>
        <div className="story-heading reveal">
          <h2>Knowledge moves further<br/><em>when it moves both ways.</em></h2>
          <p>From first hello to finished session, every part of SkillSwap is designed to make peer learning feel human, focused, and worth returning to.</p>
        </div>

        <div className="feature-grid">
          <Feature I={BrainCircuit} t="Find your people" d="Smart matching surfaces complementary skills, goals, and learning styles." />
          <Feature I={Handshake} t="Exchange with intention" d="Say hello, book a time, and learn face to face in your own private video room." />
          <Feature I={ShieldCheck} t="Build trusted reputation" d="Complete learning sessions, share thoughtful reviews, and see your progress grow." />
        </div>

        <div className="landing-loop reveal">
          <div className="section-kicker">From first hello to your next breakthrough</div>
          <h3>Your whole exchange. One place.</h3>
          <p>No scattered messages or meeting links. Stay connected from the first match to the moment it clicks.</p>
          <div className="workflow-steps">
            {['Discover','Match','Swap','Message','Schedule','Video & learn','Complete','Review'].map((step,i) => (
              <span key={step}><b>0{i+1}</b>{step}</span>
            ))}
          </div>
        </div>

        <div className="landing-cta reveal">
          <div>
            <div className="eyebrow"><Sparkles size={15}/> Your next skill is out there</div>
            <h2>Enter SkillSwap and start<br/>your first exchange.</h2>
          </div>
          <Link className="button light-button" to="/register">Create your profile <ArrowUpRight size={18}/></Link>
        </div>
      </section>
    </main>
  );
}

function Feature({I,t,d}) {
  return (
    <article className="premium-feature reveal">
      <div className="feature-icon"><I size={19}/></div>
      <div>
        <h3>{t}</h3>
        <p>{d}</p>
      </div>
      <ArrowUpRight className="feature-arrow" size={17}/>
    </article>
  );
}
