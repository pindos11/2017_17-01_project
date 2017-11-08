import socket
addr = ""
port = 0
def add_nulls(dlen,data):
    to_ret = data
    if(len(data)<dlen):
        dif = dlen-len(data)
        to_ret = "0"*dif+to_ret
    return to_ret

def check_key(key):
    global addr
    global port
    addr = addr
    port = port
    sock = socket.socket()
    sock.connect((addr, port))
    msg = ("CHK"+str(key)).encode("utf-8")
    sock.send(msg)
    answ = sock.recv(6)
    print(answ)

def say_hello(size):
    global addr
    global port
    addr = addr
    port = port
    sock = socket.socket()
    sock.connect((addr, port))
    msg = ("MES0001"+add_nulls(4,str(size))).encode("utf-8")
    sock.send(msg)
    answ = sock.recv(6)
    answ = answ.decode("utf-8")
    if(answ[:2]=="OK"):
        return(1,sock)
    else:
        return(0,sock)

def login(login,pwd):
    login = login.encode("utf-8")
    pwd = pwd.encode("utf-8")
    llen = add_nulls(4,str(len(login))).encode("utf-8")
    pwdlen = add_nulls(4,str(len(pwd))).encode("utf-8")
    msg = "LOG".encode("utf-8")+llen+pwdlen+login+pwd+"FIN".encode("utf-8")
    msglen = len(msg)
    t,sock = say_hello(msglen)
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
            

def send_msg(key,msg,sid,tid):
    sidstr = add_nulls(8,str(sid))
    tidstr = add_nulls(8,str(tid))
    kkey = add_nulls(8,str(key))
    smsg = ("MSG"+sidstr+kkey+tidstr+msg+"FIN").encode("utf-8")
    msglen = len(smsg)
    t,sock = say_hello(msglen)
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

def get_messages(key):
    kkey = add_nulls(8,str(key))
    smsg = ("UPD"+kkey+"FIN").encode("utf-8")
    msglen = len(smsg)
    t,sock = say_hello(msglen)
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
            answt = answ2.decode("utf-8")
            return(answt)
        else:
            return(-1)
    else:
        return(0)
#33125245
#check_key(33125245)
key = 0
ID = 0
while True:
    addr = input("Address: ")
    port = int(input("Port: "))
    logint = input("Login: ")
    password = input("Password: ")
    key, ID = login(logint,password)
    if(key != 0 and ID != 0):
        print("YOUR ID IS: "+str(ID))
        break        
while True:
    cmd = input("Command: ")
    if(cmd=="MSG"):
        msg = input("Message(text ||| target ID): ")
        msgd = msg.split("|||")
        text = ""
        tid = 0
        try:
            tid = int(msgd[1])
            text = msgd[0]
        except:
            print("TI DEBIL")
            continue
        stat = send_msg(key,text,ID,tid)
        if(stat==1):
            print(str(ID)+": "+text)
        else:
            print("Not sent")
    elif(cmd=="UPD"):
        msg = get_messages(key)
        if(msg!=0 and msg!=-1):
            msgs = msg.split("|||")
            for i in msgs:
                sid = int(i[:8])
                inmsg = i[8:]
                print(str(sid)+": "+inmsg)
        
        
