import json, notebook, re, inspect, uuid, os
import numpy as np

setgrader_regexp = "#(#*)\s*TEACHER\s*SETGRADER"
definegrader_regexp = "#(#*)\s*TEACHER\s*DEFINEGRADER"

def create_student_lab(source_notebook_fname, target_notebook_fname, enable_wgets=False):
    assert source_notebook_fname!=target_notebook_fname, "source and target notebook file names must be different"
    nb = json.loads("\n".join(open(source_notebook_fname, "r").readlines()))

    rc = []
    for c in nb["cells"]:
        
        
        ## cells to ignore
        if c['cell_type']=='code' and "%%javascript" in "".join(c['source']) and \
           np.sum([re.search("^/+\s*TEACHER", i) is not None for i in c['source']])>0:
            continue
        if c['cell_type']=='code' and 'source' in c and\
          re.search("^\s*#(#*)\s*TEACHER", "".join(c['source'])) is not None:
                    continue
        if c['cell_type']=='code' and 'source' in c and\
          re.search("^\s*\/*\s*javscript", "".join(c['source'])) is not None:
                    print ("removing")
                    continue
                
        ## uncomment wget lines
        if enable_wgets and c['cell_type']=='code' and 'source' in c:
            c['source'] = [i.replace("#!wget", "!wget") for i in c['source']]

        ## cells for which output is kept
        if c['cell_type']=='code' and 'source' in c and\
          re.search("^\s*Image\s*\(", "".join(c['source'])) is not None:
                    rc.append(c)
        elif c['cell_type']=='code' and 'source' in c and\
          re.search("^\s*#(#*)\s*KEEPOUTPUT", "".join(c['source'])) is not None:
            rc.append(c)
        ## all the remaining code cells will get the output removed
        elif c['cell_type']=='code':
            c['outputs'] = []
            rc.append(c)
        else:
            rc.append(c)

    nb["cells"] = rc
    with open(target_notebook_fname, "w") as f:
        f.write(json.dumps(nb))

    print ("student notebook writen to '%s'"%target_notebook_fname)


def get_code_cells(source_notebook_fname, regexp):
    import json, re
    nb = json.loads("\n".join(open(source_notebook_fname, "r").readlines()))

    rc = []
    for c in nb["cells"]:
        if c['cell_type']=='code' and 'source' in c and\
          re.search(regexp, "".join(c['source'])) is not None:
            rc.append("".join(c["source"]))

    return "\n\n\n".join(rc)

def get_setgrader_cells(source_notebook_fname):
    return get_code_cells(source_notebook_fname, 
                          regexp=setgrader_regexp)

def get_definegrader_cells(source_notebook_fname):
    return get_code_cells(source_notebook_fname, 
                          regexp=definegrader_regexp)

import inspect
def deploy_course(admin, teacher, 
                  cspec_file,
                  aggregate_tasks_code=None,
                  aggregate_submissions_code=None,
                  set_grader_notebooks_fileglob="",
                  force_reset=True):
    import json, re, inspect, pickle, base64, time
    
    steacher = base64.urlsafe_b64encode(pickle.dumps(teacher)).decode("utf-8")
    icode  = 'import pickle, base64\n'
    icode += "s='%s'\n"%steacher
    icode += 'teacher = pickle.loads(base64.urlsafe_b64decode(s))'    
    
    with open(cspec_file, "r") as f:
        cspec = json.loads(f.read())
    
    print ("course id: %s"%cspec["course_id"])

    for lab in cspec["labs"]:
        if aggregate_tasks_code is not None:
            lab["aggregate_tasks_code"] = aggregate_tasks_code
        lab["description"] = lab["name"]
        for task in lab["tasks"]:
            if aggregate_submissions_code is not None:
                task["aggregate_submissions_code"] = aggregate_submissions_code

    if admin.course_exists(cspec["course_id"]):
        if force_reset:
            print ("deleting existing course")
            admin.delete_course(cspec["course_id"])
        else:
            print ("updating existing course")
    else:
        print ("creating new course")
    admin.create_course(cspec, owner=teacher.user_id)       
                
    import glob
    notebooks = glob.glob(set_grader_notebooks_fileglob)
    for notebook in notebooks:
        print ("RUNNING SETGRADERS IN %-50s"%("'"+notebook+"'"), end=" .. ")
        code = get_definegrader_cells(notebook)
        code = code.replace("init.course_id", "'%s'"%cspec["course_id"])
        
        unique_filename = 'rr'+str(uuid.uuid4()).replace("-","")
        
        with open("%s.py"%unique_filename, "w") as f:
            f.write(code)
        time.sleep(.5)
        code = get_setgrader_cells(notebook)
        code = code.replace("init.course_id", "'%s'"%cspec["course_id"])
        code = "from %s import * \nimport inspect\n"%unique_filename+code
        print ("found %d setgraders"%len(re.findall(setgrader_regexp, code)))
        exec(code)

        os.remove(unique_filename+".py")

    return cspec["course_id"]

def deploy_session(teacher, course_id, session_id, start_date, force_reset=True):
    if teacher.course_session_exists(course_id, session_id):
        if force_reset:
            teacher.delete_course_session(course_id, session_id)
            print ("deleted session %s %s"%(course_id, session_id))
    print ("creating session %s %s, starting on %s"%(course_id, session_id, start_date))
    teacher.create_course_session(course_id, session_id, start_date)