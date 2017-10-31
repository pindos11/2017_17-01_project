from multiprocessing import Process
import socket,time,sqlite3,time,os,random

KEY_DECAY_TIME = 3600 #seconds. has to be no longer than 9999 for protocol v1 
ONLINE_CONFIRM_TIME = 600

def error_p(errmsg):
    print("Error: "+errmsg)

def logmsg(logmsg):
    a = time.strftime("%H-%M %d %h %Y")
    print(a+": "+logmsg)

def add_nulls(dlen,data):
    to_ret = data
    if(len(data)<dlen):
        dif = dlen-len(data)
        to_ret = "0"*dif+to_ret
    return to_ret

class dbwork:
    #1)login,password,id - logindata
    #2)id,key,time_to_change_key - keys
    #3)id,time_to_offline - onlines
    #4)id,unread_messages - messages
    def __init__(self):
        connection = sqlite3.connect("chatdb.db")
        cur = connection.cursor()
        #creating tables
        cur.execute('''
            CREATE TABLE IF NOT EXISTS logindata(
                ID INTEGER PRIMARY KEY,
                LOGIN TEXT,
                PASSWORD TEXT)
            ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS keys(
                ID INTEGER,
                KEY INTEGER,
                DTIME INTEGER)
            ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS onlines(
                ID INTEGER PRIMARY KEY,
                OTIME INTEGER)
            ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS messages(
                ID INTEGER,
                MESSAGE BLOB)
            ''')#ID of the user to recive message
        connection.commit()
        connection.close()

    def generate_key(self,ID): #generates a new key for given ID
        random.seed()
        connection = sqlite3.connect("chatdb.db")
        cur = connection.cursor()
        key = random.randint(10000000,99999999)
        ok = 0
        while(ok==0): #generating a unique key for messaging
            cur.execute("SELECT * FROM keys WHERE KEY = ?",(key,))
            if(cur.fetchone()==None):
                ok = 1
                break
            else:
                key = random.randint(10000000,99999999)
        cur.execute("SELECT * FROM keys WHERE ID = ?",(ID,)) #checking if the
        dtime = time.time()+KEY_DECAY_TIME                   #ID in table
        if(cur.fetchone()==None):
            cur.execute("INSERT INTO keys VALUES (?,?,?)",(ID,key,dtime))
        else:
            cur.execute("UPDATE keys SET KEY = ?, DTIME = ? WHERE ID = ?",(key,dtime,ID))
        connection.commit()
        connection.close()
        return(key)

    def get_messages(self,ID):
        connection = sqlite3.connect("chatdb.db")
        cur = connection.cursor()
        cur.execute("SELECT MESSAGE FROM messages WHERE ID = ?",(ID,))
        msgs = cur.fetchall()
        msgdata = b""
        if(msgs==[]):
            connection.close()
            return(0)
        else:
            for msg in msgs:
                message = msg[0]
                msgdata+=message
            cur.execute("DELETE FROM messages WHERE ID = ?",(ID,))
            connection.commit()
            connection.close()
            return(msgdata)

    def get_ID_by_login(self,login):
        connection = sqlite3.connect("chatdb.db")
        cur = connection.cursor()
        cur.execute("SELECT ID FROM logindata WHERE LOGIN = ?",(login,))
        ID = cur.fetchone()[0]
        connection.close()
        return(ID)
    
    def get_key(self,ID): #returns a key for given ID
        connection = sqlite3.connect("chatdb.db")
        cur = connection.cursor()
        cur.execute("SELECT KEY FROM keys WHERE ID = ?",(ID,))
        key = cur.fetchone()
        if(key!=None):
            key=key[0]
        connection.close()
        return(key)

    def get_key_dtime(self,ID):
        connection = sqlite3.connect("chatdb.db")
        cur = connection.cursor()
        cur.execute("SELECT DTIME FROM keys WHERE ID = ?",(ID,))
        dtime = cur.fetchone()
        if(dtime!=None):
            dtime=dtime[0]
        connection.close()
        return(dtime)
    
    def get_ID_by_key(self,key):
        connection = sqlite3.connect("chatdb.db")
        cur = connection.cursor()
        cur.execute("SELECT ID, DTIME FROM keys WHERE key = ?",(key,))
        uid = cur.fetchone()
        connection.close()
        if(uid==None):
            return(-1)#no such key
        else:
            dtime = uid[1]
            uid = uid[0]
            if(dtime<time.time()):
                return(-2)#timed out key
            else:
                return(uid)
        
    def update_user_online(self,ID):
        otime = time.time()+ONLINE_CONFIRM_TIME
        connection = sqlite3.connect("chatdb.db")
        cur = connection.cursor()
        cur.execute("REPLACE INTO onlines VALUES(?,?)",(ID,otime))
        connection.commit()
        connection.close()

    def get_users_online(self):
        ctime = time.time()
        connection = sqlite3.connect("chatdb.db")
        cur = connection.cursor()
        cur.execute("SELECT ID FROM onlines WHERE OTIME > ?",(ctime,))
        onlineIDs = cur.fetchall()
        onlines = []
        if(onlineIDs == []):
            return([])
        else:
            for oid in onlineIDs:
                onlines.append(oid[0])
            return(onlines)

    def add_message(self,ID,msg):
        connection = sqlite3.connect("chatdb.db")
        cur = connection.cursor()
        cur.execute("INSERT INTO messages VALUES(?,?)",(ID,msg))
        connection.commit()
        connection.close()
    
    def login(self,login,password):
        connection = sqlite3.connect("chatdb.db")
        cur = connection.cursor()
        cur.execute("SELECT * FROM logindata WHERE LOGIN = ?",(login,))
        udata = cur.fetchone()
        if(udata==None):
            cur.execute("INSERT INTO logindata VALUES (NULL,?,?)",(login,password))
            connection.commit()
            connection.close()
            ID = self.get_ID_by_login(login)
            key = self.generate_key(ID)
            self.update_user_online(ID)
            return([0,key]) #OK - new registered
        else:
            if(udata[2]==password):
                connection.close()
                ID = self.get_ID_by_login(login)
                key = self.generate_key(ID)
                self.update_user_online(ID)
                return([0,key]) #OK - ok login&pwd
            else:
                connection.close()
                return([1,0]) #login already exists(it means - password incorrect)


class client_job:

    def send_close(self,data):
        try:
            self.conn.send(data.encode("utf-8"))
        except:
            self.conn.send(data)
        self.conn.close()

    def send_msg(self,data):
        try:
            self.conn.send(data.encode("utf-8"))
        except:
            self.conn.send(data)
    
    def answer_ask_chk(self):
        self.ID = self.database.get_ID_by_key(self.key)
        if(self.ID>0):
            dtime = self.database.get_key_dtime(self.ID)
            dtime-=time.time()
            dtime = add_nulls(4,str(dtime))
            self.database.update_user_online(self.ID)
            self.send_msg("OK"+dtime)
            return(-1)
        else:
            if(self.ID==-1):
                self.error = 5 #wrong key
            else:
                self.error = 6 #key timed out
            return(0)

    def read_ask_msg(self,data):
        try:
            ask_m = data.decode("utf-8")
        except:
            self.error = 1 #encoding failure
            return(0)
        if(len(ask_m)!=11):
            self.error = 3 #message badly structured
            return(0)
        mtype = ask_m[:3]
        if(mtype=="CHK"):
            try:
                self.key = int(ask_m[3:])
            except:
                self.error = 5
                return(0)
            return self.answer_ask_chk()
        if(mtype=="MES"):
            try:
                self.protocol = int(ask_m[3:7])
                ret_bytes = int(ask_m[7:])
            except:
                self.error = 1
                return(0)
            return ret_bytes
        else:
            self.error = 2 #unknown initiation
            return(0)

    def check_key_ID(self):
        realID = self.database.get_ID_by_key(self.key)
        if(realID==self.ID):
            return(1)
        else:
            if(realID==-1):
                self.error = 5
                return(0)
            else:
                self.error = 6
                return(0)
            
    
    def process_message(self,trg_ID,message):
        if(self.check_key_ID()==1):
            if(self.database.get_key(trg_ID)==None):
                self.error = 9
                return(0)
            else:
                msglen = str(add_nulls(4,str(len(message)))).encode("utf-8")
                sender = str(add_nulls(8,str(self.ID))).encode("utf-8")
                dbmsg = sender+msglen+message #add a sender's ID and msglen
                self.database.add_message(trg_ID,dbmsg)
                self.database.update_user_online(self.ID)
                msg = "OK"+add_nulls(16,"")
                self.send_msg(msg)
                return(-1)
        else:
            self.error = 5
            return(0)
    
    def read_msg(self,data,len_m):
        if(len(data)!=len_m):
            self.error = 3
            return(0)
        try:
            mtype = data[:3].decode("utf-8")
        except:
            self.error = 1
            return(0)
        if(data[-3:].decode("utf-8")!="FIN"):
            self.error = 3
            return(0)
        if(mtype=="MSG"):#messages can be not a unicode str
            if(self.protocol==1):
                try:
                    self.ID = int(data[3:11].decode("utf-8"))
                    self.key = int(data[11:19].decode("utf-8"))
                    trg_ID = int(data[19:27].decode("utf-8"))
                except:
                    self.error = 3
                    return(0)
                msg = data[27:-3]
                return(self.process_message(trg_ID,msg))
            else:
                self.error = 4 #protocol mismatch
                return(0)
        try:
            cl_data = data.decode("utf-8")
        except:
            self.error = 1
            return(0)
        if(cl_data[-3:]!="FIN"):
            self.error = 3
            return(0)
        mtype = cl_data[:3]
        if(mtype=="LOG"):
            if(self.protocol==1):
                try:
                    llen = int(cl_data[3:7])
                    plen = int(cl_data[7:11])
                except:
                    self.error = 3
                    return(0)
                self.login = cl_data[11:11+llen]
                self.password = cl_data[11+llen:11+llen+plen]
                result = self.database.login(self.login,self.password)
                if(result[0]==0):
                    self.key = result[1]
                    self.ID = self.database.get_ID_by_key(self.key)
                    if(self.ID<0):
                        self.error = 7 #internal error???? must not happen
                        return(0)
                    else:
                        msg = "OK"+add_nulls(8,str(self.key))+add_nulls(8,str(self.ID))
                        self.send_msg(msg)
                        return(-1)
                else:
                    self.error = 8 #wrong password for existing login
                    return(0)
            else:
                self.error = 4
                return(0)
        if(mtype=="UPD"):
            if(self.protocol==1):
                try:
                    self.key = int(cl_data[3:11])
                except:
                    self.error = 5
                    return(0)
                self.ID = self.database.get_ID_by_key(self.key)
                if(self.ID>0):
                    msgdata = self.database.get_messages(self.ID)
                    if(msgdata==0):
                        self.error = 10
                        return(0)
                    else:
                        msgdata = msgdata
                        msg = "OK"+add_nulls(16,str(len(msgdata)))
                        self.database.update_user_online(self.ID)
                        self.send_msg(msg)
                        self.send_msg(msgdata)
                        return(-1)
                else:
                    self.error = 5
                    return(0)
            else:
                self.error = 4
                return(0)
        if(mtype=="WOL"):
            if(self.protocol==1):
                onlines = self.database.get_users_online()
                if(onlines==[]):
                    self.error = 11
                    return(0)
                outmsg = ""
                for oid in onlines:
                    outmsg+=add_nulls(8,str(oid))
                outmsg = outmsg.encode("utf-8")
                lenmsg = len(outmsg)
                msg = "OK"+add_nulls(16,str(lenmsg))
                self.send_msg(msg)
                self.send_msg(outmsg)
                return(-1)
            else:
                self.error = 4
                return(0)
    
    def work_with_client(self,conn,addr):
        self.database = dbwork()
        self.conn = conn
        self.addr = addr
        self.ID = ""
        self.key = ""
        self.login = ""
        self.password = ""
        self.protocol = 0
        self.error = 0 #zero is for unknown error
        data = self.conn.recv(11)
        to_recieve = self.read_ask_msg(data)
        if(to_recieve==0):
            bmsg = "BA"+add_nulls(4,str(self.error))
            self.conn.send(bmsg.encode("utf-8"))
            self.conn.close()
            return
        elif(to_recieve==-1):
            self.conn.close()
            return
        else:
            self.conn.send("OK0000".encode("utf-8"))
            data = conn.recv(to_recieve)
            to_recieve = self.read_msg(data,to_recieve)
            if(to_recieve==0):
                bmsg = "BA"+add_nulls(16,str(self.error))
                self.conn.send(bmsg.encode("utf-8"))
                self.conn.close()
            else:
                self.conn.close()

#KEEP IN MIND THAT MULTIPROCESS DOES NOT WORK IN IDLE, START THE SERVER
#USING A DOUBLECLICK ON PY FILE

def start_process(conne,addre):
    job = client_job()
    job.work_with_client(conne,addre)
        
        
#a = dbwork()
#print(a.login("SAS","123"))
#print(a.get_messages(2))
if(__name__=="__main__"):
    sock = socket.socket()
    sock.bind(('192.168.1.3', 9090))
    sock.listen(10)
    while True:
        conn, addr = sock.accept()
        answ = Process(target=start_process,args=(conn,addr))
        answ.start()
        answ.join()