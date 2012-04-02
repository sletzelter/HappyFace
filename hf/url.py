
import hf, os

def staticUrl(file):
    return join(hf.config.get("paths", "static_url"), file)

def join(url, suffix):
    if len(suffix) == 0:
        return url
    if len(url) == 0:
        return suffix
    if url[-1] != "/" and suffix[0] != "/":
        url = url+"/"
    elif url[-1] == "/" and suffix[0] == "/":
        url = url[0:-1]
    return url+suffix

def absoluteUrl(arg):
    """
    Decorator!
    Take an URL that is relative to the root URL
    of happyface and make it absolute respective to
    that root URL
    """
    def joinCfg(*args, **kwargs):
        return join(hf.config.get("paths", "happyface_url"), arg(*args, **kwargs))
    if isinstance(arg, str):
        return join(hf.config.get("paths", "happyface_url"), arg)
    return joinCfg
