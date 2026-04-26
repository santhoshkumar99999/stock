import { FiTrendingUp, FiTrendingDown } from "react-icons/fi";

export default function IndexCard({ title, data }) {
  const change = data?.change_percent ?? 0;
  const up = change >= 0;
  return (
    <div className="glass-card rounded-2xl p-6 group hover:-translate-y-1 transition-transform duration-300">
      <p className="text-slate-400 font-medium tracking-wide uppercase text-sm mb-1">{title}</p>
      <div className="flex items-end justify-between">
        <h3 className="text-4xl font-extrabold text-white tracking-tight">
          {data?.price?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? "-"}
        </h3>
        <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold backdrop-blur-sm ${up ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"}`}>
          {up ? <FiTrendingUp /> : <FiTrendingDown />}
          <span>{Math.abs(change).toFixed(2)}%</span>
        </div>
      </div>
    </div>
  );
}
