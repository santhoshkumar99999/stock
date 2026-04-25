import { useEffect, useRef } from "react";
import toast from "react-hot-toast";

export default function SignalAlert({ rows }) {
  const seen = useRef(new Set());
  useEffect(() => {
    rows.forEach((r) => {
      const key = `${r.symbol}:${r.signal}`;
      if ((r.signal === "STRONG BUY" || r.signal === "STRONG SELL") && !seen.current.has(key)) {
        seen.current.add(key);
        toast(`${r.symbol} ${r.signal} (${r.confidence}%)`);
      }
    });
  }, [rows]);
  return null;
}
