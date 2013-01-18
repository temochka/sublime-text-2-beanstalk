import httplib, base64, json
from pipes import quote
import os

class HTTPUnauthorizedError(Exception):
  pass

class HTTPInternalServerError(Exception):
  pass

class HTTPClientError(Exception):
  pass

class CurlHTTP(object):
  def __init__(self, url, headers):
    self.url = url
    self.headers = headers

  def request(self, method, path, data):
    http_response = self.curl(method, path, data)
    http_headers, http_body = http_response.split("\r\n\r\n")
    headers = self.parse_headers(http_headers)

    if headers['Status'] == '500':
      raise HTTPInternalServerError

    if headers['Status'] == '401':
      raise HTTPUnauthorizedError

    return http_body

  # Skip HTTP version and parse headers to dictionary
  def parse_headers(self, http_headers):
    return dict(tuple(header.split(': '))
                for header in http_headers.splitlines()[1:])

  def curl(self, method, path, data=''):
    cmd = 'curl -i -X%s %s -d %s "https://%s%s"' % \
            (method, self.translate_headers(),
             quote(data), self.url, path)

    f = os.popen(cmd)
    output = f.read().strip()
    exit_code = f.close()

    if exit_code:
      raise HTTPClientError("Failed to execute `%s`." % (cmd))
    return output

  def translate_headers(self):
    return ' '.join(['-H "%s: %s"' % (h, v) for h, v in self.headers.items()])

class NativeHTTP(object):
  def __init__(self, url, headers):
    self.conn = httplib.HTTPSConnection(url)
    self.headers = headers

  def request(self, method, path, data):
    self.conn.request(method, path, data, self.headers)
    response = self.conn.getresponse()

    if response.status == 500:
      raise HTTPInternalServerError

    if response.status == 401:
      raise HTTPUnauthorizedError

    data = response.read()

    return data

HTTPClient = NativeHTTP

# Linux version of ST2 is compiled without SSL support, use CURL wrapper instead
if not hasattr(httplib, 'HTTPSConnection'):
  HTTPClient = CurlHTTP

class APIClient(object):
  def __init__(self, account, username, password):
    self.account = account
    self.username = username
    self.password = password
    self.http_client = HTTPClient(self.api_url(), self.headers())

  def encoded_credentials(self):
    return base64.encodestring(self.username + ':' + self.password).strip()

  def api_url(self):
    return "%s.beanstalkapp.com" % self.account

  def headers(self):
    return {
      'Accept' : 'application/json',
      'Content-Type' : 'application/json',
      'Authorization' : 'Basic ' + self.encoded_credentials()
    }

  def repositories(self):
    return self.get("/api/repositories.json")

  def environments(self, repository_id):
    return self.get("/api/%d/server_environments.json" % repository_id)

  def release(self, repository_id, environment_id, revision, comment=''):
    data = {
      'release' : {
        'comment' : comment,
        'revision' : revision
      }
    }

    return self.post("/api/%d/releases.json?environment_id=%d" % \
                     (repository_id, environment_id), data)

  def get(self, path):
    return deserialize(self.http_client.request("GET", path, ''))

  def post(self, path, data):
    return deserialize(self.http_client.request("POST", path, serialize(data)))

def deserialize(data):
  return json.loads(data)

def serialize(data):
  return json.dumps(data)