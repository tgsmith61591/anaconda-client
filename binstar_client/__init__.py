
import requests, json
import base64


class BinstarError(Exception):
    pass

def jencode(payload):
    return base64.b64encode(json.dumps(payload))
    
class Binstar():
    '''
    An object that represents interfaces with the binstar.org restful API.
    
    :param token: a token generated by Binstar.authenticate or None for 
                  an anonymous user. 
    '''
    
    def __init__(self, token=None, domain='https://api.binstar.org'):
        self.session = requests.Session()
        self.token = token
        if token:
            self.session.headers.update({'Authorization': 'token %s' % (token)})
            
        self.domain = domain
    
    def authenticate(self, username, password, application, application_url=None, scopes=['package'],):
        '''
        Use basic authentication to create an authentication token using the interface below. 
        With this technique, a username and password need not be stored permanently, and the user can 
        revoke access at any time.
        
        :param username: The users name
        :param password: The users password
        :param application: The application that is requesting access
        :param application_url: The application's home page 
        :param scopes: Scopes let you specify exactly what type of access you need. Scopes limit access for the tokens.
        '''
        
        url = '%s/authentications' % (self.domain)
        payload = {"scopes": scopes, "note": application, "note_url": application_url}
        data = base64.b64encode(json.dumps(payload))
        r = self.session.post(url, auth=(username, password), data=data, verify=True)
        res = r.json()
        token = res['token']
        self.session.headers.update({'Authorization': 'token %s' % (token)})
        return token
        
    def _check_response(self, res, allowed=[200]):
        if not res.status_code in allowed:
            try:
                data = res.json()
            except:
                msg = 'Undefined error'
            else: 
                msg = data.get('error', 'Undefined error')
            raise BinstarError(msg, res.status_code)
        
    def user(self, login=None):
        '''
        Get user infomration.
        
        :param login: (optional) the login name of the user or None. If login is None
                      this method will return the information of the authenticated user.
        '''
        if login:
            url = '%s/user/%s' % (self.domain, login)
        else:
            url = '%s/user' % (self.domain)
        
        res = self.session.get(url, verify=True)
        self._check_response(res)
        
        return res.json()
    
    def user_packages(self, login=None):
        '''
        Returns a list of packages for a given user
        
        :param login: (optional) the login name of the user or None. If login is None
                      this method will return the packages for the authenticated user.

        '''
        if login:
            url = '%s/packages/%s' % (self.domain, login)
        else:
            url = '%s/packages' % (self.domain)
        
        res = self.session.get(url, verify=True)
        self._check_response(res)
        
        return res.json()
    
    def package(self, login, package_name):
        '''
        Get infomration about a specific package
        
        :param login: the login of the package owner 
        :param package_name: the name of the package
        '''
        url = '%s/package/%s/%s' % (self.domain, login, package_name)
        res = self.session.get(url, verify=True)
        self._check_response(res)
        
        return res.json()
    
    def all_packages(self, modified_after=None):
        '''
        '''
        url = '%s/package_listing' % (self.domain)
        data = {'modified_after':modified_after or ''}
        res = self.session.get(url, data=data, verify=True)
        self._check_response(res)
        return res.json()

    
    def add_package(self, login, package_name,
                    package_type,
                    summary=None,
                    license=None,
                    license_url=None,
                    public=True,
                    attrs=None,
                    host_publicly=None):
        '''
        Add a new package to a users account 
        
        :param login: the login of the package owner 
        :param package_name: the name of the package to be created
        :param package_type: A type identifyer for the package (eg. 'pypi' or 'conda', etc.)
        :param summary: A short summary about the package
        :param license: the name of the package license
        :param license_url: the url of the package license
        :param public: if true then the package will be hosted publicly
        :param attrs: A dictionary of extra attributes for this package 
        :param host_publicly: TODO: describe
        '''
        url = '%s/package/%s/%s' % (self.domain, login, package_name)
        
        attrs = attrs or {}
        attrs['summary'] = summary
        attrs['license'] = {'name':license, 'url':license_url}
        
        payload = dict(package_type=package_type,
                       public=public,
                       public_attrs=attrs or {},
                       host_publicly=host_publicly)
        
        data = jencode(payload)
        res = self.session.post(url, verify=True, data=data)
        self._check_response(res)
        return res.json()
    
    def release(self, login, package_name, version):
        '''
        Get information about a specific release
        
        :param login: the login of the package owner 
        :param package_name: the name of the package
        :param version: the name of the package
        '''
        url = '%s/release/%s/%s/%s' % (self.domain, login, package_name, version)
        res = self.session.get(url, verify=True)
        self._check_response(res)
        return res.json()
    
    def add_release(self, login, package_name, version, requirements, announce, description):
        '''
        Add a new release to a package.
        
        :param login: the login of the package owner 
        :param package_name: the name of the package 
        :param version: the version string of the release
        :param requirements: A dict of requirements TODO: describe 
        :param announce: An announcement that will be posted to all package watchers
        :param description: A long description about the package
        '''
        
        url = '%s/release/%s/%s/%s' % (self.domain, login, package_name, version)
        
        payload = {'requirements':requirements, 'announce':announce, 'description':description}
        data = jencode(payload)
        res = self.session.post(url, data=data, verify=True)
        self._check_response(res)
        return res.json()

    def download(self, login, package_name, release, basename, md5=None):
        '''
        Dowload a package distribution
        
        :param login: the login of the package owner 
        :param package_name: the name of the package 
        :param version: the version string of the release
        :param basename: the basename of the distribution to download
        :param md5: (optional) an md5 hash of the download if given and the package has not changed
                    None will be returned
        
        :returns: a file like object or None 
        '''
        
        url = '%s/download/%s/%s/%s/%s' % (self.domain, login, package_name, release, basename)
        if md5:
            headers = {'ETag':md5, }
        else:
            headers = {}
        
        res = self.session.get(url, verify=True, headers=headers, allow_redirects=False)
        self._check_response(res, allowed=[302, 304])
        
        if res.status_code == 304:
            return None
        elif res.status_code == 302:
            res2 = requests.get(res.headers['location'], stream=True, verify=True)
            return res2.raw
            
    
    def upload(self, login, package_name, release, basename, fd, description='', **attrs):
        '''
        Upload a new distribution to a package release. 
        
        :param login: the login of the package owner 
        :param package_name: the name of the package 
        :param version: the version string of the release
        :param basename: the basename of the distribution to download
        :param fd: a file like object to upload
        :param description: (optional) a short description about the file
        :param attrs: any extra attributes about the file (eg. build=1, pyversion='2.7', os='osx')

        '''
        url = '%s/stage/%s/%s/%s/%s' % (self.domain, login, package_name, release, basename)
        
        payload = dict(description=description, attrs=attrs)
        data = jencode(payload)
        res = self.session.post(url, data=data, verify=True)
        self._check_response(res)
        obj = res.json()
        
        s3url = obj['s3_url']
        s3data = obj['s3form_data']
        s3res = requests.post(s3url, data=s3data, files={'file':(basename, fd)}, verify=True)
        
        if s3res.status_code != 201:
            raise BinstarError('Error uploading to s3', s3res.status_code)
        
        url = '%s/commit/%s/%s/%s/%s' % (self.domain, login, package_name, release, basename)
        payload = dict(dist_id=obj['dist_id'])
        data = jencode(payload)
        res = self.session.post(url, data=data, verify=True)
        self._check_response(res)
        
        return res.json()
    

    
