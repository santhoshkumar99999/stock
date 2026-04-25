export default function IndexCard({ title, data }) {
  const change = data?.change_percent ?? 0;
  const up = change >= 0;
  return (
    <div className="rounded-xl bg-slate-900 p-5 border border-slate-800 shadow-lg">
      <p className="text-slate-300">{title}</p>
      <h3 className="text-3xl font-bold mt-2">{data?.price?.toFixed?.(2) ?? "-"}</h3>
      <p className={`mt-2 text-sm ${up ? "text-emerald-400" : "text-red-400"}`}>
        {up ? "▲" : "▼"} {change.toFixed(2)}%
      </p>
    </div>
  );
}
