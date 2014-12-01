#!/usr/bin/python3
# Saves a Lorea seed a.k.a. the missing export module.
from bs4 import BeautifulSoup as bs
from requests import get, post, Session
from re import search
import os

def slurp(name):
        with open (name + '.txt', 'r') as afile:
                return afile.read().replace('\n', '')

website,username,password = slurp('website'),slurp('username'),slurp('password')
output,output_dir_name,output_file_name = [],'output','output.txt'
post_url = website + 'action/login'
s = Session()

# ---- Step 1. Get tokens from front page
print('---- Step 1. Get tokens from front page')
soup = bs(s.get(website).text)
try:
        tokens = [ x['value'] for x in soup(class_='elgg-form-login')[0].find_all('input', type='hidden') if x['value'] != 'true' ]
except:
        print("Failed to log in to " + website)
        exit(1)
        
data = {
    '__elgg_token':    tokens[0],
    '__elgg_ts':       tokens[1],
    'username':        username,
    'password':        password,
    'persistent':      'true',
    'returntoreferer': 'false' 
   }

# ---- Step 2. Log in
print('---- Step 2. Log in')
r = s.post(post_url, data=data, allow_redirects=True)

# ---- Step 3. Goto groups page and get group list
print('---- Step 3. Goto groups page and get group list')
soup = bs(s.get(website + 'groups/member/' + username + '/').text)
groupsoup = soup(class_='elgg-list')[0]
grouplinksoup =    [ x.find_all('a') for x in groupsoup.find_all('h3') ]
group_titles =     [ x[0].get_text() for x in grouplinksoup ]
group_links =      [ x[0]['href'] for x in grouplinksoup ]
group_subs =  [ x.get_text() for x in soup(class_='elgg-subtext') ]
groups = list(map(lambda t,l,s: {'title':t,'link':l,'sub':s},
                  group_titles,group_subs,group_links))
# Example: groups → [{'title': 'Fuck Corp$urfing - FCS', 'sub': 'https://n-1.cc/g/fuck_corpsurfing_fcs', 'link': "Hack CS, don't use it! - Hackea CS, no lo uses!"}, {'title': 'LelaCoders', 'sub': 'https://n-1.cc/g/donestech+lelacoders', 'link': 'Subgroup of DonesTech'}, {'title': 'bughunting', 'sub': 'https://n-1.cc/g/bughunting', 'link': 'yo programo, tu programas, ellx hackea'}, {'title': 'B27 discussion group', 'sub': 'https://n-1.cc/g/colectivo_b27_discussion_group', 'link': 'bug = software error'}, {'title': 'Fuck FaceFuck - FFF', 'sub': 'https://n-1.cc/g/fuck-facefuck---fff', 'link': ''}, {'title': 'Help', 'sub': 'https://n-1.cc/g/help', 'link': "Hack FB, don't use it! - Hackea facebook! No lo uses!"}, {'title': 'HackTheNight', 'sub': 'https://n-1.cc/g/hackthenight', 'link': 'helping to start in Lorea'}, {'title': 'HackLabs', 'sub': 'https://n-1.cc/g/hacklabs', 'link': 'hackspace @ cso la otra carboneria'}]

# data structure:
# dictionaries of dictionaries of dictionaries of dictionaries of dictionaries
# ['groups' ['mygroup': ['discussions': ['1895355': ['title': "foo",
#                              'author': "foo",
#                              'timestamp': "foo",
#                              'replies': "foo",
#                              'lastreply': "foo",
#                              'content': "foo"]]]]]

# https://n-1.cc/discussion/view/1895355/club-informatico-de-la-base

# ---- Step 4. Open a group page and get id and discussion page link
print('---- Step 4. Open a group page and get id and discussion page link')
# TODO: Will have to iterate on all links, but for testing only do first:
group_link = [ x for x in group_links if 'hackthenight' in x ][0]
soup = bs(s.get(group_link).text)
disc_url = soup.select('.elgg-menu-item-discussion')[0].a['href']
gid = disc_url.split('/')[-1] # E.g. the last word of the URL.

# ---- Step 5. Goto groups page and get all the discussions
print('---- Step 5. Goto groups page and get all the discussions')
soup = bs(s.get(disc_url).text)
entry = {'title':   "x",
         'link':    "x",
         'first':   "x",
         'author':  "x",
         'last':    "x",
         'replier': "x",
         'count':   "x",
         'tags':    "x",
         'content': "x"}
entry_titles = [ x.string for x in soup.select('h3 a') ]
entry_links = [ x['href'] for x in soup.select('h3 a') ]
entry_firsts = [ x.time['datetime'] for x in soup.select('.elgg-subtext') if x.time]
entry_authors = [ x.a.string for x in soup.select('.elgg-subtext') if 'Started' in x.contents[0].string ]
entry_lasts = [ x.time['datetime'] if x.time else 'n/a' for x in soup.select('.groups-latest-reply') ]
entry_repliers = [ x.a.string if x.a else 'n/a' for x in soup.select('.groups-latest-reply') ]
entry_counts = [ search(r'[0-9]+', x.find_all('a')[1].string).group() if n != 'n/a' else '0' for x,n in zip(soup.select('.elgg-subtext'), entry_lasts) ]
entry_tags = []
for body in soup.select('.elgg-body'):
        if body.select('.clearfix'):
                entry_tags.append([ tag.string for tag in body.select('.elgg-tag') ])
        else:
                entry_tags.append([])
entry_contents = [ x.string for x in soup.select('.elgg-content') ]
entries = list(map(lambda tit,lin,fir,aut,las,rep,cou,tag,con: {'title':tit,
                                                     'link':lin,
                                                     'first':fir,
                                                     'author':aut,
                                                     'last':las,
                                                     'replier':rep,
                                                     'count':cou,
                                                     'tags':tag,
                                                     'content':con},
                 entry_titles,
                 entry_links,
                 entry_firsts,
                 entry_authors,
                 entry_lasts,
                 entry_repliers,
                 entry_counts,
                 entry_tags,
                 entry_contents))
print(entries[0])
# TODO Pager!!!

# ---- Step 6. Save some content
def mkdir(dir_name):
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

mkdir(output_dir_name)
mkdir(os.path.join(output_dir_name, 'testgroup'))
mkdir(os.path.join(output_dir_name, 'testgroup', 'discussion'))
filebasename = os.path.join(output_dir_name, 'testgroup', 'discussion', 'discussion')

for entry,n in zip(entries,range(len(entries))):
        lines = [ key+': '+value for key, value in entry.items() if not isinstance(value,list)]
        filename = filebasename+str(n)+'.txt'
        print(filename)
        with open (filename, 'w') as fileio:
                for line in lines:
                        print(line,file=fileio)

                        
# Group ontology:
# 
# [ ] Group assemblies
# [ ] Group blog
# [ ] Group bookmarks
# [ ] Group calendar
# [ ] Group decisions
# [~] Group discussion
# [ ] Group files
# [ ] Group pages
# [ ] Group photos
# [ ] Group tasks
# [ ] Group videos
# [ ] Group wiki

# Roadmap:
# [x] Log in
# [ ] Get a sample group type
# [ ] Write to a file
# [ ] Write to a file tree
# ...
