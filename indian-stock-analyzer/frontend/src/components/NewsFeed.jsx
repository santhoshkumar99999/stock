export default function NewsFeed({ items }) {
  return (
    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      {items.map((n, i) => (
        <a
          href={n.link}
          target="_blank"
          rel="noreferrer"
          key={`${n.title}-${i}`}
          className="glass-card rounded-2xl p-5 group flex flex-col justify-between"
        >
          <div>
            <h4 className="font-semibold text-slate-100 line-clamp-3 group-hover:text-indigo-300 transition-colors duration-200 leading-snug">
              {n.title}
            </h4>
            <p className="text-xs text-slate-400 mt-3">{n.published}</p>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-700/50 flex items-center justify-between">
            <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${n.sentiment === 'Positive' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : n.sentiment === 'Negative' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' : 'bg-slate-500/10 text-slate-300 border-slate-500/20'}`}>
              {n.sentiment ?? "Neutral"}
            </span>
            <span className="text-indigo-400 text-xs font-semibold opacity-0 group-hover:opacity-100 transition-opacity duration-200">Read more &rarr;</span>
          </div>
        </a>
      ))}
    </div>
  );
}
