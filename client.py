import socket,sqlite3,tkinter,time
from multiprocessing import Process, Queue


def add_nulls(dlen,data):
    to_ret = data
    if(len(data)<dlen):
        dif = dlen-len(data)
        to_ret = "0"*dif+to_ret
    return to_ret

class settings:
    def __init__(self):
        connection = sqlite3.connect("conf.db")
        cur = connection.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS config(
                NAME TEXT,
                VALUE TEXT)
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS servers(
                ID INTEGER PRIMARY KEY,
                NAME TEXT,
                ADDR TEXT,
                PORT TEXT,
                LOGIN TEXT,
                PASSWORD TEXT)
        ''')
        connection.commit()
        connection.close()
        
    def get_setting(self,sname):
        connection = sqlite3.connect("conf.db")
        cur = connection.cursor()
        cur.execute("SELECT VALUE FROM config WHERE NAME = ?",(sname,))
        result = cur.fetchone()
        connection.close()
        return(result)

    def set_setting(self,sname,value):
        connection = sqlite3.connect("conf.db")
        cur = connection.cursor()
        cur.execute("INSERT INTO config VALUES(?,?)",(sname,value))
        connection.close()

    def save_server(self,sname,addr,port,login,pwd):
        connection = sqlite3.connect("conf.db")
        cur = connection.cursor()
        cur.execute("REPLACE INTO servers VALUES(NULL,?,?,?,?,?)",(sname,addr,port,login,pwd))
        connection.commit()
        connection.close()

    def get_all_servers(self):
        connection = sqlite3.connect("conf.db")
        cur = connection.cursor()
        cur.execute("SELECT * FROM servers")
        result = cur.fetchall()
        connection.close()
        return(result)

class history:
    def make_tname(self,cID,sID):
        tname = "chat"
        tname+=add_nulls(8,str(cID))
        tname+=add_nulls(8,str(sID))
        return(tname)

    def add_msg(self,cID,sID,sender,message):
        tname = self.make_tname(cID,sID)
        connection = sqlite3.connect("chats.db")
        cur = connection.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS '''+tname+'''(
                SENDER INTEGER,
                MESSAGE BLOB)
        ''')
        connection.commit()
        cur.execute("INSERT INTO "+tname+" VALUES(?,?)",(sender,message))
        connection.commit()
        connection.close()

    def get_chat(self,cID,sID):
        tname = self.make_tname(cID,sID)
        connection = sqlite3.connect("chats.db")
        cur = connection.cursor()
        try:
            cur.execute("SELECT * FROM "+tname)
            result = cur.fetchall()
        except:
            result = []
        connection.close()
        return(result)

class connection:
    def __init__(self,serv):
        self.addr = serv[2]
        self.port = int(serv[3])
        self.login = serv[4]
        self.pwd = serv[5]
        self.key = 0
        self.ID = 0

    def check_connection(self):
        key,ID = self.perform_login()
        self.key = key
        self.ID = ID
        if(key!=0 and ID!=0):
            return(1)
        else:
            return(0)
        
    def get_users(self):
        msg = "WOLFIN".encode("utf-8")
        msglen = len(msg)
        t,sock = self.say_hello(msglen)
        if(t==1):
            sock.send(msg)
            answ = sock.recv(18).decode("utf-8")
            if(answ[:2]=="OK"):
                torec = int(answ[2:])
                answ = sock.recv(torec)
                answ = answ.decode("utf-8")
                to_ret = []
                while(len(answ)>8):
                    to_ret.append(answ[:8])
                    answ = answ[8:]
                to_ret.append(answ)
                return(to_ret)
            else:
                return([])
                   
        
    def check_key(self):
        sock = socket.socket()
        sock.connect((self.addr, self.port))
        msg = ("CHK"+str(self.key)).encode("utf-8")
        sock.send(msg)
        answ = sock.recv(6)
        print(answ)

    def say_hello(self,size):
        sock = socket.socket()
        sock.connect((self.addr, self.port))
        msg = ("MES0001"+add_nulls(4,str(size))).encode("utf-8")
        sock.send(msg)
        answ = sock.recv(6)
        answ = answ.decode("utf-8")
        if(answ[:2]=="OK"):
            return(1,sock)
        else:
            return(0,sock)

    def perform_login(self):
        login = self.login.encode("utf-8")
        pwd = self.pwd.encode("utf-8")
        llen = add_nulls(4,str(len(login))).encode("utf-8")
        pwdlen = add_nulls(4,str(len(pwd))).encode("utf-8")
        msg = "LOG".encode("utf-8")+llen+pwdlen+login+pwd+"FIN".encode("utf-8")
        msglen = len(msg)
        t,sock = self.say_hello(msglen)
        if(t==1):
            sock.send(msg)
            answ = sock.recv(18)
            answ = answ.decode("utf-8")
            if(answ[:2]=="OK"):
                key = int(answ[2:10])
                ID = int(answ[10:])
                return(key,ID)
            else:
                return(0,0)
        else:
            return(0,0)
                

    def send_msg(self,msg,tid):
        sidstr = add_nulls(8,str(self.ID))
        tidstr = add_nulls(8,str(tid))
        kkey = add_nulls(8,str(self.key))
        smsg = ("MSG"+sidstr+kkey+tidstr+msg+"FIN").encode("utf-8")
        msglen = len(smsg)
        t,sock = self.say_hello(msglen)
        if(t==1):
            sock.send(smsg)
            answ = sock.recv(18)
            answ = answ.decode("utf-8")
            if(answ[:2]=="OK"):
                return(1)
            else:
                return(0)
        else:
            return(0)

    def get_messages(self):
        kkey = add_nulls(8,str(self.key))
        smsg = ("UPD"+kkey+"FIN").encode("utf-8")
        msglen = len(smsg)
        t,sock = self.say_hello(msglen)
        if(t==1):
            sock.send(smsg)
            answ = sock.recv(18)
            torec = 0
            try:
                answ=answ.decode("utf-8")
            except:
                return(0)
            if(answ[:2]=="OK"):
                try:
                    torec = int(answ[2:])
                except:
                    return(0)
                answ2 = sock.recv(torec)
                to_ret = []
                while(len(answ2)>4):
                    sender = int(answ2[:8].decode("utf-8"))
                    msglen = int(answ2[8:12].decode("utf-8"))
                    msg = answ2[12:12+msglen]
                    answ2 = answ2[12+msglen:]
                    to_ret.append((sender,msg))
                return(to_ret)
            else:
                return(-1)
        else:
            return(0)


class prog_windowed:
    def __init__(self):
        self.curuid = 0
        self.settings = settings()
        self.chathist = history()
        self.mw = tkinter.Tk()
        self.mw.geometry("800x600")
        servers = self.settings.get_all_servers()
        if(servers==[]):
            self.make_serv_adding()
        else:
            self.show_serverlist()
        self.mw.mainloop()

    def make_serv_adding(self):
        try:
            self.sl.destroy()
        except:
            pass
        self.sadd = tkinter.Toplevel()
        self.sadd.title("Add a server")
        self.sadd.geometry("300x300")
        self.l1 = tkinter.Label(self.sadd,text="Serv name")
        self.l1.pack()
        self.addname = tkinter.Entry(self.sadd)
        self.addname.pack()

        self.l2 = tkinter.Label(self.sadd,text="Serv addr")
        self.l2.pack()
        self.addaddr = tkinter.Entry(self.sadd)
        self.addaddr.pack()

        self.l3 = tkinter.Label(self.sadd,text="Serv port")
        self.l3.pack()
        self.addport = tkinter.Entry(self.sadd)
        self.addport.pack()

        self.l4 = tkinter.Label(self.sadd,text="Login")
        self.l4.pack()
        self.addlogin = tkinter.Entry(self.sadd)
        self.addlogin.pack()

        self.l5 = tkinter.Label(self.sadd,text="Password")
        self.l5.pack()
        self.addpwd = tkinter.Entry(self.sadd)
        self.addpwd.pack()

        self.acceptbtn = tkinter.Button(self.sadd,text="Save",command = self.save_serv)
        self.acceptbtn.pack()

    def save_serv(self):
        sname = self.addname.get()
        saddr = self.addaddr.get()
        sport = self.addport.get()
        slogin = self.addlogin.get()
        spassw = self.addpwd.get()
        self.settings.save_server(sname,saddr,sport,slogin,spassw)
        self.sadd.destroy()
        self.show_serverlist()

    def show_serverlist(self):
        self.sl = tkinter.Toplevel()
        self.sl.title("Choose a server to connect")
        self.sl.geometry("300x300")

        self.servs = self.settings.get_all_servers()
        
        self.l1 = tkinter.Label(self.sl,text = "Select a server from list")
        self.l1.pack()

        self.slist = tkinter.Listbox(self.sl)
        for i in self.servs:
            self.slist.insert(tkinter.END, i[1])
        self.slist.pack()

        self.cbtn = tkinter.Button(self.sl,text="Connect",command = self.connserv)
        self.cbtn.pack()

        self.abtn = tkinter.Button(self.sl,text="Add new server",command = self.make_serv_adding)
        self.abtn.pack()

    def connserv(self):
        self.current_server = self.servs[self.slist.curselection()[0]]
        self.sl.destroy()
        self.connection = connection(self.current_server)
        t = self.connection.check_connection()
        if(t==0):
            self.show_servlist()
        else:
            self.make_chatwindow(t)

    def make_chatwindow(self,users_online):
        self.texts = tkinter.Text(self.mw)
        self.texts.configure(width=60)
        self.texts.place(x=10,y=10)

        self.users = tkinter.Listbox(self.mw)
        self.users.configure(height = 23)
        self.users.place(x=600,y=10)
        self.ulist = self.connection.get_users()
        for u in self.ulist:
            self.users.insert(tkinter.END,str(u))
        self.users.bind("<Double-Button-1>",self.change_chat)
        
        self.msgenter = tkinter.Entry(self.mw)
        self.msgenter.configure(width=80)
        self.msgenter.place(x=10,y=500)

        self.l1 = tkinter.Label(self.mw,text="Message:")
        self.l1.place(x=10,y=470)

        self.sendbtn = tkinter.Button(self.mw,text="Send",command = self.sendmsg)
        self.sendbtn.place(x=500,y=497)

        self.l2 = tkinter.Label(self.mw,text="Your ID is: "+str(self.connection.ID))
        self.l2.place(x=10,y=550)

        self.l2 = tkinter.Label(self.mw,text="Chat with: "+str(self.curuid))
        self.l2.place(x=10,y=400)

        self.mw.after(100,self.check_chats)

    def change_chat(self,pressed):
        uid = self.ulist[self.users.curselection()[0]]
        self.curuid = uid
        self.l2.configure(text="Chat with: "+str(self.curuid))

    def sendmsg(self):
        msg = self.msgenter.get()
        t = self.connection.send_msg(msg,self.curuid)
        if(t==1):
            self.chathist.add_msg(self.curuid,self.current_server[0],0,msg.encode("utf-8"))
            self.msgenter.delete("0",tkinter.END)
        else:
            return

    def check_chats(self):
        uid = self.curuid
        msgs = self.connection.get_messages()
        if(type(msgs) == type([])):
            for msg in msgs:
                self.chathist.add_msg(msg[0],self.current_server[0],1,msg[1])
        data = self.chathist.get_chat(self.curuid,self.current_server[0])
        to_write = []
        for msg in data:
            outmsg = ""
            if(msg[0]==0):
                outmsg+="You: "
            else:
                outmsg+=str(self.curuid)+": "
            try:
                outmsg+=msg[1].decode("utf-8")
            except:
                outmsg+="blob data"
            to_write.append(outmsg)
        to_write.reverse()
        stw = "\n".join(to_write)
        check = self.texts.get("0.0",tkinter.END)
        self.ulist = self.connection.get_users()
        if(list(self.users.get("0",tkinter.END))!=self.ulist):
            self.users.delete('0',tkinter.END)
            for u in self.ulist:
                self.users.insert(tkinter.END,str(u))
        if(check.replace("\n","")!=stw.replace("\n","")):
            self.texts.delete('0.0',tkinter.END)
            self.texts.insert(tkinter.END,stw)
        self.mw.after(1000,self.check_chats)

#33125245
#check_key(33125245)
a = prog_windowed()