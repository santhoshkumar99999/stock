import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { Toaster } from "react-hot-toast";
import CandlestickChart from "./CandlestickChart";
import FilterBar from "./FilterBar";
import IndexCard from "./IndexCard";
import NewsFeed from "./NewsFeed";
import SignalAlert from "./SignalAlert";
import StockTable from "./StockTable";

const api = axios.create({ baseURL: "http://localhost:8000" });
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

  useEffect(() => {
    const load = async () => {
      const [idx, st, nw] = await Promise.all([
        api.get("/api/indices"),
        api.get("/api/stocks"),
        api.get("/api/news"),
      ]);
      setIndices(idx.data.indices || {});
      setStocks(st.data || []);
      setNews([...(nw.data.NIFTY50?.articles || []), ...(nw.data.BANKNIFTY?.articles || [])]);
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
    <div className="min-h-screen bg-slate-950 text-slate-100 px-4 md:px-8 py-6">
      <Toaster position="bottom-right" />
      <SignalAlert rows={stocks} />
      <header className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">NSE Analyzer</h1>
      </header>
      <section className="mb-6 rounded-lg border border-slate-800 p-4 bg-slate-900/40">
        <h2 className="text-lg font-semibold mb-3">Bot Command Interface</h2>
        <div className="flex gap-2">
          <input
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            placeholder="Try: SIGNAL RELIANCE"
            className="flex-1 bg-slate-800 border border-slate-700 rounded px-3 py-2"
          />
          <button
            type="button"
            onClick={runCommand}
            className="bg-emerald-600 hover:bg-emerald-500 rounded px-4 py-2 font-medium"
          >
            Run
          </button>
        </div>
        {commandOutput ? (
          <pre className="mt-3 whitespace-pre-wrap text-sm bg-slate-950 border border-slate-800 rounded p-3">
            {commandOutput}
          </pre>
        ) : null}
      </section>
      <section className="grid md:grid-cols-2 gap-4 mb-6">
        <IndexCard title="Nifty 50" data={indices.NIFTY50} />
        <IndexCard title="BankNifty" data={indices.BANKNIFTY} />
      </section>

      <FilterBar
        search={search}
        setSearch={setSearch}
        signalFilter={signalFilter}
        setSignalFilter={setSignalFilter}
        onlyBank={onlyBank}
        setOnlyBank={setOnlyBank}
      />

      <section className="grid lg:grid-cols-5 gap-4">
        <div className="lg:col-span-3">
          <div className="mb-3">
            <select
              className="bg-slate-800 border border-slate-700 rounded px-3 py-2"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
            >
              {stocks.map((s) => (
                <option key={s.symbol} value={s.symbol}>
                  {s.symbol}
                </option>
              ))}
            </select>
          </div>
          <CandlestickChart candles={ohlcv} />
        </div>
        <div className="lg:col-span-2">
          <StockTable rows={filtered} onPick={setSymbol} />
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold mb-4">News Feed</h2>
        <NewsFeed items={news.slice(0, 18)} />
      </section>
    </div>
  );
}
