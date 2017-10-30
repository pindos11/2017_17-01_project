from multiprocessing import Process
import socket,time

def error_p(errmsg):
    print("Error: "+errmsg)

def logmsg(logmsg):
    a = time.strftime("%H-%M %d %h %Y")
    print(a+": "+logmsg)

def work_cmds(cmd):
    if(cmd=="/time"):
        return(time.strftime("%H-%M %d %h %Y"))
    elif(cmd=="/help"):
        return("Я еще не написал помощь")
    else:
        return(cmd)

def work_with_client(conn,addr):
    twords = ["/help","/time"]
    msg = b""
    while True:
        data = conn.recv(1024)
        if((not data)or(data.decode("utf-8")[-3:]=="FIN")):
            msg+=data
            break
        msg+=data
    try:
        lmsgd = msg.decode("utf-8").split("|")
        mtype = lmsgd[0]
        nick = lmsgd[1]
        message = lmsgd[2][:50]
        if(len(nick)>10):
            conn.send("BN".encode('utf-8'))
            conn.close()
            return
        if(len(message)==0):
            conn.send("BAD".encode("utf-8"))
            conn.close()
        if(mtype=="MSG"):
            if(message in twords):
                message = work_cmds(message)
                nick = "Serv"
            f = open("msgl","ab")
            f.write((nick+": "+message+"\n").encode("utf-8"))
            f.close()
            conn.send("OK".encode("utf-8"))
            conn.close()
            logmsg(nick+": "+message)
        if(mtype=="UPD"):
            f = open("msgl","rb")
            dat = f.read()
            f.close()
            rdat = dat.decode("utf-8").split("\n")
            rdat = rdat[-10:]
            odat = ("\n".join(rdat)+"|FIN").encode("utf-8")
            msg_t = []
            while(len(odat)>1024):
                msg_t.append(odat[:1024])
                odat=odat[1025:]
            msg_t.append(odat)
            for msgp in msg_t:
                conn.send(msgp)
            conn.close()
    except Exception as err:
        print(err)
        error_p("wrong message")
        conn.send("BAD".encode("utf-8"))
        conn.close()
        return
        
        

if(__name__=="__main__"):
    sock = socket.socket()
    sock.bind(('192.168.1.4', 9090))
    sock.listen(10)
    while True:
        conn, addr = sock.accept()
        answ = Process(target=work_with_client,args=(conn,addr))
        answ.start()
        answ.join()