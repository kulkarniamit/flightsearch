import json
import requests


class SlackIncomingWebhookAPI():
    """Slack class for constructing a slack API payload for
    incoming webhooks for a given channel
    """
    slack_bot_name = "<INSERT_BOTNAME>"
    slack_channel_name = "#<INSERT_CHANNEL_NAME>"
    slack_incoming_webhook = "<INSERT_YOUR_INCOMING_WEBHOOK_URL>"

    def __init__(self):
        pass

    def push_to_slack_channel(self, slack_data):
        slack_payload_text = "\n".join(slack_data)
        slack_payload_json = {  'username': self.slack_bot_name,
                                'text': slack_payload_text,
                                'channel': self.slack_channel_name}
        slack_payload = json.dumps(slack_payload_json)
        slack_url = self.slack_incoming_webhook
        slack_response = requests.post(slack_url, data=slack_payload)
        if slack_response.status_code != 200:
            print "Encountered an error while pushing to slack"
            exit(1)
        else:
            print "Successfully pushed to SLACK"