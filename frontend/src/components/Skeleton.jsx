import './Skeleton.css';

export function Skeleton({ width, height, radius = 8, className = '', variant = 'text' }) {
  const style = {};
  if (width) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;
  if (radius) style.borderRadius = typeof radius === 'number' ? `${radius}px` : radius;
  return <span className={`skeleton skeleton-${variant} ${className}`} style={style} aria-hidden="true" />;
}

export function SkeletonCard({ lines = 3 }) {
  return (
    <div className="skeleton-card card" aria-hidden="true">
      <div className="skeleton-card-top">
        <Skeleton width={70} height={22} radius={99} />
        <Skeleton width={55} height={22} radius={99} />
      </div>
      <Skeleton height={24} width="75%" style={{ marginTop: 18 }} />
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton key={i} height={14} width={i === lines - 1 ? '60%' : '100%'} />
      ))}
      <div className="skeleton-card-bottom">
        <Skeleton variant="avatar" width={32} height={32} radius="50%" />
        <Skeleton width={100} height={12} />
      </div>
    </div>
  );
}

export function SkeletonStat() {
  return (
    <div className="stat card skeleton-stat" aria-hidden="true">
      <Skeleton variant="avatar" width={38} height={38} radius={10} />
      <div>
        <Skeleton width={70} height={10} />
        <Skeleton width={45} height={22} />
      </div>
    </div>
  );
}

export function SkeletonThread() {
  return (
    <div className="skeleton-thread" aria-hidden="true">
      <Skeleton variant="avatar" width={39} height={39} radius={13} />
      <div style={{ flex: 1 }}>
        <Skeleton width="65%" height={13} />
        <Skeleton width="40%" height={11} />
      </div>
    </div>
  );
}

export function SkeletonSession() {
  return (
    <div className="card skeleton-session" aria-hidden="true">
      <div style={{ display: 'flex', gap: 20, alignItems: 'center', padding: 22 }}>
        <Skeleton width={62} height={80} radius={11} />
        <div style={{ flex: 1 }}>
          <Skeleton width={60} height={18} radius={99} />
          <Skeleton width="70%" height={18} />
          <Skeleton width="45%" height={12} />
          <Skeleton width="35%" height={10} />
        </div>
      </div>
    </div>
  );
}
