from jira import JIRA
import requests
import json
def send_slack_message(text,tkn='T1A'):
    webhook = "https://hooks.slack.com/services/"+tkn
    payload = {"text": text}
    return requests.post(webhook, json.dumps(payload), verify=False)

jira_connection = JIRA(
    options={'server': 'https://jira-dc.PA.com', 'verify': False},
    token_auth='auth')

issues = jira_connection.search_issues(' status = "Needs Info") ORDER BY created DESC')
NMI = 'NMI Bugs:\n'
Fixed = 'Fixed Bugs to verified:\n'
text = {"NMI" :{}}
status = None
bugType = None
if issues:
    for issue in issues :
        if issue.fields.status.name.lower() == 'needsmoreinfo':
            bugType = 'NMI'
        # elif issue.fields.resolution.name.lower() == 'fixed':
        #     bugType = 'FIXED'
        reporter = issue.fields.reporter.displayName
        bugFormat = str(f'<https://jira-dc.pa.com/browse/{issue.key}|{issue.key}> - {issue.fields.summary}')
        if reporter in text[bugType].keys():
            text[bugType][reporter].append(bugFormat)
        else:
            text[bugType].update({reporter: [bugFormat]})
    for bugType in text.keys():
        msg = f'*Bugs are in {bugType} State:*\n'
        for name in text[bugType].keys():
            msg = msg+" "*4+f":person_in_lotus_position: {name}\n"
            for issue in text[bugType][name]:
                msg = msg + " " * 10 + f"• {issue}\n"
    send_slack_message(msg)
