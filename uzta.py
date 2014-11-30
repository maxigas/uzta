#!/usr/bin/python3
from bs4 import BeautifulSoup as bs
from requests import get, post, Session
from requests.utils import cookiejar_from_dict, dict_from_cookiejar

with open ("password.txt", "r") as password_file:
        password=password_file.read().replace('\n', '')

# Will not work without https (because login security):
url = 'https://n-1.cc/'
username = 'maxigas'
post_url = url + 'action/login'
s = Session()
soup = bs(s.get(url).text)
tokens = []
soup = soup(class_='elgg-form-login')[0]
for x in soup.find_all('input', type='hidden'):
    token = x['value']
    if token != 'true':
        tokens.append(token)

data = {
    '__elgg_token':    tokens[0],
    '__elgg_ts':       tokens[1],
    'username':        username,
    'password':        password,
    'persistent':      'true',
    'returntoreferer': 'false' 
   }

#cookies = cookiejar_from_dict(dict_from_cookiejar(s.cookies))
#print('----')
#r = s.post(post_url, data=data, cookies=cookies, allow_redirects=True)
r = s.post(post_url, data=data, allow_redirects=True)
print(r.text)
print(r.headers)
print(r.status_code)
#print(url,username,password,tokens)
#print(cookies)
print(post_url)
