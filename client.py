import socket,tkinter
addr = "5.35.15.21"
port = 9090
bads = ["BN","BAD"]
chist = ""
def send_msg(nick,msg):
    sock = socket.socket()
    sock.connect((addr, port))
    msgo = ('MSG|'+nick+"|"+msg+"|FIN")
    msgo = msgo.encode("utf-8")
    msg_t = []
    while(len(msgo)>1024):
        msg_t.append(msgo[:1024])
        msgo=msgo[1025:]
    msg_t.append(msgo)
    for msgp in msg_t:
        sock.send(msgp)
    answ = sock.recv(1024)
    sock.close()

def ask_upd(nick):
    sock = socket.socket()
    sock.connect((addr, port))
    sock.send(("UPD|"+nick+"|ask|FIN").encode('utf-8'))
    adat = b""
    while True:
        dat = sock.recv(1024)
        if(not dat)or(dat.decode('utf-8')[-3:]=="FIN"):
            adat+=dat
            break
        if(dat.decode("utf-8") in bads):
            return bad_proc(dat.decode("utf-8"))
        adat+=dat
    return(adat.decode("utf-8"))

def bad_proc(answ):
    print(answ)
    return("")

def upd_mlog():
    mlog.after(1000,upd_mlog)
    try:
        d = ask_upd(nick).split("|")[0].split("\n")
    except Exception as err:
        print(err)
        mw.destroy()
        exit()
    d.reverse()
    mlog.delete('1.0',tkinter.END)
    n = 1
    for i in d:
        mlog.insert(float(n),i+"\n")
        n+=1

def smsg(*args):
    msg = minp.get()
    minp.delete(0,tkinter.END)
    send_msg(nick,msg)

nick = "ПИПИСИКС"
mw = tkinter.Tk()
mlog = tkinter.Text(mw,height=10,width=80,font="Arial 14")
mlog.pack()
minp = tkinter.Entry(mw)
minp.pack()
sbtn = tkinter.Button(mw,text="Send",command=smsg)
sbtn.pack()
minp.bind("<Return>",smsg)
mlog.after(1000,upd_mlog)
mw.mainloop()