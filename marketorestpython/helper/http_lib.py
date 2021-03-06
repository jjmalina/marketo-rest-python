import requests
import time
import mimetypes

class HttpLib:
    max_retries = 3
    sleep_duration = 3
    num_calls_per_second = 5 # can run five times per second at most (at 100/20 rate limit)

    def rate_limited(maxPerSecond):
        minInterval = 1.0 / float(maxPerSecond)
        def decorate(func):
            lastTimeCalled = [0.0]
            def rateLimitedFunction(*args,**kargs):
                elapsed = time.clock() - lastTimeCalled[0]
                leftToWait = minInterval - elapsed
                if leftToWait>0:
                    time.sleep(leftToWait)
                ret = func(*args,**kargs)
                lastTimeCalled[0] = time.clock()
                return ret
            return rateLimitedFunction
        return decorate

    @rate_limited(num_calls_per_second)
    def get(self, endpoint, args=None, mode=None):
        retries = 0
        while True:
            if retries > self.max_retries:
                return None
            try:
                headers = {'Accept-Encoding': 'gzip'}
                r = requests.get(endpoint, params=args, headers=headers)
                if mode is 'nojson':
                    return r
                else:
                    r_json = r.json()
                    # if we still hit the rate limiter, raise an error so the call will be retried
                    if 'success' in r_json:
                        if r_json['success'] == False:
                            print(r_json['errors'][0])
                            if r_json['errors'][0]['code'] == 606:
                                print('error 606, rate limiter')
                                raise
                    return r_json
            except Exception as e:
                print("HTTP Get Exception! Retrying.....")
                time.sleep(self.sleep_duration)
                retries += 1

    @rate_limited(num_calls_per_second)
    def post(self, endpoint, args, data=None, files=None, filename=None, mode=None):
        retries = 0
        while True:
            if retries > self.max_retries:
                return None
            try:
                if mode is 'nojsondumps':
                    r = requests.post(endpoint, params=args, data=data)
                elif files is None:
                    headers = {'Content-type': 'application/json'}
                    r = requests.post(endpoint, params=args, json=data, headers=headers)
                elif files is not None:
                    mimetype = mimetypes.guess_type(files)[0]
                    file = {filename: (files, open(files, 'rb'), mimetype)}
                    r = requests.post(endpoint, params=args, json=data, files=file)
                return r.json()
            except Exception as e:
                print("HTTP Post Exception! Retrying....."+ str(e))
                time.sleep(self.sleep_duration)
                retries += 1

    @rate_limited(num_calls_per_second)
    def delete(self, endpoint, args, data):
        retries = 0
        while True:
            if retries > self.max_retries:
                return None
            try:
                headers = {'Content-type': 'application/json'}
                r = requests.delete(endpoint, params=args, json=data, headers=headers)
                return r.json()
            except Exception as e:
                print("HTTP Delete Exception! Retrying....."+ str(e))
                time.sleep(self.sleep_duration)
                retries += 1
