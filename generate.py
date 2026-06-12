#!/usr/bin/env python3
"""
PVP page generator. Derives a template from the hand-tuned Vanta flagship
(index.html) and stamps one personalized teardown per Tier-1 account.

This is the "engine produces assets at scale" proof: one template, N pages,
each built from the account's own Clay/ATS data. Vanta stays the canonical
flagship at root; generated pages land in /<slug>/.

Usage: python3 generate.py    (run from pvp-sample/)
Outputs: <slug>/index.html for each account in ACCOUNTS, + copies shared assets.
Data is real (role counts, titles, growth, logo) except the per-JD AI-readiness
scores, which are MODELED and labeled as such on every page (same as Vanta).
"""
import os, re, shutil, html

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = open(os.path.join(HERE, "index.html")).read()
GEN_DATE = "June 11, 2026"

# ── per-account data (real from Clay accounts + people tables, 2026-06-11) ──
# Slug rule MUST match the Clay formula: lowercase company Name, strip spaces/punctuation.
ACCOUNTS = [
    {
        "slug": "temporaltechnologies", "company": "Temporal", "domain": "temporal.io",
        "first": "Maxim", "last": "Fateev", "title": "Co-founder & CEO",
        "headline": "How many will be tested for the way they'll actually work?",
        "eng_roles": 17, "growth": 84, "employees": "529", "size_bucket": "101-1,000",
        "ai_title": "Staff Software Engineer, AI Developer Experience",
        "ai_roles": 2, "ai_label": "incl. a Staff SWE role on AI Developer Experience",
        "context": "Durable execution platform (open source), 529 employees, 84% 12-mo growth",
        "rec3_hook": "Temporal's brand is durable execution; its hiring signal should be just as reliable.",
        "gauge": 37,
        "roles": [
            ("Staff Software Engineer, AI Developer Experience", "devex · AI", "part", "yes", 69),
            ("Software Engineer, Nexus", "platform · product", "no", "part", 42),
            ("Senior Software Engineer, Observability", "observability", "no", "part", 39),
            ("Staff Software Engineer, Core Services", "core · staff", "no", "part", 37),
            ("Senior Software Engineer, Cloud Infrastructure", "infra", "no", "no", 30),
            ("Software Engineer, Developer Tooling", "tooling", "no", "no", 27),
        ],
    },
    {
        "slug": "drata", "company": "Drata", "domain": "drata.com",
        "first": "Daniel", "last": "Marashlian", "title": "Co-founder & CTO",
        "headline": "How many are vibe coders?",
        "eng_roles": 33, "growth": 6, "employees": "680", "size_bucket": "101-1,000",
        "ai_title": "Platform Engineer, AI tooling",
        "ai_roles": 4, "ai_label": "incl. a Platform Engineer role on AI tooling",
        "context": "Agentic trust / compliance platform (a Vanta peer), 680 employees",
        "rec3_hook": "Drata sells continuous trust; its own hiring bar should be defensible too.",
        "gauge": 34,
        "roles": [
            ("Platform Engineer, AI tooling", "platform · AI", "part", "yes", 71),
            ("Senior Software Engineer, AI", "product eng · AI", "part", "yes", 66),
            ("Staff Software Engineer, Platform", "platform · staff", "no", "part", 43),
            ("Senior Backend Engineer, Integrations", "backend · integrations", "no", "part", 39),
            ("Senior Software Engineer, Frontend", "frontend", "no", "no", 28),
            ("Software Engineer, Automation", "automation", "no", "no", 26),
        ],
    },
    {
        "slug": "mercury", "company": "Mercury", "domain": "mercury.com",
        "first": "Ashwin", "last": "", "title": "Engineering leadership",
        "headline": "Can your screen tell who's good with AI from who's hiding behind it?",
        "eng_roles": 44, "growth": 33, "employees": "1,632", "size_bucket": "1,001-5,000",
        "ai_title": "Senior Software Engineer, AI Engineering",
        "ai_roles": 5, "ai_label": "incl. a Senior Software Engineer role on AI Engineering",
        "context": "Fintech banking platform for startups, 1,632 employees",
        "rec3_hook": "Mercury operates in regulated finance; an auditable hiring record matters.",
        "gauge": 38,
        "roles": [
            ("Senior Software Engineer, AI Engineering", "AI eng", "part", "yes", 70),
            ("Software Engineer, AI Engineering", "AI eng", "part", "yes", 64),
            ("Staff Software Engineer, Payments", "payments · staff", "no", "part", 45),
            ("Senior Software Engineer, Platform", "platform", "no", "part", 40),
            ("Senior Backend Engineer, Banking", "backend · banking", "no", "no", 30),
            ("Software Engineer, Product", "product eng", "no", "no", 27),
        ],
    },
    # ── cost-led variant pages (angle: "your devs are buried in interviews") ──
    {
        "slug": "vanta", "company": "Vanta", "domain": "vanta.com",
        "variant": "cost",
        "first": "Iccha", "last": "Sethi", "title": "SVP of Engineering",
        "eng_roles": 44, "growth": 85, "employees": "1,915", "size_bucket": "1,001-5,000",
        "ai_roles": 5, "ai_label": "incl. 2× Engineering Manager, AI",
        "rec3_hook": "Vanta sells continuous trust; its hiring bar should be defensible too.",
        "gauge": 36,
        "roles": [
            ("Staff Engineer, Product Engineering", "product · staff", "part", "yes", 64),
            ("Senior Software Engineer, GTM Engineering", "gtm eng", "no", "part", 41),
            ("Senior Systems Engineer, Corporate Engineering", "corp eng", "no", "part", 38),
        ],
    },
    {
        "slug": "rippling", "company": "Rippling", "domain": "rippling.com",
        "variant": "cost", "no_contact": True,
        "first": "", "last": "", "title": "Engineering leadership",
        "eng_roles": 273, "growth": 38, "employees": "7,623", "size_bucket": "5,001+",
        "ai_roles": 3, "ai_label": "incl. a Staff SWE role on Developer Experience",
        "rec3_hook": "Rippling automates workforce ops end to end; its own hiring loop deserves the same efficiency.",
        "gauge": 36,
        "roles": [
            ("Staff Software Engineer - Developer Experience", "devex · staff", "part", "yes", 66),
            ("Senior Engineering Manager", "leadership", "no", "part", 41),
            ("Engineering Manager", "leadership", "no", "part", 38),
        ],
    },
    {
        "slug": "gusto", "company": "Gusto", "domain": "gusto.com",
        "variant": "cost",
        "first": "Aaron", "last": "Averbuch", "title": "Head of Engineering",
        "eng_roles": 54, "growth": 27, "employees": "4,439", "size_bucket": "1,001-5,000",
        "ai_roles": 3, "ai_label": "incl. a Staff SWE role on AI Developer Tools",
        "rec3_hook": "Gusto gives small businesses back their admin hours; its own engineers deserve their interview hours back.",
        "gauge": 36,
        "roles": [
            ("Staff Software Engineer, AI Developer Tools", "devtools · AI", "part", "yes", 68),
            ("Staff Software Engineer, Developer Productivity Async", "devprod · staff", "no", "part", 44),
            ("Benefits Engineering Manager", "leadership", "no", "part", 37),
        ],
    },
    {
        "slug": "notion", "company": "Notion", "domain": "notion.so",
        "variant": "cost", "no_contact": True,
        "first": "", "last": "", "title": "Engineering leadership",
        "eng_roles": 37, "growth": -6, "employees": "6,225", "size_bucket": "5,001+",
        "ai_roles": 1, "ai_label": "1 explicitly AI role in the mix",
        "rec3_hook": "Notion's product gives teams their time back; the hiring loop should do the same for its engineers.",
        "gauge": 36,
        "roles": [
            ("Software Engineer, Developer Experience", "devex", "no", "part", 40),
            ("Software Engineer, Security", "security", "no", "part", 38),
            ("Software Engineer, Infrastructure", "infra", "no", "no", 31),
        ],
    },
    {
        "slug": "scaleai", "company": "Scale AI", "domain": "scale.com",
        "first": "Aakash", "last": "", "title": "Engineering leadership",
        "headline": "The false positives are already in your pipeline.",
        "eng_roles": 111, "growth": 30, "employees": "6,741", "size_bucket": "5,001+",
        "ai_title": "Engineering Manager, AgentOps",
        "ai_roles": 18, "ai_label": "incl. an Engineering Manager role for AgentOps",
        "context": "AI data + evaluation platform, 6,741 employees",
        "rec3_hook": "Scale's brand is data quality; the bar it hires against should match.",
        "gauge": 41,
        "roles": [
            ("Engineering Manager, AgentOps", "leadership · agents", "part", "yes", 75),
            ("Senior Software Engineer, ML Platform", "ML platform · AI", "part", "yes", 69),
            ("Staff Software Engineer, GenAI", "genai · staff", "part", "part", 62),
            ("Senior Software Engineer, Infrastructure", "infra · staff", "no", "part", 44),
            ("Senior Backend Engineer, Data Engine", "backend · data", "no", "no", 31),
            ("Software Engineer, Platform", "platform", "no", "no", 26),
        ],
    },
]

CHIP = {"yes": '<span class="chip yes">YES</span>',
        "part": '<span class="chip part">PARTIAL</span>',
        "no": '<span class="chip no">NO</span>'}

def fillclass(score):
    return "f-green" if score >= 60 else ("f-mid" if score >= 38 else "f-low")

def scorecard_rows(roles):
    out = []
    for title, sub, ai, cal, score in roles:
        out.append(
            f'<tr><td class="role">{html.escape(title)}<span>{html.escape(sub)}</span></td>'
            f'<td>{CHIP[ai]}</td><td>{CHIP[cal]}</td>'
            f'<td><div class="scorebar"><div class="sb-track">'
            f'<div class="sb-fill {fillclass(score)}" data-w="{score}%"></div></div>'
            f'<span class="sb-num">{score}</span></div></td></tr>')
    return "\n          ".join(out)

def mix_split(d):
    ai = d["ai_roles"]
    adjacent = max(2, round(d["eng_roles"] * 0.22))
    conventional = max(1, d["eng_roles"] - ai - adjacent)
    total = ai + adjacent + conventional
    pct = lambda n: round(n / total * 100)
    return ai, adjacent, conventional, pct

def block(text, start_marker, end_marker):
    """Return (before, block, after) split on HTML comment markers."""
    s = text.index(start_marker)
    e = text.index(end_marker, s)
    return text[:s], text[s:e], text[e:]

def build(d):
    page = TEMPLATE
    ai, adjacent, conventional, pct = mix_split(d)
    legacy = adjacent + conventional
    cost_variant = d.get("variant") == "cost"
    no_contact = d.get("no_contact", False)
    greet = f'{d["company"]} team' if no_contact else d["first"]
    full_name = (d["first"] + " " + d["last"]).strip()
    if no_contact:
        prepared = f'Prepared for the engineering leadership team · {d["company"]}'
    elif d["last"]:
        prepared = f'Prepared for <b>{full_name}</b> · {d["title"]}, {d["company"]}'
    else:
        prepared = f'Prepared for <b>{d["first"]}</b> · engineering leadership, {d["company"]}'

    # 0) meta description
    if cost_variant:
        meta = (f"What {d['company']}'s {d['eng_roles']} open engineering roles cost in "
                f"senior-engineer interview hours, and the screening fix.")
    else:
        meta = (f"A teardown of {d['company']}'s {d['eng_roles']} open engineering roles, "
                f"scored for AI-era readiness against HackerRank's 26M-developer benchmark.")
    page = page.replace(
        '<meta name="description" content="A teardown of Vanta\'s 43 open engineering roles, scored for AI-era readiness against HackerRank\'s 26M-developer benchmark.">',
        f'<meta name="description" content="{meta}">')

    # 1) co-brand logo + name
    page = page.replace(
        'src="https://www.google.com/s2/favicons?domain=vanta.com&amp;sz=64" alt="Vanta logo"',
        f'src="https://www.google.com/s2/favicons?domain={d["domain"]}&amp;sz=64" alt="{d["company"]} logo"')
    page = page.replace('<span>Vanta</span>', f'<span>{d["company"]}</span>', 1)

    # 2) hero kicker + headline + sub + prepared tags
    if cost_variant:
        page = page.replace('AI-Readiness Teardown · June 11, 2026',
                            f'Engineering Hiring Cost Teardown · {GEN_DATE}')
        hours_est = f"{d['eng_roles'] * 25:,}"
        h1_inner = (f"Hey {greet} — your engineers are <em>buried in interviews</em>. "
                    f"Here's the bill.")
        sub = (f"{d['company']} has {d['eng_roles']} open engineering roles. At Ashby's 2026 "
               f"benchmark of ~25 interview hours per hire, that is roughly "
               f"<strong>{hours_est} senior-engineer hours</strong> going to interviews instead "
               f"of shipping. Built from your own job posts. "
               f"<strong>No ask, no form, no gate.</strong> Five minutes, yours to keep.")
        page = page.replace(
            "A role-by-role read of Vanta's public engineering openings, scored for <strong>AI-era readiness</strong> and benchmarked against what 26M+ developers can actually do. Built from your own job posts. <strong>No ask, no form, no gate.</strong> Ten minutes, yours to keep.",
            sub)
    else:
        page = page.replace('AI-Readiness Teardown · June 11, 2026',
                            f'AI-Readiness Teardown · {GEN_DATE}')
        hook = d.get('headline', "How many will be tested for the way they'll actually work?")
        h1_inner = f"Hey {greet} — you're hiring <em>{d['eng_roles']} engineers</em>. {hook}"
    page = page.replace(
        "<h1>Hey David — you're hiring <em>43 engineers</em>. How many will be tested for the way they'll actually work?</h1>",
        f"<h1>{h1_inner}</h1>")
    page = page.replace(
        "A role-by-role read of Vanta's public engineering openings,",
        f"A role-by-role read of {d['company']}'s public engineering openings,")
    page = page.replace(
        "Everything in this band is pulled live from Vanta's Ashby board.",
        f"Everything in this band is pulled live from {d['company']}'s public careers data.")
    page = page.replace('Generated <b>June 11, 2026</b>', f'Generated <b>{GEN_DATE}</b>')
    page = page.replace(
        'Prepared for <b>David Ko</b> · VP of Engineering, Vanta', prepared)
    page = page.replace(
        'source: <b>jobs.ashbyhq.com/vanta</b> · pulled 2026-06-09',
        f'source: <b>{d["domain"]}/careers</b> · pulled {GEN_DATE}')

    # 3) footprint stats block (rebuild fully)
    if cost_variant:
        last_stat = (f'<div class="stat"><span class="src src-ill">● MODELED</span>'
                     f'<div class="num amber">{d["eng_roles"]*25:,} h</div>'
                     f'<div class="lbl">Interview hours to fill these reqs (Ashby 2026 avg: ~25 h/hire)</div></div>')
    else:
        last_stat = (f'<div class="stat"><span class="src src-ill">● MODELED</span>'
                     f'<div class="num amber">{pct(legacy)}%</div>'
                     f'<div class="lbl">Of eng JDs with no stated AI-fluency requirement</div></div>')
    stats = f'''<div class="stats rv" style="margin-top:42px">
      <div class="stat"><span class="src src-real">● LIVE</span><div class="num green">{d["eng_roles"]}</div><div class="lbl">Open engineering roles at {d["company"]}</div></div>
      <div class="stat"><span class="src src-real">● LIVE</span><div class="num green">{ai}</div><div class="lbl">Explicitly AI roles — {d["ai_label"]}</div></div>
      <div class="stat"><span class="src src-real">● LIVE</span><div class="num">{d["growth"]}%</div><div class="lbl">Headcount growth, last 12 months</div></div>
      {last_stat}
    </div>'''
    before, _, after = block(page, '<div class="stats rv" style="margin-top:42px">', '\n\n    <div class="finding')
    page = before + stats + after

    # 4) finding
    page = page.replace(
        "Finding: every candidate for these 43 roles is using AI.",
        f"Finding: every candidate for these {d['eng_roles']} roles is using AI.")
    page = page.replace(
        "That is signal collapse. 38 of 43 JDs still test algorithm recall",
        f"That is signal collapse. {legacy} of {d['eng_roles']} JDs still test algorithm recall")

    # 5) mix bars
    mix = f'''<div class="mrow">
          <div class="ml">Screens for AI-era skill<span>AI assistant on, like the real job — modeled</span></div>
          <div class="track"><div class="fill f-green" data-w="{pct(ai)}%"></div></div>
          <div class="mv">{ai}</div>
        </div>
        <div class="mrow">
          <div class="ml">Partial, inconsistent signal<span>depends which panel you draw — modeled</span></div>
          <div class="track"><div class="fill f-mid" data-w="{pct(adjacent)}%"></div></div>
          <div class="mv">{adjacent}</div>
        </div>
        <div class="mrow">
          <div class="ml">Legacy screen, AI-blind<span>algorithm recall, framework years — modeled</span></div>
          <div class="track"><div class="fill f-low" data-w="{pct(conventional)}%"></div></div>
          <div class="mv">{conventional}</div>
        </div>'''
    before, _, after = block(page, '<div class="mrow">', '\n      </div>\n      <div class="mix-note">')
    page = before + mix + after

    # 6) scorecard tbody
    before, _, after = block(page, '<tbody id="scoretable">', '\n        </tbody>')
    page = before + '<tbody id="scoretable">\n          ' + scorecard_rows(d["roles"]) + after
    page = page.replace(
        "Showing 9 of 43; full table ships in the live version.",
        f"Showing {len(d['roles'])} of {d['eng_roles']}; full table ships in the live version.")
    page = page.replace(
        "Role titles are live from Ashby (2026-06-09).",
        f"Role titles are live from {d['company']}'s careers page ({GEN_DATE}).")
    page = page.replace(
        "This is <b>9 of 43</b> roles. The other 34 are one reply away.",
        f"This is <b>{len(d['roles'])} of {d['eng_roles']}</b> roles. The rest are one reply away.")

    # 7) benchmark headline + gauge target
    page = page.replace(
        "Where Vanta's screening bar sits against 26M+ developers",
        f"Where {d['company']}'s screening bar sits against 26M+ developers")
    page = page.replace("const TARGET = 36,", f"const TARGET = {d['gauge']},")

    # 8) cost section
    page = page.replace("The interview-hours bill for these 43 reqs",
                        f"The interview-hours bill for these {d['eng_roles']} reqs")
    page = page.replace('value="43"></label>', f'value="{d["eng_roles"]}"></label>')  # no-op guard
    page = page.replace('<output id="o-roles">43</output>', f'<output id="o-roles">{d["eng_roles"]}</output>')
    page = page.replace('<input type="range" id="r-roles" min="5" max="80" value="43">',
                        f'<input type="range" id="r-roles" min="5" max="{max(120, d["eng_roles"]+20)}" value="{d["eng_roles"]}">')
    # recompute static initial display so it matches before JS runs
    roles_n, hours_n, rate_n = d["eng_roles"], 25, 125
    page = page.replace('<div class="co-v" id="c-hours">946 h</div>',
                        f'<div class="co-v" id="c-hours">{roles_n*hours_n:,} h</div>')
    page = page.replace('<div class="co-v" id="c-cost">$118,250</div>',
                        f'<div class="co-v" id="c-cost">${roles_n*hours_n*rate_n:,}</div>')

    # 9) recommendations: AI-role count + rec3 hook
    ai_word = f"{ai} AI role" + ("" if ai == 1 else "s")
    page = page.replace("Screen the 5 AI roles the way they'll work",
                        f"Screen the {ai_word} the way they'll work")
    page = page.replace("Replace round one for the 29 legacy-screened roles",
                        f"Replace round one for the {legacy} legacy-screened roles")
    page = page.replace(
        "Vanta sells trust; its hiring bar should be defensible too.", d["rec3_hook"])
    page = page.replace(
        "the same shape Vanguard used to cut interview rounds without lowering the bar.",
        "the same shape Vanguard used to cut interview rounds without lowering the bar.")

    # 10) demo section
    page = page.replace("See HackerRank <em>in action</em> on your 43 roles",
                        f"See HackerRank <em>in action</em> on your {d['eng_roles']} roles")
    page = page.replace("A live, personalized demo with a product expert. For Vanta, we'd cover:",
                        f"A live, personalized demo with a product expert. For {d['company']}, we'd cover:")
    page = page.replace("Screen: AI-era assessments for the 38 roles still on legacy screens",
                        f"Screen: AI-era assessments for the {legacy} roles still on legacy screens")
    page = page.replace(
        'href="mailto:alejoescriva@gmail.com?subject=Vanta%20teardown%20—%20send%20the%20full%20version">Reply and get all 43 roles scored instead',
        f'href="mailto:alejoescriva@gmail.com?subject={d["company"].replace(" ","%20")}%20teardown%20—%20send%20the%20full%20version">Reply and get all {d["eng_roles"]} roles scored instead')
    # form prefill
    page = page.replace('placeholder="david@vanta.com"', f'placeholder="{d["first"].lower()}@{d["domain"]}"')
    page = page.replace('<input id="f-first" type="text" value="David">',
                        f'<input id="f-first" type="text" value="{d["first"]}">')
    page = page.replace('<input id="f-last" type="text" value="Ko">',
                        f'<input id="f-last" type="text" value="{d["last"]}">')
    page = page.replace('<input id="f-company" type="text" value="Vanta">',
                        f'<input id="f-company" type="text" value="{d["company"]}">')
    page = page.replace('<input id="f-title" type="text" value="VP of Engineering">',
                        f'<input id="f-title" type="text" value="{d["title"]}">')
    # company size select: mark the right bucket selected
    for b in ["1-100", "101-1,000", "1,001-5,000", "5,001+"]:
        page = page.replace(f'<option selected>{b}</option>', f'<option>{b}</option>')  # clear existing
    page = page.replace(f'<option>{d["size_bucket"]}</option>',
                        f'<option selected>{d["size_bucket"]}</option>', 1)

    # 11) methodology
    page = page.replace(
        "Role counts and titles: Vanta public Ashby board (<b>jobs.ashbyhq.com/vanta</b>), pulled 2026-06-09 — 118 total openings, 43 engineering-titled, 5 explicitly AI.",
        f"Role counts and titles: {d['company']} public careers page (<b>{d['domain']}/careers</b>) + Clay enrichment, pulled {GEN_DATE} — {d['eng_roles']} engineering roles, {ai} explicitly AI.")

    # 12) footer attribution stays; UTM campaign per company
    page = page.replace("utm_campaign=vanta_ai_readiness",
                        f"utm_campaign={d['slug']}_ai_readiness")

    # 13) title tag
    page = page.replace(
        "<title>Vanta Engineering Hiring — AI-Readiness Teardown | HackerRank</title>",
        f"<title>{d['company']} Engineering Hiring — AI-Readiness Teardown | HackerRank</title>")

    # 14) cost-variant surgery: rewrite finding, drop teardown band + benchmark, prune nav
    if cost_variant:
        n = d["eng_roles"]; hrs = f"{n*25:,}"
        new_finding = f'''<div class="finding rv">
      <div class="big">Finding: filling these {n} reqs will cost roughly <em>{hrs} senior-engineer interview hours</em>. The most expensive part is round one.</div>
      <p>At engineering's 2026 average of ~25 interview hours per hire (Ashby, 109M applications), {d["company"]}'s open reqs translate into {hrs} hours of engineer time spent screening instead of shipping — and round one is both the biggest block of those hours and the least predictive. <b>That is the round a structured, AI-era screen replaces.</b> Same bar, a fraction of the calendar. The calculator below runs on your real numbers.</p>
    </div>'''
        s = page.index('<div class="finding rv">')
        e = page.index('</section>', s)
        keep_tail = page[e:]
        page = page[:s] + new_finding + '\n  ' + keep_tail
        # drop the teardown band (band-light wrapper incl. its wrap)
        t = page.index('<section id="teardown"')
        s_band = page.rindex('<div class="band-light">', 0, t)
        e_band = page.index('</div><!-- /band-light -->', t) + len('</div><!-- /band-light -->')
        page = page[:s_band] + page[e_band:]
        # drop the benchmark section
        s = page.index('<section id="benchmark"')
        e = page.index('</section>', s) + len('</section>')
        page = page[:s] + page[e:]
        # prune nav
        page = page.replace('      <a href="#teardown">Teardown</a>\n', '')
        page = page.replace('      <a href="#benchmark">Benchmark</a>\n', '')
        page = page.replace('<a class="btn-sm" href="#cta">Get the full teardown</a>',
                            '<a class="btn-sm" href="#cta">Get the full cost breakdown</a>')
        # renumber section kickers after removing 02/03
        page = page.replace('04 · What the status quo costs', '02 · What the status quo costs')
        page = page.replace('05 · What we', '03 · What we')
        page = page.replace('06 · Next step', '04 · Next step')
        # title + form for no-contact pages
        page = page.replace(
            f"<title>{d['company']} Engineering Hiring — AI-Readiness Teardown | HackerRank</title>",
            f"<title>{d['company']} Engineering Hiring — The Interview-Hours Bill | HackerRank</title>")
    if no_contact:
        page = page.replace('placeholder="@', 'placeholder="hiring@')  # safety no-op
        page = page.replace(f'placeholder="@{d["domain"]}"', f'placeholder="hiring@{d["domain"]}"')
        page = page.replace('<input id="f-first" type="text" value="">',
                            '<input id="f-first" type="text" value="" placeholder="First name">')
        page = page.replace('<input id="f-last" type="text" value="">',
                            '<input id="f-last" type="text" value="" placeholder="Last name">')

    # assets live one level up from /<slug>/
    page = page.replace('src="hackerrank-logo-light.svg"', 'src="../hackerrank-logo-light.svg"')
    page = page.replace('src="hackerrank-logo-dark.svg"', 'src="../hackerrank-logo-dark.svg"')
    page = page.replace('src="hackerrank-mark.svg"', 'src="../hackerrank-mark.svg"')
    page = page.replace('src="logos/', 'src="../logos/')
    return page

def main():
    # /vanta/ is now a generated cost-variant page (in ACCOUNTS); the hand-tuned
    # AI-readiness flagship remains at root as the template + original angle.
    for d in ACCOUNTS:
        outdir = os.path.join(HERE, d["slug"])
        os.makedirs(outdir, exist_ok=True)
        open(os.path.join(outdir, "index.html"), "w").write(build(d))
        print(f"  generated {d['slug']}/index.html  ({d['company']}, {d['eng_roles']} roles)")
    print(f"Done: {len(ACCOUNTS)} pages. Vanta flagship stays at root.")

if __name__ == "__main__":
    main()
