import { useEffect, useRef } from "react";
import { createChart } from "lightweight-charts";

export default function CandlestickChart({ candles }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = createChart(ref.current, {
      layout: { background: { type: 'solid', color: 'transparent' }, textColor: "#94a3b8" },
      width: ref.current.clientWidth,
      height: 400,
      grid: { vertLines: { color: "rgba(30, 41, 59, 0.5)" }, horzLines: { color: "rgba(30, 41, 59, 0.5)" } },
    });
    const series = chart.addCandlestickSeries({
      upColor: '#34d399',
      downColor: '#fb7185',
      borderVisible: false,
      wickUpColor: '#34d399',
      wickDownColor: '#fb7185',
    });
    series.setData(
      (candles || []).map((c) => ({
        time: c.time.slice(0, 10),
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }))
    );
    return () => chart.remove();
  }, [candles]);

  return <div className="w-full h-full min-h-[400px]" ref={ref} />;
}
