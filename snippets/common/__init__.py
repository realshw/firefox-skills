"""snippets.common: import a module, or its callable directly."""
# find is defined in both page_sections and read_pdf: use snippets.common.<module>.find.
from snippets.common.connect import connect
from snippets.common.page_sections import count, headings, outline, page_text, section
from snippets.common.read_pdf import pdf_info, read_pdf
from snippets.common.reattach import reattach
from snippets.common.site_tab import site_tab
from snippets.common.type_verified import composer, type_verified
from snippets.common.wait_js import as_expr, wait_js
from snippets.common.wait_stable import wait_js_stable, wait_text_stable
