# Firefox's pdf.js leaves window.PDFViewerApplication on the page, so a PDF in a tab reads as text —
# execute_async_script (getTextContent returns a Promise), poll pagesCount, join items on hasEOL or whole
# paragraphs run together. Empty text means a scan, not a bug; read_pdf(driver) raises the 20 s ceiling itself.
import os
import tempfile
import time

PDF_TEXT = os.path.join(tempfile.gettempdir(), 'pdf_text.txt')

_PDF_JS = """
const cb = arguments[arguments.length - 1];
const want = arguments[0];
(async () => {
  try {
    const app = window.PDFViewerApplication;
    const out = [];
    for (const n of want) {
      const page = await app.pdfDocument.getPage(n);
      const tc = await page.getTextContent();
      let s = '';
      for (const it of tc.items) s += it.str + (it.hasEOL ? '\\n' : ' ');
      out.push(s.trim());
    }
    let title = '';
    try { title = ((await app.pdfDocument.getMetadata()).info || {}).title || ''; } catch (e) {}
    cb({pages: out, title: title, total: app.pagesCount});
  } catch (e) { cb({error: String(e)}); }
})();
"""


def pdf_info(driver, timeout=30):
    """{pages, url} for the PDF in the current tab, or None (poll until the viewer is ready)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        d = driver.execute_script("const a = window.PDFViewerApplication;"
                                  "return a && a.pagesCount ? {pages: a.pagesCount, url: a.url || ''} : null;")
        if d:
            return d
        time.sleep(0.5)
    return None


def read_pdf(driver, pages=None, out_path=PDF_TEXT, script_timeout=300):
    """Extract the PDF's text; pages = 1-based numbers (default: all). Saves + prints a SAVED line."""
    info = pdf_info(driver)
    if not info:
        print("NO_PDF: PDFViewerApplication not found — is this tab actually a PDF?")
        return ''
    want = list(pages) if pages else list(range(1, info['pages'] + 1))
    driver.set_script_timeout(script_timeout)
    try:
        res = driver.execute_async_script(_PDF_JS, want)
    finally:
        driver.set_script_timeout(20)
    if res.get('error'):
        print("PDF_ERROR:", res['error'])
        return ''
    text = "\n\n".join("[page %d]\n%s" % (n, t) for n, t in zip(want, res['pages']))
    with open(out_path, "w") as f:
        f.write(text + "\n")
    print("SAVED:", out_path,
          "(" + str(len(want)) + "/" + str(res['total']) + " pages, " + str(len(text)) + " chars) |",
          (res.get('title') or 'untitled')[:70])
    return text


def pdf_find(driver, term, context=160, limit=10, path=PDF_TEXT):
    """Grep the saved PDF text (run read_pdf first); prints each hit with context."""
    import re
    try:
        t = open(path).read()
    except OSError:
        print("NO_TEXT: run read_pdf(driver) first")
        return 0
    hits = [m.start() for m in re.finditer(term, t, re.I)]
    for h in hits[:limit]:
        print(">>", t[max(0, h - context):h + context].replace("\n", " "))
    return len(hits)
