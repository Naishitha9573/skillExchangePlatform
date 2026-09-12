import { useEffect, useRef, useState } from 'react';

/**
 * Animates a number from 0 to `to` with spring-like easing.
 * Supports integer and single-decimal display.
 */
export default function AnimatedCounter({ to, duration = 1200, decimals = 0, suffix = '', prefix = '', className = '' }) {
  const [display, setDisplay] = useState(0);
  const ref = useRef(null);
  const started = useRef(false);

  useEffect(() => {
    const target = Number(to) || 0;
    if (target === 0) { setDisplay(0); return; }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started.current) {
          started.current = true;
          const start = performance.now();
          const step = (now) => {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            // Ease-out cubic for smooth deceleration
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = eased * target;
            setDisplay(current);
            if (progress < 1) requestAnimationFrame(step);
          };
          requestAnimationFrame(step);
        }
      },
      { threshold: 0.3 }
    );

    if (ref.current) observer.observe(ref.current);
    return () => { observer.disconnect(); started.current = false; };
  }, [to, duration]);

  const formatted = decimals > 0 ? display.toFixed(decimals) : Math.round(display);

  return (
    <span ref={ref} className={className}>
      {prefix}{formatted}{suffix}
    </span>
  );
}
