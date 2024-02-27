from jira import JIRA
import requests
import json
def send_slack_message(text,tkn='T1AJ'):
    webhook = "https://hooks.slack.com/services/"+tkn
    payload = {"text": text}
    return requests.post(webhook, json.dumps(payload), verify=False)

jira_connection = JIRA(
    options={'server': 'https://jira-hq.pa.local/', 'verify': False},
    token_auth='Auth')

issues = jira_connection.search_issues('(status != Verified ) ORDER BY created DESC')
issues = jira_connection.search_issues('startOfWeek(-1) ORDER BY created DESC')
msg = f"No. of bugs raised by CPT team last week - {len(issues)}"
NMI = 'NMI Bugs:\n'
Fixed = 'Fixed Bugs to verified:\n'
text = {"NMI":{}}
status = None
bugType = None
for issue in issues:
    if issue.fields.status.name.lower() == 'needsmoreinfo':
        bugType = 'NMI'
    # elif issue.fields.resolution.name.lower() == 'fixed':
    #     bugType = 'FIXED'
    reporter = issue.fields.reporter.displayName
    bugFormat = str(f'<https://jira-hq.pa.local/browse/{issue.key}|{issue.key}> - {issue.fields.summary}')
    if reporter in text[bugType].keys():
        text[bugType][reporter].append(bugFormat)
    else:
        text[bugType].update({reporter: [bugFormat]})
for bugType in text.keys():
    msg = f'*Bugs are in {bugType} State:*\n'
    for name in text[bugType].keys():
        msg = msg+" "*4+f":person_in_lotus_position: {name}\n"
        for issue in text[bugType][name]:
            msg = msg + " " * 8 + f":bug: {issue}\n"

send_slack_message(msg)
