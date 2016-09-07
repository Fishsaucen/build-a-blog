#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import jinja2
import os
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                              autoescape=True)

def get_posts(limit, offset):
    """
    queries database for BlogEntry posts and returns the list. The number of 
    posts is determined by limit. offset determines when we start adding posts.
    """
    posts = db.GqlQuery("SELECT * FROM BlogEntry ORDER BY created DESC "
                                "LIMIT {limit} OFFSET {offset}"
                                "".format(limit=limit, offset=offset))
    return  posts

class BlogEntry(db.Model):
    title = db.StringProperty(required = True)
    entry = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class MainHandler(Handler):
    def get(self):
        # dirty hack?
        self.redirect('/blog')

class BlogHandler(Handler):
    def get(self, error=""):
        page = self.request.get('page')
        self.request.get('error')
        # returns a list of most recent entries so we must select the first element
        #current_post = db.GqlQuery("SELECT * FROM BlogEntry ORDER BY created DESC " 
        #                           "LIMIT 1 ")
        #current_post = current_post[0]
        #entries = db.GqlQuery("SELECT * FROM BlogEntry ORDER BY created DESC "
        #        "LIMIT 5 OFFSET {offset}".format(offset=1))
        limit = 6
        offset = 0
        if (page):
            offset = int(page) * 5 - 5
        entries = get_posts(limit, offset)
        self.render('blog.html', current_post=entries[0], entries=entries[1:limit], error=error)

class NewPostHandler(Handler):
    def post(self):
        title = self.request.get('title')
        entry = self.request.get('entry')
        error = self.request.get('error') 

        if (not title):
            error = "Your post needs a title."
        elif (not entry):
            error = "You need to create a blog entry."

        if (error):
            self.render('newpost.html', title=title, entry=entry, error=error)
        else:
            # add the title and entry to db
            blog_post = BlogEntry(title=title, entry=entry) 
            blog_post.put()

            #FIXME need to redirect to /blog/id , where id is the post we just submitted
            #self.response.write(blog_post.name())
            self.redirect('/blog/' + str(blog_post.key().id()))

    def get(self, title="", body="", error=""):
        self.render('newpost.html', title=title, body=body, error=error)

class ViewPostHandler(Handler):
    def get(self, id):
        offset=1
        current_post = BlogEntry.get_by_id(int(id))
        entries = db.GqlQuery("SELECT * FROM BlogEntry ORDER BY created DESC "
                               "LIMIT 5 OFFSET {offset}".format(offset=offset))
        error=self.request.get('error')
        if (not current_post):
            error = "Could not find post #{}".format(id)

        self.render('blog.html', current_post=current_post, entries=entries, error=error)

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/blog', BlogHandler),
    ('/blog/newpost', NewPostHandler),
    webapp2.Route('/blog/<id:\d+>', ViewPostHandler),
], debug=True)
