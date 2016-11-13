import os
import re
import pandas as pd
from robobrowser import RoboBrowser
from blackboard.utility import *

def pull():
    br = RoboBrowser(history=True)
    site_url = 'https://portal.utoronto.ca'

    # First we log in to the UofT weblogin
    weblogin_url = 'https://weblogin.utoronto.ca/'
    br.open(weblogin_url)
    login_form = br.get_form('query')
    login_form['user'] = os.environ['UOFT_USER']
    login_form['pass'] = os.environ['UOFT_PASS']
    br.submit_form(login_form)

    # We go to Portal and click on the login square
    # and just keep following the redirects
    home_url = site_url + '/webapps/'
    relogin_url = site_url + '/webapps/login?action=relogin'
    br.open(relogin_url)
    while True:
        relay_form = br.get_form()
        if relay_form is None:
            break
        br.submit_form(relay_form)

    # We download the grades data
    grades_url = site_url + '/webapps/gradebook/do/instructor/downloadGradebook'
    grades_url += '?dispatch=viewDownloadOptions&course_id=_846126_1'
    br.open(grades_url)
    options_form = br.get_form(attrs={'name':'downloadGradebookForm'})
    br.submit_form(options_form, submit=options_form['top_Submit'])
    download_form = br.get_form('download_form')
    br.submit_form(download_form)
    grades_raw = br.parsed.string
    # grades_raw is the first piece of data we return

    # We build a dict out of the links to each group
    groups_url = site_url + '/webapps/sis-utmanagegroups-bb_bb60/admin/index.do'
    groups_url += '?course_id=_846126_1'
    br.open(groups_url)
    link_dict = {}
    n_group = 0
    tbody_tag = br.find('tbody', attrs={'id': 'listContainer_databody'})
    while True:
        tr_tag = tbody_tag.find('tr', attrs={'id': 'listContainer_row:{}'.format(n_group)})
        if tr_tag is None:
            break
        n_group += 1
        a0 = tr_tag.find('a')
        group_name = a0.text
        a1 = a0.find_next('a')
        group_link = a1.attrs['href']
        link_dict[group_name] = group_link

    # Define how to get the list of names on a group page, then do it
    ajax_dir = '/webapps/portal/execute/tabs/tabAction'
    ajax_re = re.compile("'{}', {{method: 'post', parameters: '([^']*)'".format(ajax_dir))
    def get_names(link_to_group):
        br.open(site_url + link_to_group)
        find_scripts = br.find_all('script')
        for script in find_scripts:
            ajax_match = ajax_re.search(str(script.string))
            if ajax_match is not None:
                break
        ajax_data = ajax_match.group(1)
        br.open(site_url + ajax_dir, method='post', params=ajax_data)
        span_tags = br.find_all('span')
        names = [span.text.strip() for span in span_tags]
        return names
    group_dict = {} # => return[1]
    for group, link in link_dict.items():
        idx = group.index(' ') + 1
        group_name = group[:idx] + group[idx:].zfill(2)
        group_dict[group_name] = get_names(link)

    return grades_raw, group_dict
