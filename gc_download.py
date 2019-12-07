""" Garmin Connect REST API authenticator and communicator.

Uses local credentials file creds.py with USERNAME_GC and PASSWORD_GC stored credentials

"""
#   Based on garminexport.py by petergardfall, garminconnect.py by tapiriik.
#
# Other useful references:
#   https://github.com/cpfair/tapiriik/blob/master/tapiriik/services/GarminConnect/garminconnect.py
#   https://forums.garmin.com/showthread.php?72150-connect-garmin-com-signin-question/page2
#   https://github.com/petergardfjall/garminexport

import os
from os import path
import pandas as pd
import re
import requests
from urllib.parse import urlencode
import creds

WEBHOST = "https://connect.garmin.com"
BASE_URL = "https://sso.garmin.com/sso/signin"
REDIRECT = "https://connect.garmin.com/modern/"
SSO = "https://sso.garmin.com/sso"
CSS = "https://static.garmincdn.com/com.garmin.connect/ui/css/gauth-custom-v1.2-min.css"

DATA = {
    'service': REDIRECT,
    'webhost': WEBHOST,
    'source': BASE_URL,
    'redirectAfterAccountLoginUrl': REDIRECT,
    'redirectAfterAccountCreationUrl': REDIRECT,
    'gauthHost': SSO,
    'locale': 'en_US',
    'id': 'gauth-widget',
    'cssUrl': CSS,
    'clientId': 'GarminConnect',
    'rememberMeShown': 'true',
    'rememberMeChecked': 'false',
    'createAccountShown': 'true',
    'openCreateAccount': 'false',
    'displayNameShown': 'false',
    'consumeServiceTicket': 'false',
    'initialFocus': 'true',
    'embedWidget': 'false',
    'generateExtraServiceTicket': 'true',
    'generateTwoExtraServiceTickets': 'false',
    'generateNoServiceTicket': 'false',
    'globalOptInShown': 'true',
    'globalOptInChecked': 'false',
    'mobile': 'false',
    'connectLegalTerms': 'true',
    'locationPromptShown': 'true',
    'showPassword': 'false'
}

URL_GC_LOGIN = 'https://sso.garmin.com/sso/signin?' + urlencode(DATA)
URL_GC_POST_AUTH = 'https://connect.garmin.com/modern/activities?'
URL_GC_LIST = 'https://connect.garmin.com/modern/proxy/activitylist-service/activities/search/activities?'
URL_GC_ACTIVITY_DETAILS = "https://connect.garmin.com/modern/proxy/activity-service/activity/{}/details"
URL_GC_ACTIVITY = "https://connect.garmin.com/modern/proxy/activity-service/activity/{}"

class GarminClient:
    """Log in to Garmin Connect and extract data from user account.

    Since this class implements the context manager protocol, this object
    can preferably be used together with the with-statement. This will
    automatically take care of logging in to Garmin Connect before any
    further interactions and logging out after the block completes or
    a failure occurs.

    Example of use: ::
      with GarminClient("my.sample@sample.com", "secretpassword") as client:
          ids = client.list_activity_ids()
          for activity_id in ids:
               gpx = client.get_activity_gpx(activity_id)

    """
    def __init__(self, username, password):
        """Initialize a :class:`GarminClient` instance.

        :param username: Garmin Connect user name or email address.
        :type username: str
        :param password: Garmin Connect account password.
        :type password: str

        """
        self.username = username
        self.password = password
        self.session = None

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def _build_request_session(self):
        '''
        Only ever gets called if there is no existing session - in which this request
        must be a log in.

        '''
        if not self.session:
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML,\
                         like Gecko) Chrome/54.0.2816.0 Safari/537.36'}

            headers.update({'referer': URL_GC_LOGIN})
            self.session = requests.Session()
            self.session.headers = headers

    def _post_request(self, url, payload):
        '''
        Creates a session and logs in if there is no existing session.

        '''
        data = {
            'embed': 'false',
            'rememberme': 'on'
        }
        data.update(payload)
        self._build_request_session()
        response = self.session.post(
            url=url,
            data=data)

        if not response.ok:
            response.reason = response.content
        response.raise_for_status()
        return response.text

    def login(self):
        payload = {
            'username': self.username,
            'password': self.password,
        }

        print('Requesting Login ticket...', end='')
        login_response = self._post_request(URL_GC_LOGIN+'#',payload)

        # extract the ticket from the login response
        match = re.search(r'response_url\s*=\s*"(https:[^"]+)"', login_response)
        if not match:
            raise Exception('Login failure!',
                            'Did you enter the correct username and password?')
        login_tic = match.group(1).replace("\\", "")
        print(' Done. Ticket=' + login_tic)

        print("Authenticating...", end='')
        self.session.post(
            url=URL_GC_POST_AUTH + 'ticket=' + login_tic
        )
        print(' Done.')

    def disconnect(self):
        if self.session:
            self.session.close()
            self.session = None

    def _get_session_ids(self, start=0):
        """Return a sequence of activity ids (along with their starting
        timestamps) starting at a given index, with index 0 being the user's
        most recently registered activity.

        Should the index be out of bounds or the account empty, an empty
        list is returned.

        :param start: The index of the first activity to retrieve.
        :type start: int

        :returns: A list of raw activities
        :rtype: list of dicts

        """
        limit = 100
        session_resp = self.session.get(
            url=URL_GC_LIST,
            params={'start':start,'limit':limit}
        )

        if session_resp.status_code != 200:
            raise Exception(
                u"failed to fetch activities {} to {} types: {}\n{}".format(
                    start, (start+limit-1),
                    session_resp.status_code, session_resp.text)
            )

        if session_resp.json():
            self.gc_sessions = session_resp.json()
        else:
            print('No results returned')

    def _get_session_data(self, session_id):
        details = self.session.get(URL_GC_ACTIVITY_DETAILS.format(session_id))
        summary = self.session.get(URL_GC_ACTIVITY.format(session_id))
        return summary.json(),details.json()

    def download_all(self):
        self._get_session_ids()
        count = 0
        for s in self.gc_sessions:
            session_id = s['activityId']
            try:
                if path.exists('garminsessions/'+str(session_id)):
                    continue
                else:
                    summary,details = self._get_session_data(session_id)
                    df = pd.DataFrame({'summary':summary,'details':details})
                    df.to_pickle('garminsessions/'+str(session_id))
                    print('session id:', session_id)
                    count += 1
            except Exception:
                print('FAILED id:', session_id)
                continue
        print('New files downloaded:',count,'/',len(self.gc_sessions))

with GarminClient(creds.USERNAME_GC, creds.PASSWORD_GC) as gc:
    gc.download_all()
    gc.disconnect()
