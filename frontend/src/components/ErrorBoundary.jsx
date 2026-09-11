import React from 'react';
export default class ErrorBoundary extends React.Component {
  constructor(props){ super(props); this.state={error:null}; }
  static getDerivedStateFromError(error){ return {error}; }
  componentDidCatch(error, info){ console.error('SkillSwap UI error:', error, info); }
  render(){
    if(this.state.error) return <main className="container"><div className="card crash"><div className="eyebrow">Recovery mode</div><h1>This screen hit a UI error.</h1><p>The rest of SkillSwap is still available. Refresh this page after confirming the backend is running.</p><details><summary>Technical details</summary><pre>{String(this.state.error?.message || this.state.error)}</pre></details><button className="button" onClick={()=>window.location.reload()}>Reload screen</button></div></main>;
    return this.props.children;
  }
}
