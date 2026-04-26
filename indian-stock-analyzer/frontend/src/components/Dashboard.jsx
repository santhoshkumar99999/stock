import { useEffect, useMemo, useState, useCallback } from "react";
import axios from "axios";
import { Toaster } from "react-hot-toast";
import CandlestickChart from "./CandlestickChart";
import FilterBar from "./FilterBar";
import IndexCard from "./IndexCard";
import NewsFeed from "./NewsFeed";
import SignalAlert from "./SignalAlert";
import StockTable from "./StockTable";
import { FiActivity, FiTerminal, FiChevronDown, FiWifi, FiWifiOff } from "react-icons/fi";

const api = axios.create({ baseURL: "" });
const BANK = new Set([
  "HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN", "INDUSINDBK", "BANKBARODA",
  "PNB", "FEDERALBNK", "IDFCFIRSTB", "BANDHANBNK", "AUBANK",
]);

export default function Dashboard() {
  const [indices, setIndices] = useState({});
  const [stocks, setStocks] = useState([]);
  const [symbol, setSymbol] = useState("RELIANCE");
  const [ohlcv, setOhlcv] = useState([]);
  const [news, setNews] = useState([]);
  const [search, setSearch] = useState("");
  const [signalFilter, setSignalFilter] = useState("ALL");
  const [onlyBank, setOnlyBank] = useState(false);
  const [command, setCommand] = useState("TOP5");
  const [commandOutput, setCommandOutput] = useState("");
  const [backendOk, setBackendOk] = useState(null); // null = checking, true = ok, false = down

  // Health-check poll
  useEffect(() => {
    const check = () =>
      api.get("/api/health")
        .then(() => setBackendOk(true))
        .catch(() => setBackendOk(false));
    check();
    const t = setInterval(check, 30_000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const load = async () => {
      try {
        const [idx, st, nw] = await Promise.all([
          api.get("/api/indices"),
          api.get("/api/stocks"),
          api.get("/api/news"),
        ]);
        setIndices(idx.data.indices || {});
        setStocks(st.data || []);
        setNews([...(nw.data.NIFTY50?.articles || []), ...(nw.data.BANKNIFTY?.articles || [])]);
      } catch (err) {
        console.error("Failed to load market data:", err);
      }
    };
    load();
    const timer = setInterval(load, 5 * 60 * 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    api.get(`/api/stock/${symbol}`).then((r) => setOhlcv(r.data.ohlcv || []));
  }, [symbol]);

  const filtered = useMemo(() => {
    return stocks.filter((s) => {
      if (search && !s.symbol.toLowerCase().includes(search.toLowerCase())) return false;
      if (signalFilter !== "ALL" && !s.signal.includes(signalFilter)) return false;
      if (onlyBank && !BANK.has(s.symbol)) return false;
      return true;
    });
  }, [stocks, search, signalFilter, onlyBank]);

  const runCommand = async () => {
    try {
      const res = await api.post("/api/command", { command });
      setCommandOutput(res.data.response || "");
    } catch (err) {
      setCommandOutput("Could not run command. Check backend connection.");
    }
  };

  return (
    <div className="min-h-screen text-slate-100 px-4 md:px-8 py-8 relative">
      <div className="absolute top-0 left-0 w-full h-96 bg-indigo-500/10 blur-[100px] pointer-events-none"></div>
      <div className="absolute bottom-0 right-0 w-full h-96 bg-purple-500/10 blur-[100px] pointer-events-none"></div>
      
      <div className="max-w-7xl mx-auto relative z-10">
        <Toaster position="bottom-right" toastOptions={{ style: { background: '#1e293b', color: '#f8fafc', border: '1px solid #334155' } }} />
        <SignalAlert rows={stocks} />
        
        <header className="flex flex-col md:flex-row md:items-center justify-between mb-10 gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-indigo-500/20 rounded-2xl border border-indigo-500/30">
              <FiActivity className="text-2xl text-indigo-400" />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-white">NSE Analyzer</h1>
              <p className="text-sm text-slate-400 font-medium mt-1">Real-time Nifty50 &amp; BankNifty insights</p>
            </div>
          </div>
          {/* Backend connection status */}
          <div className={`flex items-center gap-2 px-4 py-2 rounded-full border text-sm font-semibold backdrop-blur-sm transition-all ${
            backendOk === null
              ? "bg-slate-500/10 border-slate-500/30 text-slate-400"
              : backendOk
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
              : "bg-rose-500/10 border-rose-500/30 text-rose-400"
          }`}>
            {backendOk === null ? (
              <span className="w-2 h-2 rounded-full bg-slate-400 animate-pulse" />
            ) : backendOk ? (
              <FiWifi />
            ) : (
              <FiWifiOff />
            )}
            <span>
              {backendOk === null ? "Connecting…" : backendOk ? "Backend Connected" : "Backend Offline"}
            </span>
          </div>
        </header>

        <section className="grid md:grid-cols-2 gap-6 mb-8">
          <IndexCard title="NIFTY 50" data={indices.NIFTY50} />
          <IndexCard title="BANKNIFTY" data={indices.BANKNIFTY} />
        </section>

        <section className="mb-10 glass-card rounded-2xl p-6 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-[50px] pointer-events-none"></div>
          <div className="flex items-center gap-2 mb-4">
            <FiTerminal className="text-emerald-400 text-lg" />
            <h2 className="text-lg font-bold text-white tracking-wide">Terminal Interface</h2>
          </div>
          <div className="flex flex-col md:flex-row gap-3">
            <input
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder="Try: SIGNAL RELIANCE or TOP5"
              className="flex-1 bg-slate-900/60 border border-slate-700/50 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-shadow text-slate-100 font-mono text-sm"
              onKeyDown={(e) => e.key === 'Enter' && runCommand()}
            />
            <button
              type="button"
              onClick={runCommand}
              className="bg-emerald-500 hover:bg-emerald-400 text-slate-900 rounded-xl px-8 py-3 font-bold transition-colors shadow-lg shadow-emerald-500/20"
            >
              Execute
            </button>
          </div>
          {commandOutput ? (
            <pre className="mt-4 whitespace-pre-wrap text-sm bg-slate-950/80 border border-slate-800/80 rounded-xl p-5 text-emerald-400 font-mono leading-relaxed overflow-auto max-h-60">
              {commandOutput}
            </pre>
          ) : null}
        </section>

        <FilterBar
          search={search}
          setSearch={setSearch}
          signalFilter={signalFilter}
          setSignalFilter={setSignalFilter}
          onlyBank={onlyBank}
          setOnlyBank={setOnlyBank}
        />

        <section className="grid lg:grid-cols-5 gap-6 mb-12">
          <div className="lg:col-span-3 flex flex-col">
            <div className="glass-card rounded-2xl p-6 flex-1 flex flex-col relative overflow-hidden">
              <div className="absolute -top-10 -right-10 w-40 h-40 bg-indigo-500/10 rounded-full blur-[50px] pointer-events-none"></div>
              <div className="flex items-center justify-between mb-6 relative z-10">
                <h2 className="text-xl font-bold text-white tracking-wide">Technical Analysis</h2>
                <div className="relative">
                  <select
                    className="bg-slate-900/80 border border-slate-700/50 rounded-xl pl-4 pr-10 py-2.5 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm font-semibold text-indigo-100 cursor-pointer"
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                  >
                    {stocks.map((s) => (
                      <option key={s.symbol} value={s.symbol}>
                        {s.symbol}
                      </option>
                    ))}
                  </select>
                  <FiChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                </div>
              </div>
              <div className="flex-1 min-h-[400px] relative z-10">
                <CandlestickChart candles={ohlcv} />
              </div>
            </div>
          </div>
          <div className="lg:col-span-2">
            <h2 className="text-xl font-bold text-white tracking-wide mb-4 pl-1">Market Signals</h2>
            <StockTable rows={filtered} onPick={setSymbol} />
          </div>
        </section>

        <section className="mt-12">
          <div className="flex items-center justify-between mb-6 pl-1">
            <h2 className="text-2xl font-bold text-white tracking-wide">Latest Market News</h2>
            <span className="text-sm font-medium text-slate-400 bg-slate-800/50 px-3 py-1 rounded-full border border-slate-700/50">Top Stories</span>
          </div>
          <NewsFeed items={news.slice(0, 18)} />
        </section>
      </div>
    </div>
  );
}
