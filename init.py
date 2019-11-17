course_id = '20192.L3'
github_repo = 'rramosp/%s'%course_id
zip_file_url="https://github.com/%s/archive/master.zip"%github_repo
endpoint = 'http://localhost:5000/rlxmooc'
endpoint = 'https://9kh5rvehf0.execute-api.us-west-2.amazonaws.com/dev/rlxmooc'

def get_last_modif_date(localdir):
    try:
        import time, os, pytz
        import datetime
        k = datetime.datetime.fromtimestamp(max(os.path.getmtime(root) for root,_,_ in os.walk(localdir)))
        localtz = datetime.datetime.now(datetime.timezone(datetime.timedelta(0))).astimezone().tzinfo
        k = k.astimezone(localtz)
        return k
    except Exception:
        return None
    
import requests, zipfile, io, os, shutil
def init(force_download=False):
    if force_download or not os.path.exists("local"):
        print("replicating local resources")
        dirname = course_id+"-master/"
        if os.path.exists(dirname):
            shutil.rmtree(dirname)
        r = requests.get(zip_file_url)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall()
        if os.path.exists("local"):
            shutil.rmtree("local")
        shutil.move(dirname+"/local", "local")
        shutil.rmtree(dirname)

def get_weblink():
    from IPython.display import HTML
    return HTML("<h3>See <a href='"+endpoint+"/web/login' target='_blank'>my courses and progress</a></h2>")

