#!/usr/bin/python
#*-*coding:utf-8*-*
#
#IaaSapi Paste
#

import os
import iaasapi_59 as api 
import webob
import re
import sys
from webob import Request
from webob import Response
from webob import exc
from paste.deploy import loadapp
from wsgiref.simple_server import make_server
from daemon import Daemon
import tools
from pprint import pprint

_host_ip = '192.168.0.59'

def path_check(_url):
    urlmatch = re.match(r"/iaas[a-zA-Z]+.action$", _url)
    if urlmatch:
        return _url.split('/')[-1].split('.')[0]
    else:
        return 'None'

#Filter
class LogFilter(object):
    '''用于产生工作日志
    '''
    def __init__(self, app):
        '''记录下其下游应用入口
        '''
        self.logger = tools.initlog('logs/iaasapi.log')
        self.app = app

    def __call__(self, environ, start_response):
        _str = '<%s>' % environ
        self.logger.info(_str)
        '''将控制权转交给下游
        '''
        return self.app(environ, start_response)

    @classmethod
    def factory(cls, global_conf, **kwargs):
        #print ">>>LogFilter.factory"
        return LogFilter


class IaasApi():
    def __init__(self):
        pass
    def __call__(self, environ, start_response):
#        start_response("200 OK",[("Content-type", "application/json")])
        req = Request(environ)
        pprint(environ)
        path_url = req.path_info
        service = path_check(path_url)
#        if req.method != 'POST':
#            return ["ERROR: Invaild method"]
        if service != 'None':
            _token_id, _nova_url, _keystone_adminurl, _keystone_publicurl = api.iaas_get_token(_host_ip)
            _nova_ip = _host_ip + ':8774'
            _nova_path = _nova_url[2]
            _keystone_ip = _host_ip + ':35357'
            
            if service == 'iaasCreateTenant':
                try:
                    _rsp = api.iaas_create_tenant(_keystone_ip)
                except:
                    _rsp = exc.HTTPBadRequest('Invaild params')
                    
            elif service == 'iaasReleaseTenant':
                try:
                    tenant_id = req.headers['x-wocloud-iaas-tenantid']
                    _rsp = api.iaas_release_tenant(_keystone_ip, tenant_id)
                except:
                    _rsp = exc.HTTPBadRequest('Invaild params')
            
            elif service == 'iaasCreateServer':
                try:
                    image_id, flavor_id = req.params['imageId'], req.params['flavorId']                   
                    _rsp = api.iaas_create_server(_token_id, _nova_ip, _nova_path, image_id, flavor_id)
                except:
                    _rsp = exc.HTTPBadRequest('Invaild params')
                    
            elif service == 'iaasReleaseServer':
                try:
                    server_id = req.params['serverId']
                    _rsp = api.iaas_release_server(_token_id, _nova_ip, _nova_path, server_id)
                except:
                    _rsp = exc.HTTPBadRequest('Invaild params')
                    
            elif service == 'iaasStartServer':
                try:
                    server_id = req.params['serverId']
                    _rsp = api.iaas_start_server(_token_id, _nova_ip, _nova_path, server_id)
                except:
                    _rsp = exc.HTTPBadRequest('Invaild params')
                    
            elif service == 'iaasStopServer':
                try:
                    server_id = req.params['serverId']
                    _rsp = api.iaas_stop_server(_token_id, _nova_ip, _nova_path, server_id)
                except:
                    _rsp = exc.HTTPBadRequest('Invaild params')
            
            elif service == 'iaasCheckServer':
                try:
                    server_id = req.params['serverId']
                    _rsp = api.iaas_check_server(_token_id, _nova_ip, _nova_path, server_id, 'normal')
                except:
                    _rsp = exc.HTTPBadRequest('Invaild params')
            
            elif service == 'iaasGetImages':
                    _rsp = api.iaas_get_images(_token_id, _nova_ip, _nova_path)
            
            elif service == 'iaasGetFlavors':
                    _rsp = api.iaas_get_flavors(_token_id, _nova_ip, _nova_path)
                    
            
            else:
                _rsp = exc.HTTPBadRequest('Invaild path')
                return _rsp(environ, start_response)
            _rrsp = Response()
            _rrsp.status = "200 OK"
            _rrsp.content_type = "application/json"
            _rrsp.body = _rsp
            return _rrsp(environ, start_response)
        _rsp = exc.HTTPBadRequest('Invaild path')
        return _rsp(environ, start_response)
    
    @classmethod
    def factory(cls,global_conf,**kwargs):
#        print "in IaasApi.factory", global_conf, kwargs
        return IaasApi()

class MyDaemon(Daemon):
    '''总入口
    '''

    def do(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def run(self):

        server = make_server('localhost', 8080, self.wsgi_app)
        server.serve_forever()
        pass

if __name__ == '__main__':
    configfile = "iaas-paste.ini"
    appname = "ephem"
    wsgi_app = loadapp("config:%s" % os.path.abspath(configfile), appname)
    daemon = MyDaemon('/tmp/iaaspaste.pid',
                      '/dev/null',
                      '/tmp/iaaspaste_out.log',
                      '/tmp/iaaspaste_err.log')
    
    daemon.do(wsgi_app)
    try:
        if len(sys.argv) == 2:
            if 'start' == sys.argv[1]:
                daemon.start()
            elif 'stop' == sys.argv[1]:
                daemon.stop()
            elif 'restart' == sys.argv[1]:
                daemon.restart()
            else:
                print "Unknown command"
                sys.exit(2)
            sys.exit(0)
    except:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
