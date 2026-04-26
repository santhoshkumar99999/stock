import { FiSearch, FiFilter } from "react-icons/fi";

export default function FilterBar({
  search,
  setSearch,
  signalFilter,
  setSignalFilter,
  onlyBank,
  setOnlyBank,
}) {
  return (
    <div className="glass-card rounded-2xl p-4 mb-8 flex flex-col md:flex-row items-center gap-4 justify-between">
      <div className="relative w-full md:w-1/3">
        <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search stock by symbol..."
          className="w-full bg-slate-900/50 border border-slate-700/50 rounded-xl pl-11 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-shadow text-sm text-slate-100 placeholder:text-slate-500"
        />
      </div>
      
      <div className="flex items-center gap-4 w-full md:w-auto">
        <div className="relative w-full md:w-48">
          <FiFilter className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
          <select
            value={signalFilter}
            onChange={(e) => setSignalFilter(e.target.value)}
            className="w-full bg-slate-900/50 border border-slate-700/50 rounded-xl pl-11 pr-4 py-3 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-shadow text-sm text-slate-100 cursor-pointer"
          >
            <option value="ALL">All Signals</option>
            <option value="BUY">BUY Only</option>
            <option value="SELL">SELL Only</option>
            <option value="HOLD">HOLD Only</option>
          </select>
        </div>

        <label className="flex items-center gap-3 cursor-pointer group whitespace-nowrap bg-slate-900/50 border border-slate-700/50 rounded-xl px-4 py-3 transition-colors hover:bg-slate-800/50">
          <div className="relative flex items-center">
            <input 
              type="checkbox" 
              checked={onlyBank} 
              onChange={(e) => setOnlyBank(e.target.checked)} 
              className="sr-only peer"
            />
            <div className="w-10 h-5 bg-slate-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-indigo-500/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-500"></div>
          </div>
          <span className="text-sm font-medium text-slate-300 group-hover:text-white transition-colors">BankNifty Only</span>
        </label>
      </div>
    </div>
  );
}
