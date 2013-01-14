import httplib, base64, json

class HTTPUnauthorizedError(Exception):
  pass

class HTTPInternalServerError(Exception):
  pass


class APIClient:
  def __init__(self, account, username, password):
    self.account = account
    self.username = username
    self.password = password
    self.conn = httplib.HTTPSConnection(self.api_url())

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
    return self.request("GET", path, None, self.headers())

  def post(self, path, data):
    return self.request("POST", path, serialize(data), self.headers())

  def request(self, method, path, data, headers):
    self.conn.request(method, path, data, headers)
    response = self.conn.getresponse()

    if response.status == 500:
      raise HTTPInternalServerError

    if response.status == 401:
      raise HTTPUnauthorizedError

    data = response.read()
    
    return deserialize(data)

def deserialize(data):
  return json.loads(data)

def serialize(data):
  return json.dumps(data)