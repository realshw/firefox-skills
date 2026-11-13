# Navigate the bilibili tab to the keyword results page and return candidate links. The results SPA
# hydrates its cards gradually, so wait until the link set stops growing rather than sleeping. `pgc` marks
# PGC entries — with a title as keyword those are the official, playable ones.
import urllib.parse

exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/wait_js.py").read())
exec(open("snippets/common/wait_stable.py").read())


def search_links(driver, keyword, limit=40, timeout=30):
    site_tab(driver, "bilibili.com")
    driver.get('https://search.bilibili.com/all?keyword=' +
               urllib.parse.quote(keyword))
    js = r"""
    const out = [], seen = new Set();
    for (const a of document.querySelectorAll('a')) {
      const h = (a.href || '').split(/[?#]/)[0];
      if (!/\/(bangumi\/play|bangumi\/media|video\/BV)/.test(h)) continue;
      if (seen.has(h)) continue;
      seen.add(h);
      let ctx = '', el = a;
      for (let i = 0; i < 6 && el; i++) {
        el = el.parentElement;
        if (el && (el.innerText || '').length > 60) { ctx = el.innerText; break; }
      }
      out.push({href: h,
                text: (a.innerText || a.getAttribute('title') || '').trim().replace(/\s+/g, ' ').slice(0, 120),
                ctx: (ctx || '').trim().replace(/\s+/g, ' ').slice(0, 200),
                pgc: /\/(bangumi\/play|bangumi\/media)/.test(h)});
    }
    return out;
    """
    links = wait_js_stable(
        driver, as_expr(js), timeout, tick=1.0, stable_ticks=2) or []
    return links[:limit]
