import { useState, useEffect } from 'react';

export function useCountUp(targetValue, duration = 1200, decimals = 0) {
  const [value, setValue] = useState(0);

  useEffect(() => {
    let startTimestamp = null;
    const startValue = 0;
    const numericTarget = Number(targetValue) || 0;

    const step = (timestamp) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);
      // Ease out cubic
      const easeProgress = 1 - Math.pow(1 - progress, 3);
      const current = startValue + easeProgress * (numericTarget - startValue);
      setValue(Number(current.toFixed(decimals)));

      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        setValue(numericTarget);
      }
    };

    window.requestAnimationFrame(step);
  }, [targetValue, duration, decimals]);

  return value;
}
