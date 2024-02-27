from jira import JIRA
import requests
import json
from datetime import datetime

def send_slack_message(text,tkn='T1AJNGFP'):
    webhook = "https://hooks.slack.com/services/"+tkn
    payload = {"text": text}
    return requests.post(webhook, json.dumps(payload), verify=False)

jira_connection = JIRA(
    options={'server': 'jira-dc.pa.com/', 'verify': False},
    token_auth='auth')
issues = jira_connection.search_issues('startOfWeek(-1) ORDER BY created DESC')
msg = f"*No. of bugs raised by CPT team during (last) {datetime.today().isocalendar()[1] -1}th week - {len(issues)}*"
send_slack_message(msg)
