export default function FilterBar({
  search,
  setSearch,
  signalFilter,
  setSignalFilter,
  onlyBank,
  setOnlyBank,
}) {
  return (
    <div className="flex flex-wrap items-center gap-3 mb-4">
      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search stock..."
        className="bg-slate-800 border border-slate-700 rounded px-3 py-2"
      />
      <select
        value={signalFilter}
        onChange={(e) => setSignalFilter(e.target.value)}
        className="bg-slate-800 border border-slate-700 rounded px-3 py-2"
      >
        <option value="ALL">All</option>
        <option value="BUY">BUY</option>
        <option value="SELL">SELL</option>
        <option value="HOLD">HOLD</option>
      </select>
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={onlyBank} onChange={(e) => setOnlyBank(e.target.checked)} />
        BankNifty only
      </label>
    </div>
  );
}
