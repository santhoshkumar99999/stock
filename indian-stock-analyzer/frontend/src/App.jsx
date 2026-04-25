import { useEffect } from "react";
import { toast } from "react-hot-toast";
import Dashboard from "./components/Dashboard";
import { onForegroundMessage, requestNotificationPermission } from "./firebase";

export default function App() {
  useEffect(() => {
    requestNotificationPermission();

    let unsubscribe = () => {};
    onForegroundMessage((payload) => {
      const title = payload?.notification?.title || "Stock Alert";
      const body = payload?.notification?.body || "";
      const isBuy = payload?.data?.type === "BUY";
      const isSell = payload?.data?.type === "SELL";
      const background = isBuy ? "#dcfce7" : isSell ? "#fee2e2" : "#f0f9ff";
      const border = isBuy ? "#86efac" : isSell ? "#fca5a5" : "#bae6fd";

      toast.custom(
        () => (
          <div
            style={{
              background,
              border: `1px solid ${border}`,
              borderRadius: 8,
              padding: "12px 16px",
              maxWidth: 320,
              color: "#0f172a",
            }}
          >
            <div style={{ fontWeight: 600 }}>{title}</div>
            <div style={{ fontSize: 13, marginTop: 4 }}>{body}</div>
          </div>
        ),
        { duration: 8000 },
      );
    }).then((fn) => {
      unsubscribe = fn;
    });

    return () => unsubscribe();
  }, []);

  return <Dashboard />;
}
