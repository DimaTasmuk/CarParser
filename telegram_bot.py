import requests
import datetime

from car_parser.credentials import BOT_TOKEN, SCRAPY_API_KEY, SCRAPY_PROJECT_ID


class TelegramBot(object):

    def __init__(self, token):
        self.url = "https://api.telegram.org/bot{0}/".format(token)
        super(TelegramBot, self).__init__()

    def get_updates_json(self):
        response = requests.get(url=self.url + 'getUpdates')
        return response.json()

    def get_last_update(self):
        data = self.get_updates_json()
        results = data['result']
        last_updates = len(results) - 1
        return results[last_updates]

    def get_chat_id(self):
        last_update = self.get_last_update()
        chat_id = last_update['message']['chat']['id']
        return chat_id

    def get_last_message(self):
        update = self.get_last_update()
        message = update['message']['text']
        return message

    def send_message(self, text):
        chat_id = self.get_chat_id()
        params = {
            'chat_id': chat_id,
            'text': text,
            'disable_web_page_preview': True
        }
        response = requests.post(url=self.url + 'sendMessage', data=params)
        return response


class ScrapyProject(object):

    def __init__(self, api_key, project_id):
        self.api_key = api_key
        self.project_id = project_id
        super(ScrapyProject, self).__init__()

    def get_jobs(self):
        url = "https://app.scrapinghub.com/api/jobs/list.json?apikey={0}&project={1}".format(self.api_key,
                                                                                             self.project_id)
        response = requests.get(url=url)
        return response.json().get('jobs')

    def get_jobs_by_state(self, state):
        jobs = self.get_jobs()
        filtered_jobs = filter(lambda job: job.get("state") == state, jobs)
        return filtered_jobs

    def get_errors(self, job):
        errors_count = job.get('errors_count')
        if errors_count:
            logs = requests.get("https://storage.scrapinghub.com/logs/{}?apikey={}&format=json"
                                .format(job.get('id'), self.api_key)).json()
            errors = filter(lambda log: log.get('level') == 40, logs)
            return errors
        return None

    def check_errors(self, errors):
        error_messages = list()
        if errors:
            for error in errors:
                error_time = datetime.datetime.utcfromtimestamp(error.get('time') / 1000)  # time in milliseconds
                is_new_error = error_time + datetime.timedelta(minutes=1) >= datetime.datetime.utcnow()
                if is_new_error:
                    error_messages.append("{}\n{}".format(error_time, error.get('message')))
        return error_messages


scrapy_project = ScrapyProject(SCRAPY_API_KEY, SCRAPY_PROJECT_ID)
telegram_bot = TelegramBot(BOT_TOKEN)

for job in scrapy_project.get_jobs_by_state("running"):
    errors = scrapy_project.get_errors(job)
    error_messages = scrapy_project.check_errors(errors)
    if len(error_messages) > 0:
        for error in error_messages:
            telegram_bot.send_message(error)
