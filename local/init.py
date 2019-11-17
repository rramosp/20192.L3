endpoint  = 'https://4oowls8gyl.execute-api.us-west-2.amazonaws.com/dev/rlxmooc'
#endpoint = 'http://localhost:5000/rlxmooc'
course_id = '20192.ai4eng'
zip_file_url="https://github.com/rramosp/20192.ai4eng/archive/master.zip"

import requests, zipfile, io, os, shutil
def init():
    dirname = course_id+"-master/"
    if os.path.exists(dirname):
        shutil.rmtree(dirname)
    r = requests.get(zip_file_url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall()
    if os.path.exists("gitlocal"):
        shutil.rmtree("gitlocal")
    shutil.move(dirname+"/local", "gitlocal")
    shutil.rmtree(dirname)

def get_weblink():
    from IPython.display import HTML
    return HTML("<h3>See <a href='"+endpoint+"/web/login' target='_blank'>my courses and progress</a></h2>")
