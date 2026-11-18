"""Print which bilibili account the browser is logged in as."""


def bilibili_read_user_info(driver):
    """Print the DedeUserID cookie, nothing else — the account the shared browser is logged in as."""
    c = driver.get_cookie('DedeUserID')
    print('USER:', c['value'] if c else 'NOT LOGGED IN')
