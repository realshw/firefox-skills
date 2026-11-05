# The account the shared browser is logged in as — the DedeUserID cookie, nothing else.


def user_info(driver):
    c = driver.get_cookie('DedeUserID')
    print('USER:', c['value'] if c else 'NOT LOGGED IN')
