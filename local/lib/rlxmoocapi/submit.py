from IPython.display import display,Javascript,HTML
import json

def unicode_bytelist_to_str(ib):
    return u"".join([chr(ib[2*i]*256+ib[2*i+1]) for i in range(len(ib)//2)])

common_js ="""
    // pack and unpack functions taken from here
    // from https://codereview.stackexchange.com/questions/3569/pack-and-unpack-bytes-to-strings    
    function pack(bytes) {
        var chars = [];
        for(var i = 0, n = bytes.length; i < n;) {
            chars.push(((bytes[i++] & 0xff) << 8) | (bytes[i++] & 0xff));
        }
        return String.fromCharCode.apply(null, chars);
    }

    function unpack(str) {
        var bytes = [];
        for(var i = 0, n = str.length; i < n; i++) {
            var char = str.charCodeAt(i);
            bytes.push(char >>> 8, char & 0xFF);
        }
        return bytes;
    }    

    function get_next_cell(cell_id) {
        var cells = Jupyter.notebook.get_cells();
        var found = false;
        for (var i=0; i<cells.length; i++) {
            if (found) return cells[i];
            if (cells[i]["cell_id"]==cell_id) found=true;
        }
        return undefined
    }

    function delete_cell(cell) {
        var cells = Jupyter.notebook.get_cells();
        for (var i=0; i<cells.length; i++) {
            if (cells[i]["cell_id"]==cell["cell_id"]) {
                Jupyter.notebook.delete_cell(i)
            }
        }
    }

    function delete_cell_with_content(content) {
        var cells = Jupyter.notebook.get_cells();
        for (var i=0; i<cells.length; i++) {
            if (cells[i].get_text().includes(content)) {
                Jupyter.notebook.delete_cell(i)
            }
        }
    }

    function get_current_cell() {
        var selected_cell_index = Jupyter.notebook.get_selected_index()
        return Jupyter.notebook.get_cells()[selected_cell_index]
    }

    function insert_cell_after_current(cell_type) {
        var selected_cell_index = Jupyter.notebook.get_selected_index()
        var newcell = Jupyter.notebook.insert_cell_at_index(cell_type, selected_cell_index)
        return newcell
    }


    function get_cells(metadata_key, metadata_content) {

        var cells = Jupyter.notebook.get_cells()
        var rcells = []
        for (var i=0; i<cells.length; i++) {
            if ((metadata_key=="") || (metadata_key==undefined)) {
                rcells.push(cells[i])
            } else {
                if (metadata_key in cells[i]._metadata) {
                    if ((metadata_content == undefined) || (metadata_content==cells[i]._metadata[metadata_key])) {
                        rcells.push(cells[i])  
                    }
                }
            }    
        }
        return rcells
    }
    function get_cells_with_metadatakey(metadata_key) {
        var cells = Jupyter.notebook.get_cells()
        var rcells = {};
        for (var i=0; i<cells.length; i++) {
            if (metadata_key in cells[i]._metadata) {
                var val = cells[i]._metadata[metadata_key]
                if (!(val in rcells)) {
                    rcells[val] = []
                }
                rcells[val].push(cells[i])
            }
        }
        return rcells
    }

    function get_methods(obj)
    {
        var res = [];
        for(var m in obj) {
            if(typeof obj[m] == "function") {
                res.push(m)
            }
        }
        return res;
    }    

    function send_cells_to_python(cells) {
        var kernel = IPython.notebook.kernel;
        cells = unpack(JSON.stringify(cells))
        var pycode="from rlxmoocapi import submit; import json; submit.CellStorage.cells=["+cells+"];";
        pycode += "\\ncells=json.loads(submit.unicode_bytelist_to_str(submit.CellStorage.cells))"
        kernel.execute(pycode);

    }
"""

def get_notebook_cells(metadata_key=""):

    js=common_js+"""

    var task_id = "%s";
    var task_cells = get_cells_with_metadatakey(task_id)
    send_cells_to_python(task_cells)

    if(1==0) {
        var kernel = IPython.notebook.kernel;
        var pycode="from rlxmoocapi import submit; submit.CellStorage.cells="+task_cells+";";
        pycode += "\\ncells=submit._get_notebook_cells_stage2()"
        kernel.execute(pycode);

        var cell = get_current_cell()
        delete_cell_with_content(task_id+" submission code")
        var cell = insert_cell_after_current("markdown")
        cell.set_text(task_id+" submission code is \\n## "+Math.random())
        cell.render()
    }
    """%(metadata_key)
    
    display(Javascript(js))  

def submit_task(session, course_id, lab_id, task_id):
    url = "%s/users/%s/courses/%s/labs/%s/tasks/%s"%(session.endpoint, session.user, course_id, lab_id, task_id)
    js=common_js+"""

    var url = '%s'
    console.log("URL", url)
    var task_id = "%s";
    var task_cells = get_cells_with_metadatakey(task_id)
    var xhttp = new XMLHttpRequest();
    xhttp.open("POST", url, false);

    xhttp.onreadystatechange = function() {
        var r = JSON.parse(this.response)
        var text = "### "+task_id+" submission result"
        console.log(this.response)
        if ("error" in r) {
            text += "\\n\\n### **error**: <font color='red'>"+r["error"]+"</font>"
            text += "\\n\\n```"+r["traceback"]+"```"
        } else {
            var grade = r["grade"]
            var msg   = r["message"]
            var code  = r["submission_stamp"]
            text += "\\n |grade| msg |"
            text += "\\n |:-:|:-|"
            text += "\\n |"+grade+"|"+msg+"|"
            text += "\\n\\n**submission stamp**: "+code
        }
        var cell = get_current_cell()
        delete_cell_with_content(task_id+" submission result")
        var cell = insert_cell_after_current("markdown")
        cell.set_text(text)
        cell.render()
    };
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.setRequestHeader('Mooc-Token', '%s');
    xhttp.send(JSON.stringify({"submission_content": task_cells}));

    """%(url, task_id, session.token)
    
    display(Javascript(js))  


def test(session):
    url = "%s/users/%s"%(session.endpoint, session.user)
    print (url)
    js=common_js+"""
    var url = '%s'
    var token = '%s'

    console.log("URL", url)
    var xhttp = new XMLHttpRequest();
    xhttp.open("GET", url, true);
    xhttp.onreadystatechange = function() {
        console.log("XXX", this)
    };
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.setRequestHeader('Mooc-Token', token);
    xhttp.send();
    """%(url, session.token)
    
    display(Javascript(js)) 


class CellStorage:
    cells = None

def submit_button(user, course_id, lab_id,task_id):
    import ipywidgets as widgets
    b = widgets.Button(
        description='submit',
        disabled=False,
        button_style='info', # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Click me',
        icon='check'
    )
    def button_click(args):
        submit_task(user, course_id, lab_id, task_id)
    b.on_click(button_click)
    return b
