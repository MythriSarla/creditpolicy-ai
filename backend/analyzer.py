"""LLM analysis. Falls back to a demo brief when keys are missing."""
import json, os, re, random

SYSTEM = """You are a credit-market analyst for an Indian bank's credit team.
Using ONLY the scraped sources and the previous briefing conclusions, write a briefing.
Return ONLY valid JSON, no markdown fences, with this shape:
{
 "summary": "max 50 words, lead with the single most important change for lending",
 "indicators": [{"name": str, "value": str, "source": str}],
 "changes": [{"topic": str, "previous": str, "current": str,
              "direction": "up"|"down"|"new"|"unchanged", "impact": str}],
 "risks": [str],
 "sources": [{"name": str, "url": str}]
}
Rules:
- Always include the policy repo rate, CRR and SLR in indicators if they appear in the sources. If a figure is not in the sources, omit it rather than estimating.
- If there is no previous briefing, mark changes as direction "new".
- Use "up" for tightening or increases, "down" for easing or decreases.
- Split the briefing into 4 to 6 separate topics, one table row each (for example credit growth, deposit growth, card usage, liquidity operations, NBFC rules, SEBI circulars). Never put a summary or a long paragraph in a table cell.
- "previous" is the value listed for the same topic under "Topics" in the previous briefing. If the topic is not listed there, use "n/a" and direction "new".
- Use "unchanged" only when the facts are identical to the previous value. If "current" mentions a date, auction, circular or figure that is not in "previous", the direction must not be "unchanged".
- Never invent figures."""


def call_gemini(system, user):
    import time
    import requests

    models = [
        os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        "gemini-3.5-flash-lite",
        "gemini-flash-lite-latest",
        "gemini-3.1-flash-lite",
        "gemini-3.6-flash",
        "gemini-3.7-flash",
        "gemini-3.8-flash",
        "gemini-flash-latest",
    ]
    last_err = None

    for model in dict.fromkeys(models):  # remove duplicates, keep order
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        for attempt in range(2):
            try:
                r = requests.post(
                    url,
                    headers={"x-goog-api-key": os.getenv("GEMINI_API_KEY")},
                    json={
                        "systemInstruction": {"parts": [{"text": system}]},
                        "contents": [{"role": "user", "parts": [{"text": user}]}],
                        "generationConfig": {"responseMimeType": "application/json"},
                    },
                    timeout=120,
                )
            except requests.RequestException as e:  # dropped connection or timeout
                last_err = f"{model}: network error {e}"
                time.sleep(4)
                continue

            if r.status_code == 200:
                try:
                    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"[gemini] used {model}")
                    return text
                except (KeyError, IndexError):
                    last_err = f"{model}: empty answer"
                    break  # try the next model

            last_err = f"{model}: {r.status_code} {r.text[:150]}"
            print(f"[gemini] {model} -> {r.status_code}")
            if r.status_code in (429, 500, 503):  # busy: wait, retry, then next model
                time.sleep(4)
                continue
            break  # 404 etc.: skip to the next model

    raise RuntimeError(f"All Gemini models failed. Last error: {last_err}")


def parse_json(text):
    """Pull the JSON object out of the model's reply, even if it adds extra text."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("The model did not return JSON. Try generating again.")
    return json.loads(text[start:end + 1])


def fmt_past(p):
    """Describe a previous briefing, including its topics, so the model can compare."""
    topics = "\n".join(f"    * {c['topic']}: {c['current']}" for c in p.get("changes", []))
    inds = "; ".join(f"{i['name']}={i['value']}" for i in p.get("indicators", []))
    return f"- {p['created_at']}: {p['summary']}\n  Topics:\n{topics}\n  Indicators: {inds}"


def build_brief(df, past, extra=""):
    use_gemini = bool(os.getenv("GEMINI_API_KEY"))
    use_claude = bool(os.getenv("ANTHROPIC_API_KEY"))
    if df.empty or not (use_gemini or use_claude):
        return demo_brief(len(past))

    
    for r in df.itertuples():
        text = r.content.lower()
        print(f"[scrape] {r.source} | {len(r.content)} chars | repo: {'repo' in text} | CRR: {'crr' in text} | SLR: {'slr' in text}")

    sources_txt = "\n\n".join(
        f"### {r.source} [{r.category}] {r.url}\n{r.content}" for r in df.itertuples()
    )
    past_txt = "\n".join(fmt_past(p) for p in past) or "None"
    if extra:  # recalled context from Memento (empty when Memento is off)
        past_txt += f"\n\nMEMENTO MEMORY:\n{extra}"
    user_msg = f"PREVIOUS BRIEFINGS:\n{past_txt}\n\nCURRENT SOURCES:\n{sources_txt}"

    if use_gemini:
        text = call_gemini(SYSTEM, user_msg)
    else:
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=os.getenv("LLM_MODEL", "claude-sonnet-5-5"),
            max_tokens=3000,
            system=SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        text = msg.content[0].text

    return parse_json(text)


def demo_brief(n_past):
    """Sample data so the UI works before you add API keys."""
    repo = 6.50 - 0.25 * min(n_past, 2)
    return {
        "summary": "Demo briefing. Policy stance is steady with a cautious tone on unsecured retail lending. "
                   "Inflation remains inside the target band, leaving room for rate easing.",
        "indicators": [
            {"name": "Repo rate", "value": f"{repo:.2f}%", "source": "RBI Monetary Policy"},
            {"name": "CPI inflation", "value": f"{random.choice(['4.2','4.5','4.8'])}%", "source": "MoSPI Releases"},
            {"name": "Gross NPA (banks)", "value": "2.6%", "source": "Economic Times BFSI"},
        ],
        "changes": [
            {"topic": "Repo rate", "previous": f"{repo + 0.25:.2f}%" if n_past else "n/a",
             "current": f"{repo:.2f}%", "direction": "down" if n_past else "new",
             "impact": "Cheaper funding; expect pressure on lending spreads."},
            {"topic": "Unsecured retail lending", "previous": "Watch list" if n_past else "n/a",
             "current": "Higher risk weights discussed", "direction": "up" if n_past else "new",
             "impact": "Review exposure limits for personal loans and cards."},
            {"topic": "Housing finance norms", "previous": "No change", "current": "No change",
             "direction": "unchanged", "impact": "None."},
        ],
        "risks": ["Rising stress in unsecured retail segments",
                  "Global rate volatility affecting external borrowing costs"],
        "sources": [{"name": "RBI Monetary Policy", "url": "https://www.rbi.org.in/Scripts/MonetaryPolicy.aspx"},
                    {"name": "MoSPI Releases", "url": "https://mospi.gov.in/"}],
    }