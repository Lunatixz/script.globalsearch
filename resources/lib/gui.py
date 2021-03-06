import datetime
import json
import operator
from defs import *

def log(txt):
    if isinstance(txt,str):
        txt = txt.decode('utf-8')
    message = u'%s: %s' % (ADDONID, txt)
    xbmc.log(msg=message.encode('utf-8'), level=xbmc.LOGDEBUG)

class GUI(xbmcgui.WindowXML):
    def __init__(self, *args, **kwargs):
        self.params = kwargs['params']
        self.searchstring = kwargs['searchstring']

    def onInit(self):
        self.clearList()
        self._hide_controls()
        log('script version %s started' % ADDONVERSION)
        self.nextsearch = False
        self.searchstring = self._clean_string(self.searchstring).strip()
        if self.searchstring == '':
            self._close()
        else:
            self.window_id = xbmcgui.getCurrentWindowId()
            xbmcgui.Window(self.window_id).setProperty('GlobalSearch.SearchString', self.searchstring)
            if not self.nextsearch:
                if self.params == {}:
                    self._load_settings()
                else:
                    self._parse_argv()
            self._reset_variables()
            self._init_items()
            self._fetch_items()

    def _hide_controls(self):
        for cid in [SEARCHBUTTON, NORESULTS]:
            self.getControl(cid).setVisible(False)

    def _parse_argv(self):
        for key, value in CATEGORIES.iteritems():
            CATEGORIES[key]['enabled'] = self.params.get(value, '') == 'true'

    def _load_settings(self):
        for key, value in CATEGORIES.iteritems():
            if key not in ('albumsongs', 'artistalbums', 'tvshowseasons', 'seasonepisodes'):
                CATEGORIES[key]['enabled'] = ADDON.getSetting(key) == 'true'

    def _reset_variables(self):
        self.focusset= 'false'

    def _init_items(self):
        self.Player = MyPlayer()
        self.menu = self.getControl(MENU)
        self.content = {} 
        self.oldfocus = 0

    def _fetch_items(self):
        for key, value in sorted(CATEGORIES.items(), key=lambda x: x[1]['order']):
            if CATEGORIES[key]['enabled']:
                self._get_items(CATEGORIES[key], self.searchstring)
        self._check_focus()

    def _get_items(self, cat, search):
        if cat['content'] == 'livetv':
            self._fetch_channelgroups(cat)
            return
        if cat['type'] == 'seasonepisodes' or cat['type'] == 'albumsongs':
            search = search[0], search[1]
        self.getControl(SEARCHCATEGORY).setLabel(xbmc.getLocalizedString(cat['label']))
        self.getControl(SEARCHCATEGORY).setVisible(True)
        json_query = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"%s", "params":{"properties":%s, "sort":{"method":"%s"}, %s}, "id": 1}' % (cat['method'], json.dumps(cat['properties']), cat['sort'], cat['rule'] % (search)))
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = json.loads(json_query)
        listitems = []
        if json_response.has_key('result') and(json_response['result'] != None) and json_response['result'].has_key(cat['content']):
            for item in json_response['result'][cat['content']]:
                listitem = xbmcgui.ListItem(item['label'])
                listitem.setArt(self._get_art(item, cat['icon'], cat['media']))
                if cat['streamdetails']:
                    for stream in item['streamdetails']['video']:
                        listitem.addStreamInfo('video', stream)
                    for stream in item['streamdetails']['audio']:
                        listitem.addStreamInfo('audio', stream)
                    for stream in item['streamdetails']['subtitle']:
                        listitem.addStreamInfo('subtitle', stream)
                if cat['content'] == 'tvshows':
                    listitem.setProperty('TotalSeasons', str(item['season']))
                    listitem.setProperty('TotalEpisodes', str(item['episode']))
                    listitem.setProperty('WatchedEpisodes', str(item['watchedepisodes']))
                    listitem.setProperty('UnWatchedEpisodes', str(item['episode'] - item['watchedepisodes']))
                elif cat['content'] == 'seasons':
                    listitem.setProperty('tvshowid', str(item['tvshowid']))
                elif cat['content'] == 'movies' or cat['content'] == 'episodes' or cat['content'] == 'musicvideos':
                    listitem.setProperty('resume', str(int(item['resume']['position'])))
                elif cat['content'] == 'artists' or cat['content'] == 'albums':
                    info, props = self._split_labels(item, cat['properties'], cat['content'][0:-1] + '_')
                    for key, value in props.iteritems():
                        listitem.setProperty(key, value)
                if cat['content'] == 'movies' or cat['content'] == 'tvshows' or cat['content'] == 'episodes' or cat['content'] == 'musicvideos' or cat['content'] == 'songs':
                    listitem.setPath(item['file'])
                listitem.setInfo(cat['media'], self._get_info(item, cat['content'][0:-1]))
                listitems.append(listitem)
        if len(listitems) > 0:
            menuitem = xbmcgui.ListItem(xbmc.getLocalizedString(cat['label']))
            menuitem.setArt({'icon':cat['menuthumb']})
            menuitem.setProperty('type', cat['type'])
            menuitem.setProperty('content', cat['content'])
            self.menu.addItem(menuitem)
            self.content[cat['type']] = listitems
            if self.focusset == 'false':
                self.setContent(cat['content'])
                self.addItems(listitems)
                xbmc.sleep(100)
                self.setFocusId(self.getCurrentContainerId())
                self.focusset = 'true'

    def _fetch_channelgroups(self, cat):
        self.getControl(SEARCHCATEGORY).setLabel(xbmc.getLocalizedString(19069))
        self.getControl(SEARCHCATEGORY).setVisible(True)
        channelgrouplist = []
        json_query = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"PVR.GetChannelGroups", "params":{"channeltype":"tv"}, "id":1}')
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = json.loads(json_query)
        if(json_response.has_key('result')) and(json_response['result'] != None) and(json_response['result'].has_key('channelgroups')):
            for item in json_response['result']['channelgroups']:
                channelgrouplist.append(item['channelgroupid'])
            if channelgrouplist:
                self._fetch_channels(cat, channelgrouplist)

    def _fetch_channels(self, cat, channelgrouplist):
        # get all channel id's
        channellist = []
        for channelgroupid in channelgrouplist:
            json_query = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"PVR.GetChannels", "params":{"channelgroupid":%i, "properties":["channel", "thumbnail"]}, "id":1}' % channelgroupid)
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_response = json.loads(json_query)
            if(json_response.has_key('result')) and(json_response['result'] != None) and(json_response['result'].has_key('channels')):
                for item in json_response['result']['channels']:
                    channellist.append(item)
        if channellist:
            # remove duplicates
            channels = [dict(tuples) for tuples in set(tuple(item.items()) for item in channellist)]
            # sort
            channels.sort(key=operator.itemgetter('channelid'))
            self._fetch_livetv(cat, channels)

    def _fetch_livetv(self, cat, channels):
        listitems = []
        # get all programs for every channel id
        for channel in channels:
            channelid = channel['channelid']
            channelname = channel['label']
            channelthumb = channel['thumbnail']
            json_query = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"PVR.GetBroadcasts", "params":{"channelid":%i, "properties":["starttime", "endtime", "runtime", "genre", "plot"]}, "id":1}' % channelid)
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_response = json.loads(json_query)
            if(json_response.has_key('result')) and(json_response['result'] != None) and(json_response['result'].has_key('broadcasts')):
                for item in json_response['result']['broadcasts']:
                    broadcastname = item['label']
                    livetvmatch = re.search('.*' + self.searchstring + '.*', broadcastname, re.I)
                    if livetvmatch:
                        broadcastid = item['broadcastid']
                        duration = item['runtime']
                        genre = item['genre'][0]
                        plot = item['plot']
                        starttime = item['starttime']
                        endtime = item['endtime']
                        listitem = xbmcgui.ListItem(label=broadcastname, iconImage='DefaultFolder.png', thumbnailImage=channelthumb)
                        listitem.setProperty("icon", channelthumb)
                        listitem.setProperty("genre", genre)
                        listitem.setProperty("plot", plot)
                        listitem.setProperty("starttime", starttime)
                        listitem.setProperty("endtime", endtime)
                        listitem.setProperty("duration", str(duration))
                        listitem.setProperty("channelname", channelname)
                        listitem.setProperty("dbid", str(channelid))
                        listitems.append(listitem)
        if len(listitems) > 0:
            menuitem = xbmcgui.ListItem(xbmc.getLocalizedString(cat['label']))
            menuitem.setArt({'icon':cat['menuthumb']})
            menuitem.setProperty('type', cat['type'])
            menuitem.setProperty('content', cat['content'])
            self.menu.addItem(menuitem)
            self.content[cat['type']] = listitems
            if self.focusset == 'false':
                self.setContent(cat['content'])
                self.addItems(listitems)
                xbmc.sleep(100)
                self.setFocusId(self.getCurrentContainerId())
                self.focusset = 'true'

    def _update_list(self, item, content):
        self.clearList()
        xbmc.sleep(30)
        self.setContent(content)
        xbmc.sleep(2)
        self.addItems(self.content[item])

    def _get_info(self, labels, item):
        labels['mediatype'] = item
        labels['dbid'] = labels['%sid' % item]
        del labels['%sid' % item]
        labels['title'] = labels['label']
        del labels['label']
        if item != 'artist' and item != 'album' and item != 'song' and item != 'livetv':
            del labels['art']
        elif item == 'artist' or item == 'album' or item == 'song':
            del labels['art']
            del labels['thumbnail']
            del labels['fanart']
        else:
            del labels['thumbnail']
            del labels['fanart']
        if item == 'movie' or item == 'tvshow' or item == 'episode' or item == 'musicvideo':
            labels['duration'] = labels['runtime']
            labels['path'] = labels['file']
            del labels['file']
            del labels['runtime']
            if item != 'tvshow':
                del labels['streamdetails']
                del labels['resume']
            else:
                del labels['watchedepisodes']
        if item == 'season' or item == 'episode':
            labels['tvshowtitle'] = labels['showtitle']
            del labels['showtitle']
            if item == 'season':
                del labels['tvshowid']
                del labels['watchedepisodes']
            else:
                labels['aired'] = labels['firstaired']
                del labels['firstaired']
        if item == 'album':
            del labels['artistid']
        if item == 'song':
            labels['tracknumber'] = labels['track']
            del labels['track']
            del labels['file']
            del labels['artistid']
            del labels['albumid']
        for key, value in labels.iteritems():
            if isinstance(value, list):
                if key == 'artist' and item == 'musicvideo':
                    continue
                value = " / ".join(value)
            labels[key] = value
        return labels

    def _get_art(self, labels, icon, media):
        if media == 'video':
            art = labels['art']
            if labels.get('poster'):
                art['thumb'] = labels['poster']
            elif labels.get('banner'):
                art['thumb'] = labels['banner']
        else:
            art = labels['art']
            # needed for albums and songs
            art['thumb'] = labels['thumbnail']
            art['fanart'] = labels['fanart']
        art['icon'] = icon
        return art

    def _split_labels(self, item, labels, prefix):
        props = {}
        for label in labels:
            if label == 'thumbnail' or label == 'fanart' or label == 'art' or label == 'rating' or label == 'userrating' or label == 'file' or label == 'artistid' or label == 'albumid' or label == 'songid' or (prefix == 'album_' and (label == 'artist' or label == 'genre' or label == 'year')):
                continue
            if isinstance(item[label], list):
                item[label] = " / ".join(item[label])
            if label == 'albumlabel':
                props[prefix + 'label'] = item['albumlabel']
            else:
                props[prefix + label] = item[label]
            del item[label]
        return item, props

    def _clean_string(self, string):
        return string.replace('(', '[(]').replace(')', '[)]').replace('+', '[+]')

    def _get_allitems(self, key, listitem):
        if key == 'tvshowseasons':
            search = listitem.getVideoInfoTag().getDbId()
        elif key == 'seasonepisodes':
            tvshow = listitem.getProperty('tvshowid')
            season = listitem.getVideoInfoTag().getSeason()
            search = [tvshow, season]
        elif key == 'artistalbums':
            search = listitem.getMusicInfoTag().getDbId()
        elif key == 'albumsongs':
            artist = listitem.getMusicInfoTag().getArtist()
            album = listitem.getLabel()
            search = [artist,album]
        self._reset_variables()
        self._hide_controls()
        self.clearList()
        self.menu.reset()
        self._get_items(CATEGORIES[key], search)
        self._check_focus()

    def _get_selectaction(self):
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Settings.GetSettingValue","params":{"setting":"myvideos.selectaction"}, "id": 1}')
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = json.loads(json_query)
        action = 1
        if json_response.has_key('result') and (json_response['result'] != None) and json_response['result'].has_key('value'):
            action = json_response['result']['value']
        return action

    def _play_item(self, key, value, listitem=None):
        if key == 'file':
            xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Player.Open", "params":{"item":{"%s":"%s"}}, "id":1}' % (key, value))
        elif key == 'songid':
            xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Player.Open", "params":{"item":{"%s":%d}}, "id":1}' % (key, int(value)))
        else:
            action = self._get_selectaction()
            resume = int(listitem.getProperty('resume'))
            if action == 0:
                labels = ()
                functions = ()
                if int(resume) > 0:
                    m, s = divmod(resume, 60)
                    h, m = divmod(m, 60)
                    val = '%d:%02d:%02d' % (h, m, s)
                    labels += (LANGUAGE(32212) % val,)
                    functions += ('resume',)
                    labels += (xbmc.getLocalizedString(12021),)
                    functions += ('play',)
                else:
                    labels += (xbmc.getLocalizedString(208),)
                    functions += ('play',)
                labels += (xbmc.getLocalizedString(22081),)
                functions += ('info',)
                selection = xbmcgui.Dialog().contextmenu(labels)
                if selection >= 0:
                    if functions[selection] == 'play':
                        action = 1
                    elif functions[selection] == 'resume':
                        action = 2
                    elif functions[selection] == 'info':
                        action = 3
            if action == 3:
                self._show_info(listitem)
            elif action == 1 or action == 2:
                if action == 2:
                    self.Player.resume = resume
                xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Player.Open", "params":{"item":{"%s":%d}}, "id":1}' % (key, int(value)))

    def _check_focus(self):
        self.getControl(SEARCHCATEGORY).setVisible(False)
        self.getControl(SEARCHBUTTON).setVisible(True)
        if self.focusset == 'false':
            self.getControl(NORESULTS).setVisible(True)
            self.setFocus(self.getControl(SEARCHBUTTON))
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno(xbmc.getLocalizedString(284), LANGUAGE(32298))
            if ret:
                self._new_search()

    def _context_menu(self, controlId, listitem):
        labels = ()
        functions = ()
        media = ''
        if listitem.getVideoInfoTag():
            media = listitem.getVideoInfoTag().getMediaType()
        elif listitem.getMusicInfoTag():
            media = listitem.getMusicInfoTag().getMediaType()
        if media == 'movie':
            labels += (xbmc.getLocalizedString(13346),)
            functions += ('info',)
            path = listitem.getVideoInfoTag().getTrailer()
            if path:
                labels += (LANGUAGE(32205),)
                functions += ('play',)
        elif media == 'tvshow':
            labels += (xbmc.getLocalizedString(20351), LANGUAGE(32207), LANGUAGE(32208),)
            functions += ('info', 'tvshowseasons', 'tvshowepisodes',)
        elif media == 'episode':
            labels += (xbmc.getLocalizedString(20352),)
            functions += ('info',)
        elif media == 'musicvideo':
            labels += (xbmc.getLocalizedString(20393),)
            functions += ('info',)
        elif media == 'artist':
            labels += (xbmc.getLocalizedString(21891), LANGUAGE(32209), LANGUAGE(32210),)
            functions += ('info', 'artistalbums', 'artistsongs',)
        elif media == 'album':
            labels += (xbmc.getLocalizedString(13351),)
            functions += ('info',)
        elif media == 'song':
            labels += (xbmc.getLocalizedString(658),)
            functions += ('info',)
        if labels:
            selection = xbmcgui.Dialog().contextmenu(labels)
            if selection >= 0:
                if functions[selection] == 'info':
                    self._show_info(listitem)
                elif functions[selection] == 'play':
                    self._play_item('file', path)
                else:
                    self._get_allitems(functions[selection], listitem)

    def _show_info(self, listitem):
        xbmcgui.Dialog().info(listitem)

    def _new_search(self):
        keyboard = xbmc.Keyboard('', LANGUAGE(32101), False)
        keyboard.doModal()
        if(keyboard.isConfirmed()):
            self.searchstring = keyboard.getText()
            self.menu.reset()
            self.clearList()
            self.onInit()

    def onClick(self, controlId):
        if controlId == self.getCurrentContainerId():
            listitem = self.getListItem(self.getCurrentListPosition())
            media = ''
            if listitem.getVideoInfoTag().getMediaType():
                media = listitem.getVideoInfoTag().getMediaType()
            elif listitem.getMusicInfoTag().getMediaType():
                media = listitem.getMusicInfoTag().getMediaType()
            if media == 'movie':
                movieid = listitem.getVideoInfoTag().getDbId()
                self._play_item('movieid', movieid, listitem)
            elif media == 'tvshow':
                self._get_allitems('tvshowseasons', listitem)
            elif media == 'season':
                self._get_allitems('seasonepisodes', listitem)
            elif media == 'episode':
                episodeid = listitem.getVideoInfoTag().getDbId()
                self._play_item('episodeid', episodeid, listitem)
            elif media == 'musicvideo':
                musicvideoid = listitem.getVideoInfoTag().getDbId()
                self._play_item('musicvideoid', musicvideoid, listitem)
            elif media == 'artist':
                self._get_allitems('artistalbums', listitem)
            elif media == 'album':
                self._get_allitems('albumsongs', listitem)
            elif media == 'song':
                songid = listitem.getMusicInfoTag().getDbId()
                self._play_item('songid', songid)
        elif controlId == MENU:
            item = self.menu.getSelectedItem().getProperty('type')
            content = self.menu.getSelectedItem().getProperty('content')
            self._update_list(item, content)
        elif controlId == SEARCHBUTTON:
            self._new_search()

    def onAction(self, action):
        if action.getId() in ACTION_CANCEL_DIALOG:
            self._close()
        elif action.getId() in ACTION_CONTEXT_MENU or action.getId() in ACTION_SHOW_INFO:
            controlId = self.getFocusId()
            if controlId == self.getCurrentContainerId():
                listitem = self.getListItem(self.getCurrentListPosition())
                if action.getId() in ACTION_CONTEXT_MENU:
                    self._context_menu(controlId, listitem)
                elif action.getId() in ACTION_SHOW_INFO:
                    media = ''
                    if listitem.getVideoInfoTag().getMediaType():
                        media = listitem.getVideoInfoTag().getMediaType()
                    elif listitem.getMusicInfoTag().getMediaType():
                        media = listitem.getMusicInfoTag().getMediaType()
                    if media != '' and media != 'season':
                        self._show_info(listitem)
        elif action.getId() in (3, 4, 107) and self.getFocusId() == MENU:
            item = self.menu.getSelectedItem().getProperty('type')
            content = self.menu.getSelectedItem().getProperty('content')
            if item != self.oldfocus:
                self.oldfocus = item
                self._update_list(item, content)

    def _close(self):
        log('script stopped')
        self.close()
        xbmc.sleep(300)
        xbmcgui.Window(self.window_id).clearProperty('GlobalSearch.SearchString')


class MyPlayer(xbmc.Player):
    def __init__(self, *args, **kwargs):
        xbmc.Player.__init__(self)
        self.resume = 0

    def onPlayBackStarted(self):
        for count in range(50):
            if self.isPlayingVideo():
                break
            elif self.isPlayingAudio():
                return
            xbmc.sleep(100)
        self.seekTime(float(self.resume))
