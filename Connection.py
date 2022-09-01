"""
  FICHERO: Connection.py
  DESCRIPCIÓN: Manejo de la funcionalidad 
               asociada a las llamadas
  AUTHORS: luis.lepore@estudiante.uam.es
           oriol.julian@estudiante.uam.es
"""
import threading
import socket
import cv2
from Buffer import Buffer
import traceback
import time

# Tamaño máximo de la trama UDP
MAX_UDP = 65507
# Puerto del socket UDP de envío
UDPPORTSRC = 28001

"""
  CLASE: Connection
  DESCRIPCIÓN: Implementa sockets e hilos de escucha 
               y envío de información para la llamada
  AUTHORS: luis.lepore@estudiante.uam.es
           oriol.julian@estudiante.uam.es
"""
class Connection(object):

    """
      FUNCIÓN: void __init__(String miNick, String ip, int port, VideoClient vc)
      ARGS_IN: miNick - Nombre del usuario de la máquina
               ip - ip del usuario de la máquina
               port - puerto TCP para abrir conexión con otro usuario
               vc - objeto VideoClient
      DESCRIPCIÓN: Constructor
    """
    def __init__(self, miNick, ip, port, vc):
        self.miNick = miNick
        self.vc = vc

        self.socketUDPsrc = None
        self.socketUDPdst = None

        self.buffer = None
        self.socketTCPdst = None
        # abre el socket de escucha para recibir peticiones de llamadas y lanza el hilo de escucha 
        self.socketTCPsrc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        try:
            self.socketTCPsrc.bind((ip, port))
            self.socketTCPsrc.listen(1)
        except:
            self.socketTCPsrc.close()

        thread = threading.Thread(target=self.listen)
        thread.start()

    """
      FUNCIÓN: void listen()
      DESCRIPCIÓN: Escucha peticiones de llamada de otros usuarios
    """
    def listen(self):
        while True:
            try:
                socketTCPdst, (ipDst, _) = self.socketTCPsrc.accept()
            except:
                break

            recv = socketTCPdst.recv(MAX_UDP).decode().split()
            if self.socketTCPdst is not None:  # si el socket está abierto
                socketTCPdst.send(('CALL_BUSY').encode())
                socketTCPdst.close()
            # comando de llamada
            elif recv[0] == "CALLING":
                self.socketTCPdst = socketTCPdst
                response = self.vc.app.yesNoBox("Llamada entrante", recv[1] + " llamando... ¿Aceptar?")

                if response:
                    # lanzar sockets UDP para enviar y recibir imagen
                    # y TCP para recibir comandos
                    self.openUDPsrc()
                    thread = threading.Thread(target=self.recvVideo)
                    thread.start()
                    self.openUDPdst(ipDst, int(recv[2]))
                    self.socketTCPdst.send(('CALL_ACCEPTED ' + self.miNick + ' ' + str(UDPPORTSRC)).encode())
                    
                    self.vc.call = True
                    self.vc.showLayout()
                    thread = threading.Thread(target=self.controlCommands)
                    thread.start()
                    
                else:
                    # Devuelve denegación si se rechaza la llamada
                    self.socketTCPdst.send(('CALL_DENIED ' + self.miNick).encode())
                    self.socketTCPdst.close()
                    self.socketTCPdst = None

            else:
                self.socketTCPdst.close()
                self.socketTCPdst = None
    
    """
      FUNCIÓN: void call(String ipDst, int portDst)
      ARGS_IN: ipDst - ip del usuario a llamar
               portDst - puerto del usuario a llamar
      DESCRIPCIÓN: Llama a un usuario
    """
    def call(self, ipDst, portDst):
        self.socketTCPdst = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socketTCPdst.connect((ipDst, portDst))
        except:
            self.socketTCPdst.close()
            self.socketTCPdst = None
            return

        # Apertura del socket UDP para recibir imágenes
        self.openUDPsrc()
        thread = threading.Thread(target=self.recvVideo)
        thread.start()
        # Comando de solicitud de llamada
        self.socketTCPdst.send(("CALLING " + self.miNick + " " + str(UDPPORTSRC)).encode())
        recv = self.socketTCPdst.recv(MAX_UDP).decode().split()
        # Si se acepta se lanza UDP de envío de imágenes y el hilo de recepción de comandos
        if recv[0] == "CALL_ACCEPTED":
            self.openUDPdst(ipDst, int(recv[2]))
            self.vc.call = True
            self.vc.showLayout()
            thread = threading.Thread(target=self.controlCommands)
            thread.start()
        # En caso de denegar se cierra conexión TCP y UDP
        elif recv[0] == "CALL_DENIED":
            self.socketTCPdst.close()
            self.socketTCPdst = None
            self.socketUDPsrc.close()
            return
        # En caso de usuario ocupado se cierra conexión TCP y UDP
        elif recv[0] == "CALL_BUSY":
            self.socketTCPdst.close()
            self.socketTCPdst = None
            self.socketUDPsrc.close()
            return
    """
      FUNCIÓN: void end(Boolean pressedButton)
      ARGS_IN: pressedButton - True si se ha seleccionado colgar
                               False si lo seleccionó el otro usuario
      DESCRIPCIÓN: 
    """
    def end(self, pressedButton):
        # Si se colgó mandar comando de finalizar llamada al otro usuario
        if pressedButton is True:
            self.callEnd()

        # Cierre de sockets
        self.socketTCPdst.close()
        self.socketTCPdst = None
        self.socketUDPdst.close()
        self.socketUDPsrc.close()
    
    """
      FUNCIÓN: void controlCommands()
      DESCRIPCIÓN: Recepción de comandos
    """
    def controlCommands(self):
        while True:
            try:
                recv = self.socketTCPdst.recv(MAX_UDP).decode().split()
            except:
                break
            if recv == []:
                break
            
            print('Command pressed: '+recv[0])
            # Pausar llamada
            if recv[0] == "CALL_HOLD":
                self.vc.pause()
            # Continuar llamada
            elif recv[0] == "CALL_RESUME":
                self.vc.resume()
            # Finalizar llamada
            elif recv[0] == "CALL_END":
                self.vc.call = False
                self.end(pressedButton=False)
                self.vc.paused = False
                self.vc.app.setButton("Pausar", "Pausar")
                self.vc.app.enableButton("Pausar")
                self.vc.showLayout()
                break
    """
      FUNCIÓN: void callEnd()
      DESCRIPCIÓN: Comando de finalizar llamada
    """
    def callEnd(self):
        self.socketTCPdst.send(("CALL_END " + self.miNick).encode())

    """
      FUNCIÓN: void callHold()
      DESCRIPCIÓN: Comando de pausar llamada
    """
    def callHold(self):
        self.socketTCPdst.send(("CALL_HOLD " + self.miNick).encode())

    """
      FUNCIÓN: void callResume()
      DESCRIPCIÓN: Comando de continuar llamada
    """
    def callResume(self):
        self.socketTCPdst.send(("CALL_RESUME " + self.miNick).encode())

    """
      FUNCIÓN: void sendVideo()
      DESCRIPCIÓN: Envía imagen al otro usuario
    """
    def sendVideo(self, frame):
        
        #Codificación de la  imagen
        encode_param = [cv2.IMWRITE_JPEG_QUALITY, 50]
        result, encimg = cv2.imencode('.jpg', frame, encode_param)
        if result == False: print('Error al codificar imagen')
        encimg = encimg.tobytes()
        
        # Añadir datos relativos a la imagen
        self.idFrame += 1
        self.framesInSecond += 1
        actTime = time.time()
        if actTime - self.lastTime >= 1:
            self.FPS = self.framesInSecond
            self.framesInSecond = 0
            self.lastTime = actTime
        
        params = str(self.idFrame)+'#'+str(actTime)+'#640x480#'+str(self.FPS)+'#'
        datagram = b''.join([params.encode(), encimg])
        
        self.socketUDPdst.send(datagram)

    """
      FUNCIÓN: void recvVideo()
      DESCRIPCIÓN: recepción de imagenes del otro usuario
    """
    def recvVideo(self):
        i=0
        while True:
            try:
                recv = self.socketUDPsrc.recv(MAX_UDP).split(b'#', 4)
            except Exception:
                break
            # Si se cierra el socket se finaliza el programa
            if recv == []:
                break
            # Construcción del array elemento para insertar en el buffer
            recv = [recv[0].decode(), recv[1].decode(), recv[2].decode(), recv[3].decode(), recv[-1]]
            self.buffer.push(recv)

    """
      FUNCIÓN: void openUDPsrc()
      DESCRIPCIÓN: Apertura del socket UDP de recepción de video
    """
    def openUDPsrc(self):
        self.buffer = Buffer()
        self.socketUDPsrc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.socketUDPsrc.bind((self.ip, UDPPORTSRC))
        except:
            self.socketUDPsrc.close()

    """
      FUNCIÓN: void openUDPdst()
      DESCRIPCIÓN: Apertura del socket UDP de envío de video
    """
    def openUDPdst(self, ip, port):
        # Inicialización de parámetros de las imágenes
        self.idFrame = 0
        self.framesInSecond = 0
        self.FPS = 50
        self.lastTime = time.time()
        self.socketUDPdst = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.socketUDPdst.connect((ip, port))
        except:
            print('Error contactando con el otro usuario')
