"use client";
import {useState} from "react";

const examples = ["Download a blob to a stream", "Latest Azure storage redundancy guidance", "Compare the Python SDK with current Azure authentication guidance"];

export default function Search() {
  const [query, setQuery] = useState(examples[0]);
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function search(event) {
    event.preventDefault();
    setBusy(true); setError(""); setData(null);
    try {
      const response = await fetch("/api/search", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({query, user_id:"public"})});
      if (!response.ok) throw new Error("Search failed. Check that the router API is running.");
      setData(await response.json());
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  return <main><header><strong>Atlas</strong><span>Adaptive Retrieval Router</span></header>
    <section><h1>Azure reference search</h1><p>Search installed Python SDK references and current Microsoft Learn guidance.</p>
    <form onSubmit={search}><label htmlFor="query">Search question</label><div><input id="query" value={query} required minLength={2} maxLength={2000} onChange={e=>setQuery(e.target.value)}/><button disabled={busy}>{busy?"Searching…":"Search ↗"}</button></div></form>
    <aside>{examples.map((e,i)=><button key={e} disabled={busy} onClick={()=>setQuery(e)}>{["SDK example","Live example","Hybrid example"][i]}</button>)}</aside></section>
    <article aria-live="polite">{error && <p role="alert">{error}</p>}{data && <><h2>{data.results.length} results</h2><p><b>{data.decision.route}</b> · {data.decision.reasoning}</p>
    {data.warnings.map(w=><p key={w} role="alert">{w}</p>)}
    <ol>{data.results.map(r=><li key={r.document_id}><small>{r.source} · {r.metadata.version || r.retrieval_method}</small><h3><a href={r.url} target="_blank" rel="noreferrer">{r.title}</a></h3><p>{r.snippet}</p></li>)}</ol></>}</article></main>
}
