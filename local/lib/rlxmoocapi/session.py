import requests, json, getpass, inspect, pickle, codecs
from time import time, sleep
from IPython.core.display import display, HTML
import inspect


mf_tlastcall = None
def maxfreq(maxlapse=5):
    """
    ensures function calls are at least 'maxlapse' seconds apart
    forces sleep until 'maxlapse' happens
    """
    def wrapper(func):
        def function_wrapper(*args, **kwargs):
            global mf_tlastcall

            if mf_tlastcall is not None:
                t = time()-mf_tlastcall
                if t<maxlapse:
                    sleep(maxlapse-t)

            mf_tlastcall = time()
            return func(*args, **kwargs)

        return function_wrapper
    return wrapper

class Session:
    
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.token    = None

    @maxfreq()
    def do(self, request_function, url, data=None, loggedin_required=True):
        assert not loggedin_required or self.token is not None, "must login first"
        resp = request_function(self.endpoint+"/api/"+url, json=data, 
                             headers={'Content-Type':'application/json',
                                      'Mooc-Token': self.token})

        if resp.status_code!=200:
            c = eval(resp.content)
            if "traceback" in c:
                traceback = c["traceback"]
                e = ValueError(c["error"]+"\n\ntraceback:\n"+traceback)
                raise e
            else:
                msg = "\n--\n".join([str(i) for i in [resp.content, resp.headers, resp.text, resp.reason]])
                raise ValueError(msg)
        return resp

    def do_post(self, url, data=None, loggedin_required=True):
        return self.do(requests.post, url, data, loggedin_required)

    def do_get(self, url, data=None, loggedin_required=True):
        return self.do(requests.get, url, data, loggedin_required)    

    def do_put(self, url, data=None, loggedin_required=True):
        return self.do(requests.put, url, data, loggedin_required)        
    
    def do_delete(self, url, data=None, loggedin_required=True):
        return self.do(requests.delete, url, data, loggedin_required)        
    
    def do_head(self, url, data=None, loggedin_required=True):
            return self.do(requests.head, url, data, loggedin_required)        

    def login(self, user_id=None, pwd=None, course_id=None, session_id=None, lab_id=None):
        if user_id is None:
            user_id = input("username: ")
        if pwd is None:
            pwd = getpass.getpass("password: ")

        data = {"user_id": user_id, "user_pwd": pwd}
        resp = self.do_post("login", data, loggedin_required=False)
        self.token = eval(resp.content)["Mooc-Token"]
        self.user_id = user_id

        if course_id is not None and session_id is not None:
            self.course_session = self.get_course_session(course_id, session_id)
        self.course_id = course_id
        self.session_id = session_id
        self.lab_id = lab_id

        return self
        
    def create_user(self, user_id, pwd, user_name, user_email):
        data = {"user_id": user_id, "user_name": user_name, "user_pwd": pwd, "user_email": user_email}
        self.do_post("users", data)

    def get_user(self, user_id):
        resp = self.do_get("users/%s"%user_id)
        if resp.status_code==200:
            return eval(resp.content.decode())

    def pwd_change(self, user_id=None):
        user_id = user_id if user_id is not None else self.user_id
        resp = self.do_get("users/%s/request_pwd_change"%user_id)
        print ("check your email for password change code\n\n")
        code = input("password change code: ")
        old_pwd =  getpass.getpass("old password:         ")
        new_pwd1 = getpass.getpass("new password:         ")
        new_pwd2 = getpass.getpass("new password (again): ")

        if new_pwd1!=new_pwd2:
            raise ValueError("new password does not match")

        data = {"code": code, "old_pwd": old_pwd, "new_pwd": new_pwd1}
        resp = self.do_post("users/%s/pwd_change"%user_id, data)
        if resp.status_code==200:
            return eval(resp.content.decode())


    def delete_user(self, user_id):
        self.do_delete("users/%s"%user_id)

    def user_exists(self, user_id):
        resp = self.do_get("users/%s/exists"%(user_id))
        if resp.status_code==200:
            return eval(resp.content.decode())["result"]==str(True)

    def create_course(self, cspec, owner=""):
        cspec = json.dumps(cspec)
        data = {"course_spec": cspec, "owner": owner}
        self.do_post("courses", data)

    def create_course_session(self, course_id, session_id, start_date):
        data = {"course_id": course_id, "session_id": session_id, "start_date": start_date}
        self.do_post("courses/%s/sessions"%course_id, data)

    def get_course_session(self, course_id, session_id):
        resp = self.do_get("courses/%s/sessions/%s"%(course_id, session_id))
        if resp.status_code==200:
            return eval(resp.content.decode())

    def get_course_sessions(self, course_id):
        resp = self.do_get("courses/%s/sessions"%(course_id))
        if resp.status_code==200:
            return eval(resp.content.decode())

    def recompute_session_grades(self, course_id, session_id):
        resp = self.do_post("courses/%s/sessions/%s/recompute"%(course_id, session_id))
        if resp.status_code==200:
            return eval(resp.content.decode())

    def update_course(self, cspec):
        course_id = cspec["course_id"]
        cspec = json.dumps(cspec)
        data = {"course_spec": cspec}
        self.do_put("courses/%s"%course_id, data)
        
    def get_course(self, course_id):
        resp = self.do_get("courses/%s"%course_id)
        if resp.status_code==200:
            return eval(resp.content.decode())

    def course_exists(self, course_id):
        resp = self.do_get("courses/%s/exists"%(course_id))
        if resp.status_code==200:
            return eval(resp.content.decode())["result"]==str(True)

    def course_session_exists(self, course_id, session_id):
        resp = self.do_get("courses/%s/sessions/%s/exists"%(course_id, session_id))
        if resp.status_code==200:
            return eval(resp.content.decode())["result"]==str(True)

    def user_session_exists(self, user_id, course_id, session_id):
        resp = self.do_get("users/%s/courses/%s/sessions/%s/exists"%(user_id, course_id, session_id))
        if resp.status_code==200:
            return eval(resp.content.decode())["result"]==str(True)

    def delete_course(self, course_id):
        self.do_delete("courses/%s"%course_id)

    def delete_course_session(self, course_id, session_id):
        self.do_delete("courses/%s/sessions/%s"%(course_id, session_id))

    def delete_user_session(self, user_id, course_id, session_id, delete_grades_and_submissions=False):
        data = {"delete_grades_and_submissions": str(delete_grades_and_submissions)}
        self.do_delete("users/%s/courses/%s/sessions/%s"%(user_id, course_id, session_id), data=data)


    def create_user_session(self, user_id, course_id, session_id):
        data = {"session_id": session_id}
        self.do_post("users/%s/courses/%s/sessions"%(user_id, course_id), data)

    def get_user_sessions(self, user_id=None):
        user_id = user_id if user_id is not None else self.user_id
        resp = self.do_get("users/%s/sessions"%(user_id))
        if resp.status_code==200:
            return eval(resp.content.decode())

    def get_user_session_gradetree(self, course_id=None, session_id=None, user_id=None):
        session_id = session_id if session_id is not None else self.session_id
        course_id = course_id if course_id is not None else self.course_id
        user_id = user_id if user_id is not None else self.user_id
        resp = self.do_get("users/%s/courses/%s/sessions/%s/grade_tree"%(user_id, course_id, session_id))
        if resp.status_code==200:
            r = eval(resp.content.decode())
            return r
                
    def set_grader(self, course_id, lab_id, task_id, 
                   grader_source, grader_function_name,
                   source_functions_names, source_variables_names):
        data = {
                  "grader_source": grader_source,
                  "grader_function_name": grader_function_name,
                  "source_functions_names": source_functions_names,
                  "source_variables_names":source_variables_names
                }
        self.do_post("courses/%s/labs/%s/tasks/%s/grader"%(course_id, lab_id, task_id), data)

    def invite(self, course_id, session_id, invitations_emails):
        data = {
                  "invitations_emails": invitations_emails,
                }
        return self.do_post("courses/%s/sessions/%s/invitations"%(course_id, session_id), data)


    def get_grader(self, course_id, lab_id, task_id):
        resp = self.do_get("courses/%s/labs/%s/tasks/%s/grader"%(course_id, lab_id, task_id))
        if resp.status_code==200:
            return json.loads(resp.content.decode())

    def default_course_session_lab(self, course_id, session_id, lab_id):
        course_id = course_id or self.course_id
        session_id = session_id or self.session_id
        lab_id    = lab_id or self.lab_id
        assert course_id is not None, "must set course_id"
        assert session_id is not None, "must set session_id"
        assert lab_id is not None, "must set lab_id"
        return course_id, session_id, lab_id

    def default_course_lab(self, course_id, lab_id):
        course_id = course_id or self.course_id
        lab_id    = lab_id or self.lab_id
        assert course_id is not None, "must set course_id"
        assert lab_id is not None, "must set lab_id"
        return course_id, lab_id


    def get_grader_source_names(self, course_id=None, lab_id=None, task_id=None):
        course_id, lab_id = self.default_course_lab(course_id, lab_id)
        resp = self.do_get("courses/%s/labs/%s/tasks/%s/grader_source_names"%(course_id, lab_id, task_id))
        if resp.status_code==200:
            return json.loads(resp.content.decode())

    def get_submissions(self, course_id=None, session_id=None, lab_id=None, task_id=None, user_id=None, include_details=False):
        user_id = user_id if user_id is not None else self.user_id
        course_id, session_id, lab_id = self.default_course_session_lab(course_id, session_id, lab_id)
        data = {"include_details": str(include_details) }
        resp = self.do_get("users/%s/courses/%s/sessions/%s/labs/%s/tasks/%s/submissions"%(user_id, course_id, session_id, lab_id, task_id),
                           data=data)
        if resp.status_code==200:
            return json.loads(resp.content.decode())['Items']

    def delete_submissions(self, course_id=None, lab_id=None, task_id=None, user_id=None):
        user_id = user_id if user_id is not None else self.user_id
        course_id, lab_id = self.default_course_lab(course_id, lab_id)
        self.do_delete("users/%s/courses/%s/labs/%s/tasks/%s/submissions"%(user_id, course_id, lab_id, task_id))

    def submit_task(self, namespace, course_id=None, session_id=None, lab_id=None, task_id=None, user_id=None,
                    display_html=True):
        """
        call this function with namespace=globals()
        """
        user_id = user_id if user_id is not None else self.user_id
        course_id, session_id, lab_id = self.default_course_session_lab(course_id, session_id, lab_id)

        source = self.get_grader_source_names(course_id, lab_id, task_id)
        functions = {f: inspect.getsource(namespace[f]) for f in source['source_functions_names']}
        variables = codecs.encode(pickle.dumps({i:namespace[i] for i in source['source_variables_names']}), "base64").decode()

        submission_content = { 'source_functions': functions,
                               'source_variables': variables}

        data = {"submission_content": submission_content}
        resp = self.do_post("users/%s/courses/%s/sessions/%s/labs/%s/tasks/%s"%(user_id, course_id, session_id, lab_id, task_id), data)
        if resp.status_code==200:
           r = eval(resp.content.decode()) 
           gmsg = r["message"].strip()
           if len(gmsg)>0:
              gmsg = "<pre>----- grader message -------</pre>%s<pre>----------------------------</pre>"%gmsg
          
           if display_html:
                s = """
                <b>%s submitted.</b> <b><font color="blue">your grade is %s</font></b> 
                <p/>%s
                <p/><p/>
                <div style="font-size:10px"><b>SUBMISSION CODE</b> %s</div>

                """%(task_id, str(r["grade"]), gmsg, r["submission_stamp"])
                display(HTML(s))               
           return r

    def print_grade_tree(self, course_id=None, session_id=None, user_id=None):
        course_id, session_id, _ = self.default_course_session_lab(course_id, session_id, None)
        print (course_id, session_id)
        gt = self.get_user_session_gradetree(course_id, session_id, user_id)
        course = self.get_course(course_id)
        ccu = Course(course["course_spec"])
        r = "+-------+----------+----------------------------+\n"
        r += "+ grade + part id  + description                +\n"
        r += "+-------+----------+----------------------------+\n"
        r += "%8.2f TOTAL GRADE   %s\n\n"%(gt["grade"], ccu.spec["course_description"])
        for k in sorted(gt["labs"].keys()):
            lab = ccu.get_lab(k)
            r += "+-------+----------+----------------------------+\n"
            r += "%8.2f %-10s %s\n"%(gt["labs"][k]["grade"], k, lab["name"])
            r += "+-------+----------+----------------------------+\n"
            for t in sorted(gt["labs"][k]["tasks"].keys()):
                _, task = ccu.get_labtask(k,t)
                r+="%8.2f %-10s %s\n"%(gt["labs"][k]["tasks"][t], t, task["name"])
            r += "\n"
        print (r)

    def run_grader_locally(self, grader_function_name, source_functions_names, source_variables_names, namespace):
        functions = {f: eval("inspect.getsource(%s)"%f, namespace) for f in source_functions_names}

        # serialize and unserialize variables with pickle to simulate 
        # sending string through http
        dvars = codecs.encode(pickle.dumps({i:namespace[i] for i in source_variables_names}), "base64").decode()
        variables = pickle.loads(codecs.decode(dvars.encode(), "base64"))
        return namespace[grader_function_name](functions, variables, self.user_id)

    def make_backup(self):
        return self.do_get("make_backup")

class Course:

    def __init__(self, spec):
        self.spec = spec
        self.course_id = spec["course_id"]

    def get_lab(self, lab_id):
        for lab in self.spec["labs"]:
            if lab["lab_id"]==lab_id:
                return lab
        assert False, "lab %s, in course %s not found"%(lab_id, self.course_id)

    def get_labtask(self, lab_id, task_id):
        for lab in self.spec["labs"]:
            if lab["lab_id"]==lab_id:
                for task in lab["tasks"]:
                    if task["task_id"]==task_id:
                        return lab, task
        assert False, "lab/task %s/%s, in course %s not found"%(lab_id, task_id, self.course_id)
