export default function NewsFeed({ items }) {
  return (
    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
      {items.map((n, i) => (
        <a
          href={n.link}
          target="_blank"
          rel="noreferrer"
          key={`${n.title}-${i}`}
          className="rounded-xl bg-slate-900 border border-slate-800 p-4 hover:border-slate-700"
        >
          <h4 className="font-semibold text-slate-100 line-clamp-2">{n.title}</h4>
          <p className="text-xs text-slate-400 mt-2">{n.published}</p>
          <p className="text-xs mt-2 text-emerald-400">{n.sentiment ?? "Neutral"}</p>
        </a>
      ))}
    </div>
  );
}
