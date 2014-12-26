#!/usr/bin/python3
# Saves a Lorea seed a.k.a. the missing export module.
# Exit codes:
# 1 One of the configuration files not found.
# 2 Failed to log in to website.
from bs4 import BeautifulSoup as bs
from requests import get, post, Session
from re import search, findall
from pprint import pprint
import os

# ---- Step 0. Initialisation
print('---- Step 0. Initialisation')
def slurp(name):
	try:
		with open (name + '.txt', 'r') as afile:
			return afile.read().replace('\n', '')
	except:
		print('File '+name+'.txt not found.')
		print('You should create it in the same directory as this script.')
		exit(1)

website,username,password = slurp('website'),slurp('username'),slurp('password')

# TODO Use the datastructure below.
site = [{'url': website, 'groups':
         [{'title':'','link':'','sub':'','features':
           {'assemblies': [],
            'blog':       [],
            'bookmarks':  [],
            'calendar':   [],
            'decisions':  [],
            'discussion': {'entry_titles':   [],
                           'entry_links':    [],
                           'entry_firsts':   [],
                           'entry_authors':  [],
                           'entry_lasts':    [],
                           'entry_repliers': [],
                           'entry_counts':   [],
                           'entry_tags':     [],
                           'entry_contents': []},
            'files':      [],
            'pages':      [],
            'photos':     [],
            'tasks':      [],
            'videos':     [],
            'wiki':       []}}]}]

output,output_dir_name,output_file_name = [],'output','output.txt'
post_url = website + 'action/login'
s = Session()

# ---- Step 1. Get tokens from front page
print('---- Step 1. Get tokens from front page')
soup = bs(s.get(website).text)
try:
	tokens = [ x['value'] for x in soup(class_='elgg-form-login')[0].find_all('input', type='hidden') if x['value'] != 'true' ]
except:
	print("Failed to find tokens on " + website)
	exit(2)
        
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
print('---- Step 4. Open a group page and get id, discussion and task page links')
# TODO: Will have to iterate on all links, but for testing only do first:
group_link = [ x for x in group_links if 'postcapitalista' in x ][0]
soup = bs(s.get(group_link).text)
disc_url = soup.select('.elgg-menu-item-discussion')[0].a['href']
gid = disc_url.split('/')[-1] # E.g. the last word of the URL.

# https://cooperativa.ecoxarxes.cat/tasks/group/14716/all
task_url = website + 'tasks/group/' + gid + '/all'
print('task_url = ' + task_url)

# ---- Step 5. Goto groups page and get all the discussions
print('---- Step 5. Goto groups page and get all the discussions')

def read_discussions_page(soup):
	""" Take soup and return discussions from discussion page. soup => entries """
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
    # Worked with n-1.cc but not with cooperativa.ecoxarxes.cat...
	try:
		entry_authors = [ x.a.string for x in soup.select('.elgg-subtext') if 'Started' in x.contents[0].string ]
	except:
		entry_authors = [ x.contents[0].string.replace('Started by ','') for x in soup.select('.elgg-subtext') if 'Started' in x.contents[0].string ]
	entry_lasts = [ x.time['datetime'] if x.time else 'n/a' for x in soup.select('.groups-latest-reply') ]
	entry_repliers = [ x.a.string if x.a else 'n/a' for x in soup.select('.groups-latest-reply') ]
    # Worked with n-1.cc but not with cooperativa.ecoxarxes.cat...
	try:
		entry_counts = [ search(r'[0-9]+', x.find_all('a')[1].string).group() if n != 'n/a' else '0' for x,n in zip(soup.select('.elgg-subtext'), entry_lasts) ]
	except:
		entry_counts = []
	entry_tags = []
	for body in soup.select('.elgg-body'):
		if body.select('.clearfix'):
			entry_tags.append([ tag.string for tag in body.select('.elgg-tag') ])
		else:
			entry_tags.append([])
	entry_contents = [ x.string for x in soup.select('.elgg-content') ]
	return list(map(lambda tit,lin,fir,aut,las,rep,cou,tag,con:
					 {'title':tit,
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

def read_discussions(url):
	""" Take url and return discussions from discussion page. soup => entries """
	soup = bs(s.get(url).text)
	pager_links = [ x['href'] for x in soup.select('.elgg-pagination a')[:-1] ]
	entries = []
	for u in [url] + pager_links:
		print('Reading ' + u)
		entries = entries + read_discussions_page(bs(s.get(u).text))
	return entries

entries = read_discussions(disc_url)

# ---- Step 6. Goto groups page and get all the tasks
print('---- Step 6. Goto groups page and get all the tasks')

def read_task_page(soup):
	""" Take soup and return tasks from task page. soup => tasks """
	task = {'title':   "x",
			 'link':    "x",
             'author':  "x",
             'done':   "x",
             'tags':    "x",
             'content': "x"}
	task_title = soup.title.text.split(': ')[1]
	print(task_title)
	task_link = [ x.get('href').replace('?view=rss','') for x in soup.find_all('a') if x.get('title') == 'RSS feed for this page' ][0]
	try:
		task_author = [ soup.find_all('div', class_='elgg-subtext')[0].text.split(' by ')[1].split(' ')[0] ][0]
	except:
		task_author = [ soup.find_all('div', class_='elgg-subtext')[0].text.split(' to ')[1].split(' ')[0] ][0]
	# TODO harvest done status too
	task_done = 'unknown'
	task_tags = [ tag.string for tag in soup.select('.elgg-tag') ]
	if task_tags == []:
		task_tags = ['']
	task_content = 	soup.select('.elgg-output')[0].text
	return list(map(lambda title,link,author,done,tags,content:
					 {'title':title,
					  'link':link,
					  'author':author,
					  'done':done,
					  'tags':tags,
					  'content':content},
					[task_title],
					[task_link],
					[task_author],
					[task_done],
					task_tags,
					[task_content]))

def read_tasks_page(url):
	""" Take url and return tasks from a task page. url => tasks """
	tasks_links = findall('"' + website + 'tasks/view/[0-9]*/[a-z-]*"', s.get(url).text)
	# Remove duplicates
	tasks_links = list(set(tasks_links))
	# Remove doublequotes
	tasks_links = [ link.replace('"','') for link in tasks_links ]
	tasks = []
	for url in tasks_links:
		print('Reading task page ' + url)
		tasks = tasks + read_task_page(bs(s.get(url).text))
	return tasks

def read_tasks(url):
	""" Take url and return tasks from task page. url => tasks """
	soup = bs(s.get(url).text)
	pager_links = [ x['href'] for x in soup.select('.elgg-pagination a')[:-1] ]
	# TODO check if the pager really works here (works on discussion pages)
	for link in pager_links:
		print('Pager link: ' + link)
	tasks = []
	for u in [url] + pager_links:
		print('Reading tasks page ' + u)
		tasks = tasks + read_tasks_page(url)
	return tasks

tasks = read_tasks(task_url)

# ---- Step 7. Save some content
print('---- Step 7. Save some content')
def mkdir(dir_name):
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

mkdir(output_dir_name)
mkdir(os.path.join(output_dir_name, 'testgroup'))
mkdir(os.path.join(output_dir_name, 'testgroup', 'discussions'))
mkdir(os.path.join(output_dir_name, 'testgroup', 'tasks'))

def write_discussions(entries):
	filebasename = os.path.join(output_dir_name,
								'testgroup',
								'discussions',
								'discussion')
	for entry,n in zip(entries,range(len(entries))):
		lines = [ key+': '+value for key, value in entry.items() if not isinstance(value,list)]
		filename = filebasename+str(n)+'.txt'
#		print(filename)
		with open (filename, 'w') as fileio:
			for line in lines:
				print(line,file=fileio)

def write_tasks(tasks):
	filebasename = os.path.join(output_dir_name,
								'testgroup',
								'tasks',
								'task')
	for task,n in zip(tasks,range(len(tasks))):
		lines = [ key+': '+value for key, value in task.items() if not isinstance(value,list)]
		filename = filebasename+str(n)+'.txt'
		print(filename)
		with open (filename, 'w') as fileio:
			for line in lines:
				print(line,file=fileio)
				
write_discussions(entries)
write_tasks(tasks)

# Group ontology:
# 
# [ ] Group assemblies
# [ ] Group blog
# [ ] Group bookmarks
# [ ] Group calendar
# [ ] Group decisions
# [x] Group discussion
# [ ] Group files
# [ ] Group pages
# [ ] Group photos
# [x] Group tasks
# [ ] Group videos
# [ ] Group wiki

# Roadmap:
# [x] Log in
# [x] Get a sample group type
# [x] Write to a file
# [x] Write to a file tree
# ...
