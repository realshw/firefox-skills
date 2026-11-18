"""Read one labelled row of a Wikipedia article's infobox."""

import re

from selenium.webdriver.common.by import By

exec(open("snippets/common/wait_js.py").read())


def wikipedia_read_infobox_row(driver, label, flags=re.I, timeout=15):
    """Print and return the infobox row whose label matches `label` (a regex), as {"label", "value", "rows"}.

    The row-wise read for "who is the CEO of X": table.infobox holds one <tr> per field, th.infobox-label
    the name and td.infobox-data the value, which stacks office-holders on separate lines — the current one
    first, with "(interim)"/"(acting)" and the other posts written inline. Every matching row is returned in
    "rows", so a "Key people" answer keeps the whole list and not the first name found. The label is matched
    against the th's text, never the whole infobox: "CEO" appears in many values ("former CEO of Cooley").
    A missing row prints NO INFOBOX ROW and returns {"label": ..., "value": "", "rows": []} — an article
    whose infobox has no such field says nothing about who holds the post, so read the lead and body next.
    """
    ok = wait_js(driver, "!!document.querySelector('table.infobox')", timeout, 0.5)
    if not ok:
        print("NO INFOBOX: %s" % driver.current_url)
        return {"label": label, "value": "", "rows": []}
    found = driver.execute_script(
        """
        const re = new RegExp(arguments[0], arguments[1]);
        const out = [];
        document.querySelectorAll('table.infobox tr').forEach(tr => {
          const th = tr.querySelector('th.infobox-label, th');
          const td = tr.querySelector('td.infobox-data, td');
          const clean = s => (s || '').replace(/\\s+/g, ' ').trim();
          if (!th || !td) return;
          const name = clean(th.textContent);
          if (!re.test(name)) return;
          out.push({label: name, value: td.innerText.replace(/\\n{2,}/g, '\\n').trim()});
        });
        return out;
    """, label, "" if not (flags & re.I) else "i")
    if not found:
        print("NO INFOBOX ROW: %r (%s)" % (label, driver.current_url))
        return {"label": label, "value": "", "rows": []}
    for r in found:
        print("%s: %s" % (r["label"], r["value"]))
    return {"label": found[0]["label"], "value": found[0]["value"], "rows": found}
