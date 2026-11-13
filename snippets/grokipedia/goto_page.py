# grokipedia_goto_page(driver) maps spaces to underscores ("Elon Musk" -> /page/Elon_Musk) and waits on wait_stable().
# Entries run to tens of KB — use the shared sections_find(driver); company pages open with a key-value summary block.
from urllib.parse import quote
exec(open("snippets/common/site_tab.py").read())
exec(open("snippets/common/wait_stable.py").read())


def grokipedia_goto_page(driver, title, timeout=60):
    """Navigate to a Grokipedia entry and wait for the rendered text to settle."""
    url = "https://grokipedia.com/page/" + quote(
        title.strip().replace(" ", "_"), safe="_-()")
    site_tab(driver, "grokipedia.com")
    driver.get(url)
    t = wait_text_stable(driver,
                         "return document.body.innerText",
                         timeout=timeout,
                         label="grokipedia")
    print("GROKIPEDIA:", driver.title[:90], "|", driver.current_url[:90], "|",
          len(t), "chars")
    return len(t)
