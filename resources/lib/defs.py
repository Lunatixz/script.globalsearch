import sys
import re
import xbmc
import xbmcgui

ADDON = sys.modules['__main__'].ADDON
ADDONID = sys.modules['__main__'].ADDONID
ADDONVERSION = sys.modules['__main__'].ADDONVERSION
LANGUAGE = sys.modules['__main__'].LANGUAGE
CWD = sys.modules['__main__'].CWD

ACTION_CANCEL_DIALOG = (9, 10, 92, 216, 247, 257, 275, 61467, 61448,)
ACTION_CONTEXT_MENU = (117,)
ACTION_SHOW_INFO = (11,)

SEARCHBUTTON = 990
SEARCHCATEGORY = 991
NORESULTS = 999
MENU = 9000

MOVIELABELS = ["genre", "country", "year", "top250", "setid", "rating", "userrating", "playcount", "director", "mpaa", "plot", "plotoutline", "title", "originaltitle", "sorttitle",
               "runtime", "studio", "tagline", "writer", "premiered", "set", "imdbnumber", "lastplayed", "votes", "trailer", "dateadded", "streamdetails", "art", "file", "resume"]

TVSHOWLABELS = ["genre", "year", "episode", "season", "rating", "userrating", "playcount", "mpaa", "plot", "title", "originaltitle", "sorttitle", "runtime", "studio", "premiered",
                "imdbnumber", "lastplayed", "votes", "dateadded", "art", "watchedepisodes", "file"]

SEASONLABELS = ["episode", "season", "showtitle", "tvshowid", "userrating", "watchedepisodes", "playcount", "art"]

EPISODELABELS = ["episode", "season", "rating", "userrating", "playcount", "director", "plot", "title", "originaltitle", "runtime", "writer", "showtitle", "firstaired", "lastplayed",
                 "votes", "dateadded", "streamdetails", "art", "file", "resume"]

MUSICVIDEOLABELS = ["genre", "year", "rating", "userrating", "playcount", "director", "plot", "title", "runtime", "studio", "premiered", "lastplayed", "album", "artist", "dateadded",
                    "streamdetails", "art", "file", "resume"]

ARTISTLABELS = ["genre", "description", "formed", "disbanded", "born", "yearsactive", "died", "mood", "style", "instrument", "thumbnail", "fanart", "art"]

ALBUMLABELS = ["title", "description", "albumlabel", "artist", "genre", "year", "thumbnail", "fanart", "art", "theme", "type", "mood", "style", "rating", "userrating", "artistid"]

SONGLABELS = ["title", "artist", "album", "genre", "duration", "year", "file", "thumbnail", "fanart", "comment", "art", "rating", "userrating", "track", "playcount", "artistid", "albumid"]

CATEGORIES = {
              'movies':{
                        'order':1,
                        'enabled':False,
                        'type':'movies',
                        'content':'movies',
                        'method':'VideoLibrary.GetMovies',
                        'properties':MOVIELABELS,
                        'sort':'title',
                        'rule':'"filter":{"field":"title", "operator":"contains", "value":"%s"}',
                        'streamdetails':True,
                        'label':342,
                        'icon':'DefaultVideo.png',
                        'menuthumb':'globalsearch-icon-movies.png',
                        'media':'video'
                       },
              'tvshows':{
                         'order':2,
                         'enabled':False,
                         'type':'tvshows',
                         'content':'tvshows',
                         'method':'VideoLibrary.GetTVShows',
                         'properties':TVSHOWLABELS,
                         'sort':'label',
                         'rule':'"filter":{"field":"title", "operator":"contains", "value":"%s"}',
                         'streamdetails':False,
                         'label':20343,
                         'icon':'DefaultVideo.png',
                         'menuthumb':'globalsearch-icon-tvshows.png',
                         'media':'video'
                        },
              'episodes':{
                          'order':3,
                          'enabled':False,
                          'type':'episodes',
                          'content':'episodes',
                          'method':'VideoLibrary.GetEpisodes',
                          'properties':EPISODELABELS,
                          'sort':'title',
                          'rule':'"filter":{"field":"title", "operator":"contains", "value":"%s"}',
                          'streamdetails':True,
                          'label':20360,
                          'icon':'DefaultVideo.png',
                          'menuthumb':'globalsearch-icon-episodes.png',
                          'media':'video'
                         },
              'musicvideos':{
                             'order':4,
                             'enabled':False,
                             'type':'musicvideos',
                             'content':'musicvideos',
                             'method':'VideoLibrary.GetMusicVideos',
                             'properties':MUSICVIDEOLABELS,
                             'sort':'label',
                             'rule':'"filter":{"field":"title", "operator":"contains", "value":"%s"}',
                             'streamdetails':True,
                             'label':20389,
                             'icon':'DefaultVideo.png',
                             'menuthumb':'globalsearch-icon-musicvideos.png',
                             'media':'video'
                            },
              'artists':{
                         'order':5,
                         'enabled':False,
                         'type':'artists',
                         'content':'artists',
                         'method':'AudioLibrary.GetArtists',
                         'properties':ARTISTLABELS,
                         'sort':'label',
                         'rule':'"filter":{"field": "artist", "operator": "contains", "value": "%s"}',
                         'streamdetails':False,
                         'label':133,
                         'icon':'DefaultArtist.png',
                         'menuthumb':'globalsearch-icon-artists.png',
                         'media':'music'
                        },
              'albums':{
                        'order':6,
                        'enabled':False,
                        'type':'albums',
                        'content':'albums',
                        'method':'AudioLibrary.GetAlbums',
                        'properties':ALBUMLABELS,
                        'sort':'label',
                        'rule':'"filter":{"field": "album", "operator": "contains", "value": "%s"}',
                        'streamdetails':False,
                        'label':132,
                        'icon':'DefaultAlbumCover.png',
                        'menuthumb':'globalsearch-icon-albums.png',
                        'media':'music'
                       },
              'songs':{
                       'order':7,
                       'enabled':False,
                       'type':'songs',
                       'content':'songs',
                       'method':'AudioLibrary.GetSongs',
                       'properties':SONGLABELS,
                       'sort':'title',
                       'rule':'"filter":{"field": "title", "operator": "contains", "value": "%s"}',
                       'streamdetails':False,
                       'label':134,
                       'icon':'DefaultAudio.png',
                       'menuthumb':'globalsearch-icon-songs.png',
                       'media':'music'
                      },
              'livetv':{
                     'order':9,
                     'enabled':False,
                     'type':'livetv',
                     'content':'livetv',
                     'label':19069,
                     'menuthumb':'globalsearch-icon-livetv.png'
                    },  
              'actors':{
                        'order':10,
                        'enabled':False,
                        'type':'actors',
                        'content':'movies',
                        'method':'VideoLibrary.GetMovies',
                        'properties':MOVIELABELS,
                        'sort':'title',
                        'rule':'"filter":{"field":"actor", "operator":"contains", "value":"%s"}',
                        'streamdetails':True,
                        'label':344,
                        'icon':'DefaultVideo.png',
                        'menuthumb':'globalsearch-icon-actors.png',
                        'media':'video'
                       },
              'directors':{
                           'order':11,
                           'enabled':False,
                           'type':'directors',
                           'content':'movies',
                           'method':'VideoLibrary.GetMovies',
                           'properties':MOVIELABELS,
                           'sort':'title',
                           'rule':'"filter":{"field":"director", "operator":"contains", "value":"%s"}',
                           'streamdetails':True,
                           'label':20348,
                           'icon':'DefaultVideo.png',
                           'menuthumb':'globalsearch-icon-directors.png',
                           'media':'video'
                          },
              'tvshowseasons':{
                               'order':11,
                               'enabled':False,
                               'type':'tvshowseasons',
                               'content':'seasons',
                               'method':'VideoLibrary.GetSeasons',
                               'properties':SEASONLABELS,
                               'sort':'label',
                               'rule':'"tvshowid":%s',
                               'streamdetails':False,
                               'label':20373,
                               'icon':'DefaultVideo.png',
                               'menuthumb':'globalsearch-icon-seasons.png',
                               'media':'video'
                              },
              'seasonepisodes':{
                                'order':12,
                                'enabled':False,
                                'type':'seasonepisodes',
                                'content':'episodes',
                                'method':'VideoLibrary.GetEpisodes',
                                'properties':EPISODELABELS,
                                'sort':'title',
                                'rule':'"tvshowid":%s, "season":%s',
                                'streamdetails':True,
                                'label':20360,
                                'icon':'DefaultVideo.png',
                                'menuthumb':'globalsearch-icon-episodes.png',
                                'media':'video'
                               },
              'artistalbums':{
                              'order':13,
                              'enabled':False,
                              'type':'artistalbums',
                              'content':'albums',
                              'method':'AudioLibrary.GetAlbums',
                              'properties':ALBUMLABELS,
                              'sort':'label',
                              'rule':'"filter":{"artistid":%s}',
                              'streamdetails':False,
                              'label':132,
                              'icon':'DefaultAlbumCover.png',
                              'menuthumb':'globalsearch-icon-albums.png',
                              'media':'music'
                             },
              'albumsongs':{
                             'order':14,
                             'enabled':False,
                             'type':'albumsongs',
                             'content':'songs',
                             'method':'AudioLibrary.GetSongs',
                             'properties':SONGLABELS,
                             'sort':'title',
                             'rule':'"filter":{"and":[{"field":"artist", "operator":"is", "value":"%s"}, {"field":"album", "operator":"is", "value":"%s"}]}',
                             'streamdetails':False,
                             'label':134,
                             'icon':'DefaultAudio.png',
                             'menuthumb':'globalsearch-icon-songs.png',
                             'media':'music'
                            }
             }
