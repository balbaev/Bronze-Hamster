import sys
import gobject
import os
import time
import sqlite3
import copy
try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    import gtk
    import gtk.glade
except:
    sys.exit(1)
    
class PyTrabas:
    def __init__(self):
        self.local_path = os.path.realpath(os.path.dirname(sys.argv[0]))
        self.gladefile = os.path.join(self.local_path, "mainwindow.glade")
        self.b_tree = gtk.glade.XML(self.gladefile, "mainWindow")
        dic = { "gtk_main_quit" : self.quit,
                "on_add_task" : self.on_add_task,
                "on_edit_task" : self.on_edit_task,
                "on_delete_task" : self.on_delete_task,
                "on_call_tm" : self.on_call_tm }
        self.b_tree.signal_autoconnect(dic)
        
        self.task_view = self.b_tree.get_widget("task_view")
        
        self.c_task_object = 0
        self.c_root_dir = 1
        self.c_backup_dir = 2
        self.c_freq = 3
        self.c_start_time = 4
        self.s_root_dir = "Root dir"
        self.s_backup_dir = "Backup dir"
        self.s_freq = "Frequency"
        self.s_start_time = "Start time"
        
        self.add_list_column(self.s_root_dir, self.c_root_dir, self.task_view)
        self.add_list_column(self.s_backup_dir, self.c_backup_dir, self.task_view)
        self.add_list_column(self.s_freq, self.c_freq, self.task_view)
        self.add_list_column(self.s_start_time, self.c_start_time, self.task_view)
        
        self.task_list = gtk.ListStore(gobject.TYPE_PYOBJECT,
                                     gobject.TYPE_STRING,
                                     gobject.TYPE_STRING,
                                     gobject.TYPE_STRING,
                                     gobject.TYPE_STRING)
        self.task_view.set_model(self.task_list)
        self.init_db()
        
    def init_db(self):
        db = os.path.join(self.local_path, "db")
        if (os.access(db, os.R_OK)):
            self.conn = sqlite3.connect(db)
            self.c = self.conn.cursor()
            self.c.execute("""
            select root_dir, backup_dir, freq, start_time
            from backup_unit""")
            for row in self.c:
                task = Task(row[0], row[1], row[2], row[3])
                self.task_list.append([task,] + list(row))
        else:
            self.conn = sqlite3.connect(db)
            self.c = self.conn.cursor()
            self.c.executescript("""
            create table backup_unit(
            root_dir varchar, backup_dir varchar, freq varchar, start_time varchar);
            
            create table snapshot_unit(
            root_dir varchar, snapshot varchar, cur_time varchar);
            
            create table log(
            user varchar, message varchar, time varchar);
            
            create table dir_state(
            root_dir varchar, cur_state varchar);
            """)
        
    def add_list_column(self, title, column_id, view):
        """This function adds a column to the list view.
        First it create the gtk.TreeViewColumn and then set
        some needed properties"""
        column = gtk.TreeViewColumn(title, gtk.CellRendererText()
        , text = column_id)
        column.set_resizable(True)
        column.set_sort_column_id(column_id)
        view.append_column(column)
        
    def on_add_task(self, widget):
        task_dlg = TaskDialog()
        result, new_line = task_dlg.run()
        if (result == gtk.RESPONSE_OK):
            os.system("/sbin/btrfs create subvolume %s" % new_line.root_dir)
            self.c.execute("insert into backup_unit values(?,?,?,?)", new_line.get_tuple()[1:])
            self.task_list.append(new_line.get_list())
    
    def on_edit_task(self, widget):
        # Get the selection in the gtk.TreeView
        selection = self.task_view.get_selection()
        # Get the selection iter
        model, selection_iter = selection.get_selected()
        if (selection_iter):
            #if there's selection, get task object
            task = self.task_list.get_value(selection_iter, self.c_task_object)
            last_task = copy.copy(task)
            #create task dialog, based on current data
            task_dlg = TaskDialog(task)
            result, changed_task = task_dlg.run()
            if (result == gtk.RESPONSE_OK):
                self.c.execute("""update backup_unit
                set root_dir=?, backup_dir=?, freq=?, start_time=?
                where root_dir=?"""
                , changed_task.get_tuple()[1:] + (last_task.root_dir,))
                self.task_list.set(selection_iter,
                                   self.c_task_object, changed_task,
                                   self.c_root_dir, changed_task.root_dir,
                                   self.c_backup_dir, changed_task.backup_dir,
                                   self.c_freq, changed_task.freq,
                                   self.c_start_time, changed_task.start_time)
                
    def on_delete_task(self, widget):
        # Get the selection in the gtk.TreeView
        selection = self.task_view.get_selection()
        # Get the selection iter
        model, selection_iter = selection.get_selected()
        if (selection_iter):
            #if there's selection, get task object
            task = self.task_list.get_value(selection_iter, self.c_task_object)
            #create task dialog, based on current data
            self.c.execute("""delete from backup_unit
            where root_dir=?"""
            ,(task.root_dir,))
            self.c.execute("""delete from snapshot_unit
            where root_dir=?"""
            ,(task.root_dir,))
            self.task_list.remove(selection_iter)
            
    def on_call_tm(self, widget):
        # Get the selection in the gtk.TreeView
        selection = self.task_view.get_selection()
        # Get the selection iter
        model, selection_iter = selection.get_selected()
        if (selection_iter):
            #if there's selection, get task object
            task = self.task_list.get_value(selection_iter, self.c_task_object)
            tm_dialog = TimeMachineDialog(task, self.c)
            result = tm_dialog.run()
            
    def quit(self, widget):
        self.conn.commit()
        self.c.close()
        gtk.main_quit()

class Task:
    def __init__(self, root_dir = "", backup_dir = "", freq = "", start_time = time.time()):
        self.root_dir = root_dir
        self.backup_dir = backup_dir
        self.freq = freq
        self.start_time = start_time
        
    def get_list(self):
        return [self, self.root_dir, self.backup_dir, self.freq, self.start_time]
    
    def get_tuple(self):
        return (self, self.root_dir, self.backup_dir, self.freq, self.start_time)
        
class Snapshot:
    def __init__(self, snapshot="", cur_time=time.time()):
        self.snapshot = snapshot
        self.cur_time = cur_time
        
    def get_list(self):
        return [self, self.snapshot, self.cur_time]
    
class TaskDialog:
    def __init__(self, task=Task()):
        self.local_path = os.path.realpath(os.path.dirname(sys.argv[0]))
        self.gladefile = os.path.join(self.local_path, "mainwindow.glade")
        self.task = task
    
    def run(self):
        self.b_tree = gtk.glade.XML(self.gladefile, "dlg_task")
        self.dlg = self.b_tree.get_widget("dlg_task")
        
        self.en_root = self.b_tree.get_widget("en_root_dir")
        self.en_root.set_text(self.task.root_dir)
        self.en_back = self.b_tree.get_widget("en_backup_dir")
        self.en_back.set_text(self.task.backup_dir)
        self.en_freq = self.b_tree.get_widget("en_freq")
        self.en_freq.set_text(self.task.freq)
        #run the dialog and store the response/home/zorgan
        self.result = self.dlg.run()
        #get the value of the entry field
        self.task.root_dir = self.en_root.get_text()
        self.task.backup_dir = self.en_back.get_text()
        self.task.freq = self.en_freq.get_text()
        #we are done with dialog, destroy it
        self.dlg.destroy()
        #return the result and the task
        return self.result, self.task
        
class TimeMachineDialog:
    def __init__(self, task, cursor):
        self.local_path = os.path.realpath(os.path.dirname(sys.argv[0]))
        self.gladefile = os.path.join(self.local_path, "mainwindow.glade")
        self.filesystem = os.path.join(self.local_path, "test.py")
        self.task = task
        self.c = cursor
        
    def run(self):
        self.b_tree = gtk.glade.XML(self.gladefile, "dlg_time_machine")
        self.dlg = self.b_tree.get_widget("dlg_time_machine")
        dic = { "on_make_snapshot" : self.on_make_snapshot,
                "on_time_machine" : self.on_time_machine,
                "on_cur_state" : self.on_cur_state }
        self.b_tree.signal_autoconnect(dic)
        
        self.snapshot_view = self.b_tree.get_widget("snapshot_view")
        
        self.c_snapshot_object = 0
        self.c_snapshot = 1
        self.c_start_time = 2
        self.s_snapshot = "Snapshot"
        self.s_start_time = "Start time"
        
        self.add_list_column(self.s_snapshot, self.c_snapshot, self.snapshot_view)
        self.add_list_column(self.s_start_time, self.c_start_time, self.snapshot_view)
        
        self.snapshot_list = gtk.ListStore(gobject.TYPE_PYOBJECT,
                                     gobject.TYPE_STRING,
                                     gobject.TYPE_STRING)
        self.snapshot_view.set_model(self.snapshot_list)
        
        self.c.execute("select snapshot, cur_time from snapshot_unit where root_dir=?",
                       (self.task.root_dir,))
        for row in self.c:
            snapshot = Snapshot(row[0], row[1])
            self.snapshot_list.append([snapshot,] + list(row))
            
        if len(self.snapshot_list) == 0:
            self.on_make_snapshot(self)
        self.result = self.dlg.run()
        return self.result
    
    def add_list_column(self, title, column_id, view):
        """This function adds a column to the list view.
        First it create the gtk.TreeViewColumn and then set
        some needed properties"""
        column = gtk.TreeViewColumn(title, gtk.CellRendererText()
        , text = column_id)
        column.set_resizable(True)
        column.set_sort_column_id(column_id)
        view.append_column(column)
    
    def on_make_snapshot(self, widget):
        cur_time = time.time()
        #snapshot = self.task.backup_dir + "/" + str(cur_time)
        snapname = '%s-%s' % ( self.task.freq, time.strftime('%Y%m%d-%H%M%S') )
        btrfscmd = '/sbin/btrfs'
        source = self.task.root_dir
        destdir = self.task.backup_dir
        #print ('%s subvolume snapshot "%s" "%s/%s" >/dev/null 2>&1'
        #% ( btrfscmd, source, destdir, snapname ))
        os.system('%s subvolume snapshot "%s" "%s/%s" >/dev/null 2>&1'
        % ( btrfscmd, source, destdir, snapname ))
        self.c.execute("insert into snapshot_unit values(?,?,?)",
                       (self.task.root_dir, snapname, cur_time))
        self.snapshot_list.append(Snapshot(snapname, cur_time).get_list())
        
    def on_time_machine(self, widget):
        selection = self.snapshot_view.get_selection()
        model, selection_iter = selection.get_selected()
        if (selection_iter):
            snapshot = self.snapshot_list.get_value(selection_iter, self.c_snapshot_object)
            source = self.task.root_dir
            destdir = self.task.backup_dir + '/' + snapshot.snapshot
            os.system ('%s %s %s'
                   % (self.filesystem, destdir, source))
            
    def on_cur_state(self, widget):
        source = self.task.root_dir
        os.system ('/usr/bin/fusermount -u -q -z %s'
               % source)
    
if __name__ == "__main__":
    trabas = PyTrabas()
    gtk.main()