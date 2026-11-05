# Screenshot, and probe the page for likely chat inputs
import os
import tempfile


def probe_input(driver):
    driver.save_screenshot(
        os.path.join(tempfile.gettempdir(), "probe_inputs.png"))
    print("SHOT_SAVED")
    els = driver.find_elements("css selector",
                               "textarea, [contenteditable='true'], input")
    for i, el in enumerate(els):
        try:
            print(i, "|", el.tag_name, "|", (el.get_attribute("placeholder")
                                             or "")[:60], "| shown:",
                  el.is_displayed())
        except Exception as e:
            print(i, "ERR", e)
    print("DONE")
