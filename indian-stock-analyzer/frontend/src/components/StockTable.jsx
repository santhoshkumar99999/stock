const signalColor = (signal) => {
  if (signal.includes("STRONG BUY")) return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
  if (signal.includes("BUY")) return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
  if (signal.includes("STRONG SELL")) return "bg-rose-500/20 text-rose-400 border-rose-500/30";
  if (signal.includes("SELL")) return "bg-rose-500/10 text-rose-400 border-rose-500/20";
  return "bg-slate-500/10 text-slate-300 border-slate-500/20";
};

export default function StockTable({ rows, onPick }) {
  return (
    <div className="glass-card rounded-2xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-slate-400 uppercase bg-slate-900/50 border-b border-slate-700/50">
            <tr>
              <th className="px-6 py-4 font-semibold tracking-wider">Stock</th>
              <th className="px-6 py-4 font-semibold tracking-wider text-right">Price</th>
              <th className="px-6 py-4 font-semibold tracking-wider text-center">Signal</th>
              <th className="px-6 py-4 font-semibold tracking-wider text-right">Confidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {rows.map((r) => (
              <tr
                key={r.symbol}
                className="hover:bg-indigo-500/10 cursor-pointer transition-colors duration-200 group"
                onClick={() => onPick(r.symbol)}
              >
                <td className="px-6 py-4 whitespace-nowrap font-medium text-slate-200 group-hover:text-indigo-300 transition-colors">
                  {r.symbol}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right font-medium">
                  {r.price?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? "-"}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <span className={`px-2.5 py-1 text-xs font-bold rounded-full border ${signalColor(r.signal)}`}>
                    {r.signal}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right">
                  <div className="flex items-center justify-end gap-2">
                    <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${r.signal.includes('BUY') ? 'bg-emerald-400' : r.signal.includes('SELL') ? 'bg-rose-400' : 'bg-slate-400'}`} 
                        style={{ width: `${r.confidence}%` }}
                      />
                    </div>
                    <span className="text-xs font-semibold text-slate-300 w-8">{r.confidence}%</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
