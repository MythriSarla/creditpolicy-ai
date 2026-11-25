import { useEffect, useState } from "react";
import { generateBriefing, listBriefings, getBriefing, getSources } from "./api";

const fmt = (iso) =>
  new Date(iso).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

const DIR = { up: "Tightening", down: "Easing", new: "New", unchanged: "No change" };

function Changes({ rows }) {
  return (
    <section className="changes">
      <h2>What changed since the last briefing</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Topic</th><th>Previous</th><th>Now</th><th>Signal</th><th>Impact for lending</th></tr>
          </thead>
          <tbody>
            {rows.map((c, i) => (
              <tr key={i} className={`row-${c.direction}`}>
                <td className="topic">{c.topic}</td>
                <td>{c.previous}</td>
                <td><strong>{c.current}</strong></td>
                <td><span className={`tag tag-${c.direction}`}>{DIR[c.direction] || c.direction}</span></td>
                <td>{c.impact}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Brief({ b }) {
  return (
    <article>
      <p className="stamp">Briefing #{b.id} · generated {fmt(b.created_at)}</p>
      <p className="summary">{b.summary}</p>
      <Changes rows={b.changes} />
      <section>
        <h2>Key indicators</h2>
        <dl className="indicators">
          {b.indicators.map((x, i) => (
            <div key={i}>
              <dt>{x.name}</dt>
              <dd>{x.value}</dd>
              <span className="src">{x.source}</span>
            </div>
          ))}
        </dl>
      </section>
      <section>
        <h2>Risks and implications</h2>
        <ul className="risks">{b.risks.map((r, i) => <li key={i}>{r}</li>)}</ul>
      </section>
      <section>
        <h2>Sources</h2>
        <ul className="links">
          {b.sources.map((s, i) => (
            <li key={i}><a href={s.url} target="_blank" rel="noreferrer">{s.name}</a></li>
          ))}
        </ul>
      </section>
    </article>
  );
}

export default function App() {
  const [list, setList] = useState([]);
  const [current, setCurrent] = useState(null);
  const [sources, setSources] = useState([]);
  const [view, setView] = useState("brief");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const refresh = async () => {
    try {
      const l = await listBriefings();
      setList(l);
      if (l.length && !current) setCurrent(await getBriefing(l[0].id));
    } catch (e) {
      setError("Can't reach the backend. Start it with: uvicorn main:app --reload");
    }
  };

  useEffect(() => {
    refresh();
    getSources().then(setSources).catch(() => {});
  }, []);

  const generate = async () => {
    setLoading(true);
    setError("");
    try {
      const b = await generateBriefing();
      setCurrent(b);
      setView("brief");
      setList(await listBriefings());
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  };

  const open = async (id) => {
    setCurrent(await getBriefing(id));
    setView("brief");
  };

  return (
    <div className="shell">
      <aside>
        <h1>CreditPolicy AI</h1>
        <p className="tagline">Credit-market briefings that remember the last one.</p>
        <button className="primary" onClick={generate} disabled={loading}>
          {loading ? "Reading sources…" : "Generate briefing"}
        </button>
        <nav>
          <button className={view === "brief" ? "on" : ""} onClick={() => setView("brief")}>Latest briefing</button>
          <button className={view === "sources" ? "on" : ""} onClick={() => setView("sources")}>Sources</button>
        </nav>
        <h3>History</h3>
        {list.length === 0 && <p className="muted">No briefings yet. Generate your first one.</p>}
        <ul className="history">
          {list.map((h) => (
            <li key={h.id}>
              <button className={current?.id === h.id ? "on" : ""} onClick={() => open(h.id)}>
                <span>{fmt(h.created_at)}</span>
                <small>{h.conclusions.slice(0, 70)}…</small>
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <main>
        {error && <div className="error" role="alert">{error}</div>}
        {view === "sources" ? (
          <section>
            <h2>Sources tracked</h2>
            <ul className="links">
              {sources.map((s, i) => (
                <li key={i}>
                  <a href={s.url} target="_blank" rel="noreferrer">{s.name}</a>{" "}
                  <span className="muted">({s.category})</span>
                </li>
              ))}
            </ul>
          </section>
        ) : current ? (
          <Brief b={current} />
        ) : (
          !error && (
            <p className="empty">
              Select “Generate briefing” to scrape today’s sources and compare them with earlier briefings.
            </p>
          )
        )}
      </main>
    </div>
  );
}