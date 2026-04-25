const signalColor = (signal) => {
  if (signal.includes("BUY")) return "text-emerald-400";
  if (signal.includes("SELL")) return "text-red-400";
  return "text-slate-300";
};

export default function StockTable({ rows, onPick }) {
  return (
    <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-auto">
      <table className="w-full text-sm">
        <thead className="text-slate-400 border-b border-slate-800">
          <tr>
            <th className="text-left p-3">Stock</th>
            <th className="text-left p-3">Price</th>
            <th className="text-left p-3">Signal</th>
            <th className="text-left p-3">Confidence</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr
              key={r.symbol}
              className="border-b border-slate-800 hover:bg-slate-800/50 cursor-pointer"
              onClick={() => onPick(r.symbol)}
            >
              <td className="p-3">{r.symbol}</td>
              <td className="p-3">{r.price?.toFixed?.(2) ?? "-"}</td>
              <td className={`p-3 font-semibold ${signalColor(r.signal)}`}>{r.signal}</td>
              <td className="p-3">{r.confidence}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
