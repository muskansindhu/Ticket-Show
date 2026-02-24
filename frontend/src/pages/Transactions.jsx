import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiRequest, formatCurrency } from "../apiClient.js";
import Icon from "../components/Icon.jsx";

function formatDateTime(value) {
    if (!value) return "--";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "--";
    return date.toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

export default function Transactions() {
    const navigate = useNavigate();
    const [wallet, setWallet] = useState(null);
    const [walletLoading, setWalletLoading] = useState(false);
    const [walletError, setWalletError] = useState("");

    useEffect(() => {
        async function loadWallet() {
            setWalletLoading(true);
            setWalletError("");
            try {
                const data = await apiRequest("/auth/wallet");
                setWallet(data);
            } catch (err) {
                setWalletError(err.message);
            } finally {
                setWalletLoading(false);
            }
        }
        loadWallet();
    }, []);

    return (
        <section className="page">
            <div className="page-header reveal" style={{ "--delay": "0.03s" }}>
                <div>
                    <button
                        className="ghost"
                        onClick={() => navigate("/profile")}
                        style={{ marginBottom: "1rem" }}
                    >
                        <Icon name="arrowLeft" size={14} /> Back to Profile
                    </button>
                    <h2>Wallet Transactions</h2>
                    <p className="muted">View your payment and refund history.</p>
                </div>
            </div>

            {walletLoading ? <p className="muted">Loading transactions...</p> : null}
            {walletError ? <p className="notice">{walletError}</p> : null}

            {!walletLoading && Array.isArray(wallet?.transactions) && wallet.transactions.length === 0 ? (
                <p className="muted">No wallet transactions yet.</p>
            ) : null}

            {Array.isArray(wallet?.transactions) && wallet.transactions.length > 0 ? (
                <div className="list-stack booking-list reveal" style={{ "--delay": "0.08s" }}>
                    {wallet.transactions.map((tx) => (
                        <article className="booking-card booking-record" key={tx.id} style={{ padding: "1.25rem" }}>
                            <div className="booking-header" style={{ margin: 0 }}>
                                <div className="booking-title">
                                    <Icon name="wallet" size={14} />
                                    <h4>{tx.transaction_type}</h4>
                                </div>
                                <span className={`status-pill ${String(tx.transaction_type || "").toLowerCase()}`}>
                                    {tx.transaction_type}
                                </span>
                            </div>
                            <div className="booking-meta booking-summary-meta" style={{ marginTop: "0.5rem" }}>
                                <span className="icon-inline"><Icon name="credit" size={14} /> {formatCurrency(tx.amount)}</span>
                                <span className="icon-inline"><Icon name="calendar" size={14} /> {formatDateTime(tx.created_at)}</span>
                            </div>
                            <p className="muted" style={{ marginTop: "0.5rem" }}>{tx.description || "--"}</p>
                            <p className="muted mono" style={{ marginTop: "0.25rem", marginBottom: 0 }}>Ref: {tx.reference_id || "--"}</p>
                        </article>
                    ))}
                </div>
            ) : null}
        </section>
    );
}
