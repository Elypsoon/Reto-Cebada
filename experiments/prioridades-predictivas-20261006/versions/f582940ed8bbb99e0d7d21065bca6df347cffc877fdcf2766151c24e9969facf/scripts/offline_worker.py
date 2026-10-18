"""Entrada local: bloquea sockets IP antes de cargar el estimador."""
import runpy
import socket
import sys

def blocked(*args,**kwargs):
    raise RuntimeError('Proceso local sin red: conexión IP bloqueada')

original_connect=socket.socket.connect
original_connect_ex=socket.socket.connect_ex
original_sendto=socket.socket.sendto
def connect(self,*args,**kwargs):
    if self.family in [socket.AF_INET,socket.AF_INET6]:return blocked()
    return original_connect(self,*args,**kwargs)
def connect_ex(self,*args,**kwargs):
    if self.family in [socket.AF_INET,socket.AF_INET6]:return blocked()
    return original_connect_ex(self,*args,**kwargs)
def sendto(self,*args,**kwargs):
    if self.family in [socket.AF_INET,socket.AF_INET6]:return blocked()
    return original_sendto(self,*args,**kwargs)
socket.socket.connect=connect
socket.socket.connect_ex=connect_ex
socket.socket.sendto=sendto
socket.create_connection=blocked
mode,target,*arguments=sys.argv[1:]
sys.argv=[target,*arguments]
if mode=='module':runpy.run_module(target,run_name='__main__')
elif mode=='script':runpy.run_path(target,run_name='__main__')
else:raise ValueError('Entrada offline incompatible')
