#!/usr/bin/env python

from bs4 import BeautifulSoup as soup
import requests
from colorama import Fore
from time import sleep

try:
    from secrets import password, ut_eid
except:
    from getpass import getpass
    ut_eid = getpass("Please enter your UT EID:")
    password = getpass("Please enter your UT Password:")

registrar_url = "https://utdirect.utexas.edu/apps/registrar/course_schedule"
fall_2015_str = "20159"

class HTTPException(Exception):
    pass

def login():
    login_url = "https://login.utexas.edu/login/UI/Login"
    session = requests.Session()
    payload = {"IDToken1": ut_eid, "IDToken2": password, "IDButton": "Log In",
               "Referer": "https://login.utexas.edu/login/cdcservlet?94283569&MajorVersion=1&&IssueInstant=2015-04-23T11%3A39%3A48Z"}
    r = session.post(login_url, data=payload)
    if r.status_code != 200:
        raise HTTPException("Got status code: " + str(r.status_code) + " when logging in.")

    return session

def request_unique_range(session, start, finish):
    assert start < finish
    url = registrar_url + "/" + fall_2015_str + "/results/?search_type_main=UNIQUE&ccyys="
    url += fall_2015_str + "&start_unique=" + str(start) + "&end_unique=" + str(finish)
    r = session.get(url)
    if r.status_code != 200:
        raise HTTPException("Got status code: " + str(r.status_code) + " when requesting unique range.")
    r = check_for_lares(r)

    results = soup(r.text).findAll("table", {"class": "results"})

    if len(results) < 1:
        return []
    elif len(results) > 1:
        raise HTTPException("Too many tables?")

    classes = []
    table = results[0]
    rows = table.findAll("tr")
    for tr in rows:
        unique = get_unique(tr)
        status = get_status(tr)
        days = get_days(tr)
        hours = get_hours(tr)
        if unique is not None:
            classes.append((unique, status, days, hours))

    sleep(0.02)
    return classes

def request_unique(session, num):
    unique = str(num)
    url = registrar_url + "/" + fall_2015_str + "/" + str(num)

    r = session.get(url)
    if r.status_code != 200:
        raise HTTPException("Got status code: " + str(r.status_code) + " when requesting unique range.")
    r = check_for_lares(r)

    results = soup(r.text).findAll("table", {"id": "details_table"})

    if len(results) < 1:
        return []
    elif len(results) > 1:
        raise HTTPException("Too many tables?")

    classes = []
    table = results[0]
    rows = table.findAll("tr")
    for tr in rows:
        unique = get_unique(tr)
        status = get_status(tr)
        days = get_days(tr)
        hours = get_hours(tr)
        if unique is not None:
            classes.append((unique, status, days, hours))

    sleep(0.02)
    return classes

def get_unique(row):
    """ Given a row in the results table, get the unique number.

    Args:
        row (tr): The BeautifulSoup row element you want to get the
            unique number of.

    Returns:
        None if the row does not have a unique number.
        The string of characters for the unique number.
    """
    unique = row.find("td", {"data-th": "Unique"})
    if unique is None:
        return None

    if unique.a is not None:
        return unique.a.text
    else:
        return unique.text

def get_days(row):
    days = row.find("td", {"data-th": "Days"})
    if days is None:
        return None

    spans = days.findAll("span")
    return [span.text for span in spans]

def get_hours(row):
    hours = row.find("td", {"data-th": "Hour"})
    if hours is None:
        return None

    spans = hours.findAll("span")
    return [span.text for span in spans]

def get_status(row):
    """ Given a row in the results table, get the unique number. """
    status = row.find("td", {"data-th": "Status"})
    if status is None:
        return None

    return status.text

def check_for_lares(r):
    """ Checks a response to see if it is the LARES redirection page.

    If it is, we redirect to the proper location and update the request
    result to be what we actually want.
    """
    r_text = r.text
    text = soup(r_text)
    if len(text.findAll("input", {"value": "Submit LARES data"})) > 0:
        text = soup(r_text)
        payload = {text.html.body.form.input['name']: text.html.body.form.input['value']}
        r = s.post(text.html.body.form['action'], data=payload)
        if r.status_code != 200:
            raise HTTPException("Got status code: " + str(r.status_code) + " posting LARES data.")
        return r
    else:
        return r

def parse_file(session, f):
    f = open(f, "r")
    data = f.readlines()
    for line in data:
        if "#" in line:
            continue
        elif "print" in line:
            print ' '.join(line.split()[1:])
        elif "check" in line:
            if "-" in line:
                num1 = int(line[6:11])
                num2 = int(line[12:].strip())
            else:
                num1 = num2 = int(line[6:11])

            if num1 == num2:
                statuses = request_unique(s, num1)
            else:
                statuses = request_unique_range(s, num1, num2)

            for status in statuses:
                print_status(status)

def print_status(status):
    color = Fore.RESET
    if "open" in status[1]:
        color = Fore.GREEN
    elif "waitlisted" in status[1]:
        color = Fore.YELLOW
    elif "closed" in status[1]:
        color = Fore.RED

    status_string = "    {0:<25}".format(str(status[1]))
    unique_string = " {0:<8}".format(str(status[0]))
    time_string = " {0:<4} {1}".format(str(status[2][0]), str(status[3][0]))
    if len(status[2]) > 1:
        time_string += "\n" + (" " * len(status_string + unique_string))
        time_string += " {0:<4} {1}".format(str(status[2][1]), str(status[3][1]))
    print color + status_string + Fore.RESET + unique_string + time_string

    #string = color + "   " + str(status[1]) + Fore.RESET
    #string += " " + status[0] + " " + status[2][0] + " " + status[3][0]
    #if len(status[2]) > 1:
    #    string += "\n     " + (" " * len(str([status[1]]))) + status[2][1] + " " + status[3][1]
    #print string

s = login()
#parse_file(s, 'schedule.txt')
parse_file(s, 'op_systems.txt')
#statuses = request_unique(s, 16450)
#statuses += request_unique_range(s, 11990, 11997)
#print set(statuses)
