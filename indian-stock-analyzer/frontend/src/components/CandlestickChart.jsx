import { useEffect, useRef } from "react";
import { createChart } from "lightweight-charts";

export default function CandlestickChart({ candles }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = createChart(ref.current, {
      layout: { background: { color: "#0f172a" }, textColor: "#94a3b8" },
      width: ref.current.clientWidth,
      height: 360,
      grid: { vertLines: { color: "#1e293b" }, horzLines: { color: "#1e293b" } },
    });
    const series = chart.addCandlestickSeries();
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

  return <div className="w-full rounded-xl border border-slate-800" ref={ref} />;
}
