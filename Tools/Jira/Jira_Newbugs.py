from jira import JIRA
import requests
import json
from pprint import pprint
from datetime import datetime

def send_slack_message(text, tkn='T1A'):
    webhook = "https://hooks.slack.com/services/"+tkn
    payload = {"text": text}
    return requests.post(webhook, json.dumps(payload), verify=False)

jira_connection = JIRA(
    options={'server': 'https://jira-dc.pa.com/', 'verify': False},
    token_auth='auth')
issues1 = jira_connection.search_issues('created >= -1h ORDER BY created DESC')
issues = jira_connection.search_issues('  ORDER BY created DESC')
if issues:
    bugs = {}
    msg = f'*New Bug Alert!!!:*\n'
    for issue in issues:
        reporter = issue.fields.reporter.displayName
        priority = issue.fields.priority.name
        version = ''
        for ver in issue.fields.versions:
            version = ver.name + ', ' + version
        summary = issue.fields.summary
        bugFormat = str(
            f'<https://jira-dc.pa.com/browse/{issue.key}|{issue.key}> - {priority} - {version} - {summary}')
        if reporter not in bugs.keys():
            bugs.update({reporter:[bugFormat]})
        else:
            bugs[reporter].append(bugFormat)
    for Name in bugs.keys():
        msg = msg+" "*4+f"{Name}:\n"
        for bug in bugs[Name]:
            msg = msg + " " * 10 + f"• {bug}\n"
        # pprint (msg)
    send_slack_message(msg)
if issues1:
    bugs = {}
    msg = f'*New Bug Alert!!!:*\n'
    for issue in issues1:
        reporter = issue.fields.reporter.displayName
        priority = issue.fields.priority.name
        version = ""
        for ver in issue.fields.versions:
            version = ver.name + ', '+version
        summary = issue.fields.summary
        bugFormat = str(
            f'<https://jira-dc.pa.com/browse/{issue.key}|{issue.key}> - {priority} - {version} - {summary}')
        if reporter not in bugs.keys():
            bugs.update({reporter:[bugFormat]})
        else:
            bugs[reporter].append(bugFormat)
    for Name in bugs.keys():
        msg = msg+" "*4+f"{Name}:\n"
        for bug in bugs[Name]:
            msg = msg + " " * 10 + f"• {bug}\n"
        # pprint (msg)
    send_slack_message(msg, tkn='T1AJ')
