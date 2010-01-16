# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
import re
import os.path
import random
from datetime import datetime

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
import oxlib
from oxlib import stripTags
from oxlib.normalize import canonicalTitle, canonicalName
from django.utils import simplejson as json

import utils
import managers
import fields
import load

class MovieImdb(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    imdbId = models.CharField(max_length=7, unique=True)
    title = models.CharField(max_length=1000)
    year = models.CharField(max_length=4)
    runtime = models.IntegerField(null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    tagline = models.TextField(blank=True)
    plot = models.TextField(blank=True)
    plot_outline = models.TextField(blank=True)

    rating = models.FloatField(null=True, blank=True)
    votes = models.IntegerField(null=True, blank=True)

    budget = models.IntegerField(null=True, blank=True)
    gross = models.IntegerField(null=True, blank=True)
    profit = models.IntegerField(null=True, blank=True)

    series_imdb = models.CharField(max_length=7, default='')
    series_title = models.CharField(max_length=1000, blank=True, default='')
    episode_title = models.CharField(max_length=1000, blank=True, default='')
    season = models.IntegerField(default=-1)
    episode = models.IntegerField(default=-1)
    
    def __unicode__(self):
        return u"%s (%s)" % (self.title, self.imdbId)

class MovieOxdb(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=1000)
    year = models.CharField(max_length=4)
    runtime = models.IntegerField(null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    tagline = models.TextField(blank=True)
    plot = models.TextField(blank=True)
    plot_outline = models.TextField(blank=True)

    rating = models.FloatField(null=True, blank=True)
    votes = models.IntegerField(null=True, blank=True)

    budget = models.IntegerField(null=True, blank=True)
    gross = models.IntegerField(null=True, blank=True)
    profit = models.IntegerField(null=True, blank=True)

    series_imdb = models.CharField(max_length=7, default='')
    series_title = models.TextField(blank=True, default='')
    episode_title = models.TextField(blank=True, default='')
    season = models.IntegerField(default=-1)
    episode = models.IntegerField(default=-1)

    def __unicode__(self):
        return u"%s (%s)" % (self.title, self.year)

class MovieExtra(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=1000)
    description = models.TextField(blank=True)
    contributor = models.CharField(max_length=1000)

def getMovie(info):
    '''
        info dict with:
            imdbId, title, director, episode_title, season, series
    '''
    if 'imdbId' in info:
        try:
            movie = models.Movie.byImdbId(imdbId)
        except models.Movie.DoesNotExist:
            movie = load.loadIMDb(movieId==info['imdbId'])
    else:
        q = Movie.objects.filter(title=info['title'], year=info['director'])
        if q.count() > 1:
            movie = q[0]
        else:
            movie = newMovie(info['title'], info['director'], '')
            updated = False
            for key in ('episode_title', 'season', 'year'):
                if key in info:
                    setattr(movie.oxdb, key, info[key])
                    updated = True
            if updated:
                movie.save()
    return movie

def newMovie(title, director, year):
    movie = Movie()
    oxdb = MovieOxdb()
    oxdb.save()
    movie.oxdb = oxdb
    movie.oxdb.title = title
    movie.oxdb.year = str(year)
    movie.oxdb.save()
    movie.oxdbId = "__init__%s" % random.randint(0, 100000)
    movie.save()
    movie.oxdbId = movie.oxid()
    movie.save()
    return movie

def movie_path(f, size):
    name = "%s.%s" % (size, 'ogv')
    url_hash = f.movieId
    return os.path.join('movie', url_hash[:2], url_hash[2:4], url_hash[4:6], name)

class Movie(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    published = models.DateTimeField(default=datetime.now, editable=False)

    #only movies that have metadata from files are available,
    #this is indicated by setting available to True 
    available = models.BooleanField(default=False, db_index=True)

    movieId = models.CharField(max_length=128, unique=True, blank=True)
    oxdbId = models.CharField(max_length=42, unique=True, blank=True)

    imdb = models.OneToOneField('MovieImdb', null=True, related_name='movie')
    oxdb = models.OneToOneField('MovieOxdb', null=True, related_name='movie')
    extra = models.OneToOneField('MovieOxdb', null=True, related_name='movie')

    objects = managers.MovieManager()

    def get(self, key, default=None):
        if self.extra and getattr(self.extra, key):
            return getattr(self.extra, key)
        if self.oxdb and getattr(self.oxdb, key):
            return getattr(self.oxdb, key)
        if self.imdb:
            return getattr(self.imdb, key)
        return default

    def _manual(self, qs, f='manual'):
        if qs.filter(**{f:True}).count() > 0:
            return qs.exclude(**{f:False})
        return qs.exclude(**{f:True})

    def directors(self):
        qs = self.people.filter(cast__role='directors').order_by('cast__position')
        return self._manual(qs, 'cast__manual')
    def writers(self):
        qs = self.people.filter(cast__role='writers').order_by('cast__position')
        return self._manual(qs, 'cast__manual')
    def editors(self):
        qs = self.people.filter(cast__role='editors').order_by('cast__position')
        return self._manual(qs, 'cast__manual')
    def producers(self):
        qs = self.people.filter(cast__role='producers').order_by('cast__position')
        return self._manual(qs, 'cast__manual')
    def cinematographers(self):
        qs = self.people.filter(cast__role='cinematographers').order_by('cast__position')
        return self._manual(qs, 'cast__manual')

    def cast(self):
        cast = []
        qs = Cast.objects.filter(movie=self, role='cast').order_by('position')
        qs = self._manual(qs)
        for c in qs:
            cast.append((c.person.name, c.character))
        return tuple(cast)

    def alternative_titles(self):
        return self._manual(self.alternative_titles_all)
    def genres(self):
        return self._manual(self.genres_all)
    def keywords(self):
        return self._manual(self.keywords_all)
    def countries(self):
        return self._manual(self.countries_all, 'moviecountry__manual').order_by('moviecountry__position')
    def languages(self):
        return self._manual(self.languages_all, 'movielanguage__manual').order_by('movielanguage__position')
    def trivia(self):
        return self._manual(self.trivia_all)
    def locations(self):
        return self._manual(self.locations_all)
    def connections(self):
        return self._manual(self.connections_all)

    def connections_json(self):
        connections = {}
        for connection in self.connections():
            if connection.relation not in connections:
                connections[connection.relation] = []
            connections[connection.relation].append(connection.object.movieId)
        return connections

    def reviews(self):
        q = self.reviews_all.filter(manual=True)
        if q.count() > 0:
            return q
        whitelist = ReviewWhitelist.objects.all()
        q = Q(id=-1)
        for w in whitelist:
            q = q | Q(url__contains=w.url)
        return self.reviews_all.filter(q).filter(manual=False)

    rights_level = models.IntegerField(default=-1)

    '''
    #these values get populated with imdb/oxdb values on save()
    #edits will be overwritten
    title = models.CharField(max_length=1000)
    year = models.CharField(max_length=4)
    runtime = models.IntegerField(null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    tagline = models.TextField(blank=True)
    plot = models.TextField(blank=True)
    plot_outline = models.TextField(blank=True)

    rating = models.FloatField(null=True, blank=True)
    votes = models.IntegerField(null=True, blank=True)

    budget = models.IntegerField(null=True, blank=True)
    gross = models.IntegerField(null=True, blank=True)
    profit = models.IntegerField(null=True, blank=True)

    series_imdb = models.CharField(max_length=7, default='')
    series_title = models.TextField(blank=True, default='')
    episode_title = models.TextField(blank=True, default='')
    season = models.IntegerField(default=-1)
    episode = models.IntegerField(default=-1)
    '''

    json = fields.DictField(default={}, editable=False)

    '''
    directors = fields.TupleField(default=())
    writers = fields.TupleField(default=())
    editors = fields.TupleField(default=())
    producers = fields.TupleField(default=())
    cinematographers = fields.TupleField(default=())
    cast = fields.TupleField(default=())
    alternative_titles = fields.TupleField(default=())
    genres = fields.TupleField(default=())
    keywords = fields.TupleField(default=())
    countries = fields.TupleField(default=())
    languages = fields.TupleField(default=())
    trivia = fields.TupleField(default=())
    locations = fields.TupleField(default=())
    connections = fields.DictField(default={})
    reviews = fields.TupleField(default=())
    '''

    #FIXME: use data.0xdb.org
    '''
    tpb_id = models.CharField(max_length=128, blank=True)
    kg_id = models.CharField(max_length=128, blank=True)
    open_subtitle_id = models.IntegerField(null=True, blank=True)
    wikipedia_url = models.TextField(blank=True)

    #FIXME: use data.0xdb.org/posters for that
    #what of this is still required?
    still_pos = models.IntegerField(null=True, blank=True)
    poster = models.TextField(blank=True)
    posters_disabled = models.TextField(blank=True)
    posters_available = models.TextField(blank=True)
    poster_height = models.IntegerField(null=True, blank=True)
    poster_width = models.IntegerField(null=True, blank=True)
    '''

    #stream related fields
    '''
    '''
    stream128 = models.FileField(default=None, blank=True, upload_to=lambda f, x: movie_path(f, '128'))
    stream320 = models.FileField(default=None, blank=True, upload_to=lambda f, x: movie_path(f, '320'))
    stream640 = models.FileField(default=None, blank=True, upload_to=lambda f, x: movie_path(f, '640'))
    #FIXME: is this still required? should this not be aspect ratio? depends on stream???
    scene_height = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return u'%s (%s)' % (self.get('title'), self.get('year'))

    def save(self, *args, **kwargs):
        if not self.oxdb:
            oxdb = MovieOxdb()
            oxdb.save()
            self.oxdb = oxdb
        if self.imdb:
            mid = self.imdb.imdbId
        else:
            mid = self.oxdbId
        self.movieId = mid
        
        if self.id:
            self.json = self.get_json()
        '''
        #populate auto values for faster results
        #FIXME: why is it not possible to use setattr to set List instead of db value?
        common_fields = [f.name for f in MovieImdb._meta.fields]
        only_relevant = lambda f: f not in ('id', 'created', 'modified', 'imdbId')
        common_fields = filter(only_relevant, common_fields)
        for f in common_fields:
            setattr(self, f, self.get(f))
        for f in ('directors', 'writers', 'editors',  'producers', 'cinematographers', 
                  'reviews', 'countries', 'languages',
                  'keywords', 'genres', 'trivia', 'alternative_titles'):
           value = getattr(self, 'get_' + f)
           setattr(self, f, tuple([v.json() for v in value()]))
        for f in ('cast', ):
           value = getattr(self, 'get_' + f)
           setattr(self, f, value())
        self.connections = self.connections_json()
        '''
        super(Movie, self).save(*args, **kwargs)
        self.updateFind()
        self.updateSort()

    _public_fields = {
        'movieId': 'id',
        'title':   'title',
        'year':    'year',

        'runtime':    'runtime',
        'release_date':    'release_date',

        'countries': 'country',
        'directors': 'director',
        'languages': 'language',
        'genres': 'genre',
        'keywords': 'keyword',
        'cast': 'cast',
        'series_title': 'series_title',
        'episode_title': 'episode_title',
        'season': 'season',
        'episode': 'episode',
        'reviews': 'reviews',
        'trivia': 'trivia',
        'rating': 'rating',
        'votes': 'votes',
        'alternative_titles': 'alternative_titles',
        'connections_json': 'connections'
    }
    def get_json(self, fields=None):
        movie = {}
        for key in self._public_fields:
            pub_key = self._public_fields.get(key, key)
            if not fields or pub_key in fields:
                if hasattr(self, key):
                    value = getattr(self, key)
                else:
                    value = self.get(key)
                if key in ('directors', 'writers', 'editors', 'cinematographers', 'producers',
                           'reviews', 'countries', 'languages',
                           'keywords', 'genres', 'trivia', 'alternative_titles'):
                    movie[pub_key] = tuple([v.json() for v in value()])
                elif callable(value):
                    movie[pub_key] = value()
                else:
                    movie[pub_key] = value
        if fields:
            for f in fields:
                if f.endswith('.length') and f[:-7] in ('cast', 'genre', 'trivia'):
                    movie[f] = getattr(self.sort.all()[0], f[:-7])
        return movie

    def fields(self):
        fields = {}
        for f in self._meta.fields:
            if f.name in self._public_fields:
                fields[f.name] = {}
                fields[f.name]['order'] = 'desc'
                fields[f.name]['type'] = type(f)
        return fields
    fields = classmethod(fields)

    #Class functions to get Movies by ID, right now movieId, imdbId and oxdbId
    #FIXME: this should go into a manager
    def byMovieId(self, movieId):
        if len(movieId) == 7:
            return self.byImdbId(movieId)
        return self.byOxdbId(movieId)
    byMovieId = classmethod(byMovieId)

    def byImdbId(self, imdbId):
        return self.objects.get(imdb__imdbId=imdbId)
    byImdbId = classmethod(byImdbId)

    def byOxdbId(self, oxdbId):
        return self.objects.get(oxdbId=oxdbId)
    byOxdbId = classmethod(byOxdbId)

    def oxid(self):
        directors = ','.join([d.name for d in self.directors()])
        return utils.oxid(self.get('title', ''), directors, self.get('year', ''),
                          self.get('series_title', ''), self.get('episode_title', ''),
                          self.get('season', ''), self.get('episode', ''))

    def updateFind(self):
        try:
            f = self.find
        except MovieFind.DoesNotExist:
            f = MovieFind(movie=self)

        f.title = self.get('title') + ' '.join([t.title for t in self.alternative_titles()])
        f.director = ' '.join([i.name for i in self.directors()])
        f.country = ' '.join([i.name for i in self.countries()])
        f.year = self.get('year', '')
        f.language = ' '.join([i.name for i in self.languages()])
        f.writer = ' '.join([i.name for i in self.writers()])
        f.producer = ' '.join([i.name for i in self.producers()])
        f.editor = ' '.join([i.name for i in self.editors()])
        f.cinematographer = ' '.join([i.name for i in self.cinematographers()])
        f.cast = ' '.join(['%s %s' % i for i in self.cast()])
        f.genre = ' '.join([i.name for i in self.genres()])
        f.keywords = ' '.join([i.name for i in self.keywords()])
        f.summary = self.get('plot', '') + self.get('plot_outline', '')
        f.trivia = ' '.join([i.trivia for i in self.trivia()])
        f.location = ' '.join([i.name for i in self.locations()])
        #FIXME: collate filenames
        #f.filename = self.filename
        f.all = ' '.join(filter(None, [f.title, f.director, f.country, f.year, f.language,
                          f.writer, f.producer, f.editor, f.cinematographer,
                          f.cast, f.genre, f.keywords, f.summary, f.trivia,
                          f.location, f.filename]))
        f.save()

    def updateSort(self):
        try:
            s = self.sort
        except MovieSort.DoesNotExist:
            s = MovieSort(movie=self)

        def sortName(value):
            sort_value = '~'
            if value:
                sort_value = stripTags(value).split(',')
                sort_value = '; '.join([canonicalName(name.strip()) for name in sort_value])
                sort_value = sort_value.replace(u'\xc5k', 'A')
            if not sort_value:
                sort_value = '~'
            return sort_value

        #title
        title = canonicalTitle(self.get('title'))
        title = re.sub(u'[\'!¿¡,\.;\-"\:\*\[\]]', '', title)
        title = title.replace(u'Æ', 'Ae')
        #pad numbered titles
        numbers = re.compile('^(\d+)').findall(title)
        if numbers:
            padded = '%010d' % int(numbers[0])
            title = re.sub('^(\d+)', padded, title)

        s.title = title.strip()

        directors = ','.join([i.name for i in self.directors()])
        s.director = sortName(directors)

        s.country = ','.join([i.name for i in self.countries()])
        s.year = self.get('year', '')

        names = ','.join([i.name for i in self.producers()])
        s.producer = sortName(names)
        names = ','.join([i.name for i in self.writers()])
        s.writer = sortName(names)
        names = ','.join([i.name for i in self.editors()])
        s.editor = sortName(names)
        names = ','.join([i.name for i in self.cinematographers()])
        s.cinematographer = sortName(names)

        s.language = ','.join([i.name for i in self.languages()])
        s.country = ','.join([i.name for i in self.countries()])
        s.runtime = self.get('runtime', 0)

        s.keywords = self.keywords().count()
        s.genre = self.genres().count()
        s.cast = len(self.cast())
        s.summary = len(self.get('plot', '').split())
        s.trivia = self.trivia().count()
        s.connections = self.connections().count()
        s.movieId = self.movieId
        s.rating = self.get('rating', -1)
        s.votes = self.get('votes', -1)

        # data from related subtitles
        s.scenes = 0 #FIXME
        s.words =  0 #FIXME
        s.wpm =    0 #FIXME
        s.risk =   0 #FIXME
        # data from related files
        s.duration = 0 #FIXME
        s.resolution = 0 #FIXME
        s.aspectratio = 0 #FIXME
        s.bitrate = 0 #FIXME
        s.pixels = 0 #FIXME
        s.filename = 0 #FIXME
        s.files = 0 #FIXME
        s.size = 0 #FIXME
        s.save()

class MovieFind(models.Model):
    """
        used to search movies, all search values are in here
    """
    movie = models.OneToOneField('Movie', related_name='find', primary_key=True)

    all = models.TextField(blank=True)
    title = models.TextField(blank=True)
    director = models.TextField(blank=True, default='')
    country = models.TextField(blank=True, default='')
    year = models.CharField(max_length=4)
    language = models.TextField(blank=True, default='')
    writer = models.TextField(blank=True, default='')
    producer = models.TextField(blank=True, default='')
    editor = models.TextField(blank=True, default='')
    cinematographer = models.TextField(blank=True, default='')
    cast = models.TextField(blank=True, default='')
    #person

    genre = models.TextField(blank=True)
    keywords = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    trivia = models.TextField(blank=True)
    locations = models.TextField(blank=True, default='')

    #only for own files or as admin?
    filename = models.TextField(blank=True, default='')

    _private_fields = ('id', 'movie')
    #return available find fields
    #FIXME: should return mapping name -> verbose_name
    def fields(self):
        fields = []
        for f in self._meta.fields:
            if f.name not in self._private_fields:
                name = f.verbose_name
                name = name[0].capitalize() + name[1:]
                fields.append(name)
        return tuple(fields)
    fields = classmethod(fields)

class MovieSort(models.Model):
    """
        used to sort movies, all sort values are in here
    """
    movie = models.OneToOneField('Movie', related_name='sort', primary_key=True)

    title = models.CharField(max_length=1000)
    director = models.TextField(blank=True)
    country = models.TextField(blank=True)
    year = models.CharField(max_length=4)

    producer = models.TextField(blank=True)
    writer = models.TextField(blank=True)
    editor = models.TextField(blank=True)
    cinematographer = models.TextField(blank=True)

    language = models.TextField(blank=True)
    runtime = models.IntegerField(blank=True, null=True)

    keywords = models.IntegerField(blank=True)
    genre = models.TextField(blank=True)
    cast = models.IntegerField(blank=True)
    summary = models.IntegerField(blank=True)
    trivia = models.IntegerField(blank=True)
    connections = models.IntegerField(blank=True)

    rating = models.FloatField(blank=True)
    votes = models.IntegerField(blank=True)
    scenes = models.IntegerField(blank=True)
    words = models.IntegerField(null=True, blank=True)
    wpm = models.IntegerField('Words per Minute', null=True, blank=True)
    risk = models.IntegerField(null=True, blank=True)

    movieId = models.CharField('ID', max_length=128, blank=True)

    duration = models.FloatField(default=-1)
    resolution = models.IntegerField(blank=True)
    aspectratio = models.IntegerField('Aspect Ratio', blank=True)
    bitrate = models.IntegerField(blank=True)
    pixels = models.IntegerField(blank=True)
    filename = models.IntegerField(blank=True)
    files = models.IntegerField(blank=True)
    size = models.IntegerField(blank=True)

    _private_fields = ('id', 'movie')
    #return available sort fields
    #FIXME: should return mapping name -> verbose_name
    def fields(self):
        fields = []
        for f in self._meta.fields:
            if f.name not in self._private_fields:
                name = f.verbose_name
                name = name[0].capitalize() + name[1:]
                fields.append(name)
        return tuple(fields)
    fields = classmethod(fields)

class AlternativeTitle(models.Model):
    movie = models.ForeignKey(Movie, related_name='alternative_titles_all')
    title = models.TextField()
    type = models.CharField(max_length=1000)
    manual = models.BooleanField(default=False)

    class Meta:
        ordering = ('title', )

    def __unicode__(self):
        return self.title

    def json(self):
        return (self.title, self.type)

def get_or_create(model, name):
    try:
        o = model.objects.get(name=name)
    except model.DoesNotExist:
        o = model.objects.create(name=name)
        o.save()
    return o

class Person(models.Model):
    name = models.CharField(max_length=200)
    imdbId = models.CharField(max_length=7, blank=True)
    name_sort = models.CharField(max_length=200)
    movies = models.ManyToManyField(Movie, related_name='people', through='Cast')

    class Meta:
        ordering = ('name_sort', )

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.name_sort:
            self.name_sort = oxlib.normalize.canonicalName(self.name)
        super(Person, self).save(*args, **kwargs)

    def get_or_create(model, name, imdbId=None):
        if imdbId:
            q = model.objects.filter(name=name, imdbId=imdbId)
        else:
            q = model.objects.all().filter(name=name)
        if q.count() > 0:
            o = q[0]
        else:
            o = model.objects.create(name=name)
            if imdbId:
                o.imdbId = imdbId
            o.save()
        return o
    get_or_create = classmethod(get_or_create)

    def json(self):
        return self.name

class Cast(models.Model):
    movie = models.ForeignKey(Movie, related_name='cast_relation')
    person = models.ForeignKey(Person)
    role = models.CharField(max_length=200)
    character = models.CharField(max_length=1000, blank=True)
    position = models.IntegerField()
    manual = models.BooleanField(default=False)

    class Meta:
        ordering = ('position', 'person__name_sort')

    def __unicode__(self):
        return "%s <> %s" % (self.person, self.movie)

    def link(self, movie, person, role, character, position, manual=False):
        q = self.objects.filter(movie=movie, person=person, role=role, character=character)
        if q.count() > 0:
            link = q[0]
            link.position = position
            link.manual = manual
            link.save()
        else:
            link = self()
            link.movie=movie
            link.person=person 
            link.role=role
            link.character=character
            link.position = position
            link.manual = manual
            link.save()
        return link
    link = classmethod(link)

    def json(self):
        return (self.person.json(), self.character)

class Country(models.Model):
    name = models.CharField(max_length=200, unique=True)
    movies = models.ManyToManyField(Movie, related_name='countries_all', through='MovieCountry')

    class Meta:
        #!! adding this to ordering, breaks:
        #   models.Country.objects.values("name").annotate(movies=Count('movies')) 
        #'moviecountry__position',
        ordering = ('name', )

    def __unicode__(self):
        return self.name

    get_or_create = classmethod(get_or_create)

    def json(self):
        return self.name

class MovieCountry(models.Model):
    movie = models.ForeignKey(Movie)
    country = models.ForeignKey(Country)
    position = models.IntegerField()
    manual = models.BooleanField(default=False)

    class Meta:
        ordering = ('position', 'country')

    def __unicode__(self):
        return "%s <> %s" % (self.country, self.movie)

    def link(self, movie, country, position):
        q = self.objects.filter(movie=movie, country=country)
        if q.count() > 0:
            link = q[0]
            link.position = position
            link.save()
        else:
            link = self()
            link.movie=movie
            link.country=country
            link.position=position
            link.save()
        return link
    link = classmethod(link)

class Language(models.Model):
    name = models.CharField(max_length=200, unique=True)
    movies = models.ManyToManyField(Movie, related_name='languages_all', through="MovieLanguage")

    class Meta:
        ordering = ('name', )

    def __unicode__(self):
        return self.name
    get_or_create = classmethod(get_or_create)

    def json(self):
        return self.name

class MovieLanguage(models.Model):
    movie = models.ForeignKey(Movie)
    language = models.ForeignKey(Language)
    position = models.IntegerField()
    manual = models.BooleanField(default=False)

    class Meta:
        ordering = ('position', 'language')

    def __unicode__(self):
        return self.language.name

    def link(self, movie, language, position):
        q = self.objects.filter(movie=movie, language=language)
        if q.count() > 0:
            link = q[0]
            link.position = position
            link.save()
        else:
            link = self()
            link.movie=movie
            link.language=language
            link.position=position
            link.save()
        return link
    link = classmethod(link)

class Keyword(models.Model):
    name = models.CharField(max_length=200, unique=True)
    manual = models.BooleanField(default=False)
    movies = models.ManyToManyField(Movie, related_name='keywords_all')

    class Meta:
        ordering = ('name', )

    def __unicode__(self):
        return self.name

    get_or_create = classmethod(get_or_create)

    def json(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length=200, unique=True)
    manual = models.BooleanField(default=False)
    movies = models.ManyToManyField(Movie, related_name='genres_all')

    class Meta:
        ordering = ('name', )

    def __unicode__(self):
        return self.name

    get_or_create = classmethod(get_or_create)

    def json(self):
        return self.name

class Location(models.Model):
    name = models.CharField(max_length=200, unique=True)
    manual = models.BooleanField(default=False)
    movies = models.ManyToManyField(Movie, related_name='locations_all')
    #fixme: geo data

    lat_sw = models.FloatField(default=0)
    lng_sw = models.FloatField(default=0)
    lat_ne = models.FloatField(default=0)
    lng_ne = models.FloatField(default=0)
    lat_center = models.FloatField(default=0)
    lng_center = models.FloatField(default=0)
    area = models.FloatField(default=-1)

    class Meta:
        ordering = ('name', )

    def __unicode__(self):
        return self.name

    get_or_create = classmethod(get_or_create)

    def json(self):
        return self.name

class Trivia(models.Model):
    trivia = models.TextField()
    manual = models.BooleanField(default=False)
    position = models.IntegerField()
    movie = models.ForeignKey(Movie, related_name='trivia_all')

    class Meta:
        ordering = ('position', )

    def __unicode__(self):
        return self.trivia

    def json(self):
        trivia = self.trivia
        trivia = oxlib.fixAmpersands(trivia)
        trivia = re.sub('<a name="#tr\d{7}"></a> ', '', trivia)
        trivia = re.sub('<a href="(/name/nm.*?)">(.*?)</a>', '<a href="/?f=name&amp;q=\\2">\\2</a>', trivia)
        trivia = re.sub('<a href="/title/tt(.*?)/">(.*?)</a>', '<a href="/\\1">\\2</a>', trivia)
        return trivia

class Connection(models.Model):
    subject = models.ForeignKey(Movie, related_name='connections_all')
    relation = models.CharField(max_length=512)
    object = models.ForeignKey(Movie)
    manual = models.BooleanField(default=False)

    def get_or_create(model, subject, relation, object, reverse=True, manual=False):
        q = model.objects.filter(subject=subject, relation=relation, object=object)
        if q.count() > 0:
            o = q[0]
        else:
            o = model.objects.create(subject=subject, relation=relation, object=object, manual=manual)
            o.save()
        if reverse:
            _map = {
                'Edited into': 'Edited from',
                'Features': 'Featured in',
                'Follows': 'Followed by',
                'References': 'Referenced in',
                'Remake of': 'Remade as',
                'Spin off from': 'Spin off',
                'Spoofs': 'Spoofed in',
                'Version of': 'Version of',
                'Alternate language version of': 'Alternate language version of',
            }
            if relation in _map.values():
                for k in _map:
                    if _map[k] == relation:
                        reverse_relation = k
            else:
                reverse_relation = _map[relation]
            o2 = model.get_or_create(object, reverse_relation, subject, reverse=False)
        return o
    get_or_create = classmethod(get_or_create)

    def __unicode__(self):
        return '%s %s %s' % (self.subject, self.relation, self.object)

class Review(models.Model):
    movie = models.ForeignKey('Movie', related_name='reviews_all')
    title = models.CharField(blank=True, max_length=2048)
    url = models.CharField(blank=True, max_length=2048)
    manual = models.BooleanField(default=False)

    def __unicode__(self):
        return self.title

    def get_or_create(self, movie, url):
        q = self.objects.filter(movie=movie, url=url)
        if q.count() > 0:
            o = q[0]
        else:
            o = self.objects.create(movie=movie, url=url)
            o.save()
        return o
    get_or_create = classmethod(get_or_create)

    def name(self):
        for w in ReviewWhitelist.objects.all():
            if w.url in self.url:
                return w.name
        return self.title

    def json(self):
        return (self.name(), self.url)

class ReviewWhitelist(models.Model):
    name = models.CharField(max_length=255, unique=True)
    url = models.CharField(max_length=255, unique=True)

class List(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)
    name = models.CharField(max_length=255, unique=True)
    public = models.BooleanField(default=False)
    movies = models.ManyToManyField(Movie, related_name='lists', through='ListItem')

    def add(self, movie):
        q = self.movies.filter(id=movie.id)
        if q.count() == 0:
            l = ListItem()
            l.list = self
            l.movie = movie
            l.save()

    def remove(self, movie):
        self.ListItem.objects.all().filter(movie=movie, list=self).delete()

    def __unicode__(self):
        return u'%s (%s)' % (self.title, unicode(self.user))

class ListItem(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    list = models.ForeignKey(List)
    movie = models.ForeignKey(Movie)

    def __unicode__(self):
        return u'%s in %s' % (unicode(self.movie), unicode(self.list))

def stream_path(f, size):
    name = "%s.%s" % (size, 'ogv')
    url_hash = f.oshash
    return os.path.join('stream', url_hash[:2], url_hash[2:4], url_hash[4:6], name)

def still_path(f, still):
    name = "%s.%s" % (still, 'png')
    url_hash = f.oshash
    return os.path.join('still', url_hash[:2], url_hash[2:4], url_hash[4:6], name)

FILE_TYPES = (
    (0, 'unknown'),
    (1, 'video'),
    (2, 'audio'),
    (3, 'subtitle'),
)

class File(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    published = models.DateTimeField(default=datetime.now, editable=False)

    verified = models.BooleanField(default=False)

    oshash = models.CharField(blank=True, unique=True, max_length=16)
    sha1 = models.CharField(blank=True, null=True, unique=True, max_length=40)
    md5 = models.CharField(blank=True, null=True, unique=True, max_length=32)

    movie = models.ForeignKey(Movie, related_name="files", default=None, null=True)

    type = models.IntegerField(default=0, choices=FILE_TYPES)
    info = fields.DictField(default={})
    #FIMXE: why do i need those in the db? could jsut have them in info

    path = models.CharField(blank=True, max_length=2048)
    size = models.BigIntegerField(default=-1)
    duration = models.FloatField(default=-1)
    
    video_codec = models.CharField(blank=True, max_length=256)
    pixel_format = models.CharField(blank=True, max_length=256)
    width = models.IntegerField(default=-1)
    height = models.IntegerField(default=-1)
    pixel_aspect_ratio = models.CharField(blank=True, max_length=256)
    display_aspect_ratio = models.CharField(blank=True, max_length=256)
    framerate = models.CharField(blank=True, max_length=256)

    audio_codec = models.CharField(blank=True, max_length=256)
    samplerate = models.IntegerField(default=-1)
    channels = models.IntegerField(default=-1)

    #computed values
    bpp = models.FloatField(default=-1)
    pixels = models.BigIntegerField(default=0)

    part = models.IntegerField(default=0)

    needs_data = models.BooleanField(default=True)

    #stream related fields
    available = models.BooleanField(default=False)
    stream128 = models.FileField(default=None, upload_to=lambda f, x: stream_path(f, '128'))
    stream320 = models.FileField(default=None, upload_to=lambda f, x: stream_path(f, '320'))
    stream640 = models.FileField(default=None, upload_to=lambda f, x: stream_path(f, '640'))

    timeline = models.ImageField(default=None, null=True, upload_to=lambda f, x: still_path(f, '0'))

    def save_chunk(self, chunk, name='video.ogv'):
        if not self.available:
            #FIXME: this should use stream128 or stream640 depending on configuration
            video = getattr(self, 'stream128')
            if not video:
                video.save(name, ContentFile(chunk))
                self.save()
            else:
                f = open(video.path, 'a')
                f.write(chunk)
                f.close()
            return True
        return False

    objects = managers.FileManager()

    def get_or_create(model, oshash):
        try:
            f = model.objects.get(oshash=oshash)
        except model.DoesNotExist:
            f = model.objects.create(oshash=oshash)
            f.save()
        return f
    get_or_create = classmethod(get_or_create)

    def __unicode__(self):
        return "%s (%s)" % (self.path, self.oshash)

    def update(self, data=None):
        """
            only add, do not overwrite keys in file
        """
        if data and not self.info:
            self.info = data
        _video_map = {
            'codec': 'video_codec',
        }
        if 'video' in self.info and self.info['video']:
            for key in ('codec', 'pixel_format', 'width', 'height',
                        'pixel_aspect_ratio', 'display_aspect_ratio', 'framerate'):
                if key in self.info['video'][0]:
                    setattr(self, _video_map.get(key, key), self.info['video'][0][key])
        _audio_map = {
            'codec': 'audio_codec',
        }
        if 'audio' in self.info and self.info['audio']:
            for key in ('codec', 'samplerate', 'channels'):
                if key in self.info['audio'][0]:
                    setattr(self, _audio_map.get(key, key), self.info['audio'][0][key])

        for key in ('duration', 'size', 'sha1', 'md5'):
            if key in self.info:
                setattr(self, key, self.info[key])

        #detect and assign type based on extension or detected video track
        if os.path.splitext(self.info['path'])[-1] in ('.rar', '.sub', '.idx'):
            self.type = 0
        elif 'video' in self.info:
            self.type = 1
        elif os.path.splitext(self.info['path'])[-1] in ('.mp3', '.oga'):
            self.type = 2
        elif os.path.splitext(self.info['path'])[-1] in ('.srt', ):
            self.type = 3
        #FIXME: this should be computed and not submitted path
        self.path = self.info['path']
        self.save()

    def findMovie(self):
        info = utils.parsePath(self.path)
        self.movie = getMovie(info)
        self.save()

class Still(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    file = models.ForeignKey(File, related_name="stills")
    position = models.FloatField()
    still = models.ImageField(default=None, null=True, upload_to=lambda f, x: still_path(f, '0'))

    def __unicode__(self):
        return '%s at %s' % (self.file, self.position)

class Subtitle(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)

    file = models.ForeignKey(File, related_name="subtitles")
    language = models.CharField(max_length=16)
    srt = models.TextField(blank=True)

    def get_or_create(model, user, oshash, language):
        q = model.objects.filter(file__oshash=oshash, language=language, user=user)
        if q.count() > 0:
            s = q[0]
        else:
            f = models.File.get_or_create(oshash=oshash)
            s = model.objects.create(user=user, language=language, file=f)
            s.save()
        return s
    get_or_create = classmethod(get_or_create)

    def __unicode__(self):
        return '%s.%s.srt' % (os.path.splitext(self.movie_file.path)[0], self.language)

class Layer(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)
    movie = models.ForeignKey(Movie)

    #seconds
    time_in = models.FloatField(default=-1)
    time_out = models.FloatField(default=-1)

    type = models.CharField(blank=True, max_length=255)
    value = models.TextField()

    #location = models.ForeignKey('Location', default=None)

class Archive(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255, unique=True)
    public = models.BooleanField(default=False)
    users = models.ManyToManyField(User, related_name='archives')
    
    def __unicode__(self):
        return '%s' % (self.name)

class ArchiveFile(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    archive = models.ForeignKey(Archive, related_name='files')
    file = models.ForeignKey(File)
    path = models.CharField(blank=True, max_length=2048)

    objects = managers.ArchiveFileManager()

    def update(self, data):
        """
            only add, do not overwrite keys in file
        """
        self.file.update(data)
        self.path = data.get('path', '')
        self.save()

    def get_or_create(model, archive, oshash):
        try:
            f = model.objects.by_oshash(oshash=oshash)
        except model.DoesNotExist:
            file = File.get_or_create(oshash)
            file.save()
            f = model.objects.create(archive=archive, file=file)
            f.save()
        return f
    get_or_create = classmethod(get_or_create)

    def __unicode__(self):
        return '%s (%s)' % (self.path, unicode(self.archive))


