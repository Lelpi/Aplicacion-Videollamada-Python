"""
  FICHERO: practica3_client.py
  DESCRIPCIÓN: Manejo general de la aplicación
  AUTHORS: luis.lepore@estudiante.uam.es
           oriol.julian@estudiante.uam.es
           profesores EPS
"""
from appJar import gui
from PIL import Image, ImageTk
import numpy as np
import cv2
from User import User
from Server import Server
from Connection import Connection

"""
  FICHERO: VideoClient
  DESCRIPCIÓN: Manejo general de la aplicación
  AUTHORS: luis.lepore@estudiante.uam.es
           oriol.julian@estudiante.uam.es
           profesores EPS
"""
class VideoClient(object):
    """
      FUNCIÓN: void __init__(String window_size)
      ARGS_IN: window_size - tamaño inicial de la ventana
      DESCRIPCIÓN: Constructor
    """
    def __init__(self, window_size):

        # Creamos una variable que contenga el GUI principal
        self.app = gui("Redes2 - P2P", window_size)
        self.app.setGuiPadding(10,10)

        # Inicialización de flags de control
        self.nick = ""
        self.call = False
        self.paused = False
        self.connection = None
        # Inicialización del layout
        self.app.addLabel("title", "Cliente Multimedia P2P - Redes2 - " + self.nick)
        self.app.addImage("video", "imgs/webcam.gif")
        self.app.addButtons(["Conectar", "Colgar", "Listar usuarios", "Pausar", "Salir"], self.buttonsCallback)
        self.showLayout()
        self.app.addStatusbar(fields=2)

        # Registramos la función de captura de video
        # Esta misma función también sirve para enviar un vídeo
        self.cap = cv2.VideoCapture(0)
        self.app.setPollTime(20)
        self.app.registerEvent(self.capturaVideo)

        # Creación de subventana inicial de registro
        self.app.startSubWindow("Registro")
        self.app.setSticky("e")
        self.app.setSize(300, 150)
        self.app.setPadding([20,0])
        self.app.addLabelEntry("Nick:")
        self.app.addLabelSecretEntry("Password:")
        self.app.addButton("Submit", self.press)
        self.app.stopSubWindow()

        # Creación de subventana de selección de usuarios a llamar
        self.app.startSubWindow("Usuarios")
        self.app.addListBox("listaUsuarios", [])
        self.app.setPadding([2, 2])
        self.app.addButton("Llamar", self.buttonsCallback)
        self.app.stopSubWindow()

    """
      FUNCIÓN: void start()
      DESCRIPCIÓN: Lanzamiento de la aplicación
    """
    def start(self):
        self.app.go(startWindow="Registro")

    """
      FUNCIÓN: void capturaVideo()
      DESCRIPCIÓN: Función que captura el frame a mostrar y enviar en cada momento
    """
    def capturaVideo(self):
        # Si llamada pausada no se actualiza la imagen y
        # no se muestran parámetros en la statusbar
        if self.paused is True:
            self.app.setStatusbar("FPS: -", field=0)
            self.app.setStatusbar("Resolución: -", field=1)
            return

        # Capturamos un frame de la cámara o del vídeo
        ret, frame = self.cap.read()

        if self.call is False:
            frame_compuesto = cv2.resize(frame, (640,480))
        else:
            # Creación del frame compuesto y envío de imagen
            self.connection.sendVideo(frame)
            frame_peque = cv2.resize(frame, (160, 120))  # ajustar tamaño de la imagen pequeña
            recvData = self.connection.buffer.pop()
            if recvData is None:
                return
            else:
                # Descompresión de los datos, una vez recibidos
                decimg = cv2.imdecode(np.frombuffer(recvData[-1],np.uint8), 1)
                frame_compuesto = cv2.resize(decimg, (640,480))
                self.app.setStatusbar("FPS: " + recvData[3], field=0)
                self.app.setStatusbar("Resolución: " + recvData[2], field=1)
                frame_compuesto[0:frame_peque.shape[0], 0:frame_peque.shape[1]] = frame_peque

        cv2_im = cv2.cvtColor(frame_compuesto, cv2.COLOR_BGR2RGB)
        img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))

        # Lo mostramos en el GUI
        self.app.setImageData("video", img_tk, fmt = 'PhotoImage')

    """
      FUNCIÓN: void setImageResolution()
      DESCRIPCIÓN: Establece la resolución de la imagen capturada
    """
    def setImageResolution(self, resolution):        
        # Se establece la resolución de captura de la webcam
        # Puede añadirse algún valor superior si la cámara lo permite
        # pero no modificar estos
        if resolution == "LOW":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160) 
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120) 
        elif resolution == "MEDIUM":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320) 
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240) 
        elif resolution == "HIGH":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640) 
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) 

    """
      FUNCIÓN: void buttonsCallback(String button)
      ARGS_IN: button - nombre del botón pulsado
      DESCRIPCIÓN: Función que gestiona los callbacks de los botones
    """
    def buttonsCallback(self, button):

        if button == "Salir":
            # Salimos de la aplicación
            if self.call is True:
                self.call = False
                self.connection.end(pressedButton=True)
            self.connection.socketTCPsrc.close()
            self.app.stop()
        elif button == "Conectar":
            # Entrada del nick del usuario a conectar
            nick = self.app.textBox("Conexión", "Introduce el nick del usuario a buscar")
            if nick is None:
                return
            ip, port, versions = self.server.connectToUser(nick)
            if ip == "":
                self.app.warningBox("Error", "El usuario "+nick+" no existe.")
                return
            
            self.connection.call(ip, port)
        elif button == "Listar usuarios":
            # Mostrar subventana con usuarios del servidor
            self.server.connect()
            self.server.send("LIST_USERS")
            users = self.server.receive()
            usersArray = self.user.getUsers(users)

            self.app.clearListBox("listaUsuarios", callFunction=False)
            self.app.addListItems("listaUsuarios", usersArray)
            self.app.showSubWindow("Usuarios")
        elif button == "Llamar":
            # Llamada desde la subventana con usuarios
            nick = self.app.getListBox("listaUsuarios")
            self.app.hideSubWindow("Usuarios")
            if nick is None or len(nick) != 1:
                return
            # Obtención de datos del usuario a llamar
            ip, port, versions = self.server.connectToUser(nick[0])
            print('nick: '+nick[0])
            if ip == "":
                self.app.warningBox("Error", "El usuario "+nick[0]+" no existe.")
                return
            
            self.connection.call(ip, port)
        elif button == "Colgar":
            # Reinicio de flags de llamada y finalización de la misma
            self.call = False
            self.paused = False
            self.app.setButton("Pausar", "Pausar")
            self.app.enableButton("Pausar")
            self.showLayout()
            self.connection.end(pressedButton=True)
        elif button == "Pausar":
            # Pausar o continuar y actualizar botones
            if self.paused:
                self.connection.callResume()
                self.app.setButton("Pausar", "Pausar")
            else:
                self.connection.callHold()
                self.app.setButton("Pausar", "Reanudar")
            self.paused = not self.paused

    """
      FUNCIÓN: void press()
      DESCRIPCIÓN: Lanzamiento de aplicación tras el registro
    """
    def press(self):
        self.app.hideSubWindow("Registro")
        self.app.show()
        self.nick = self.app.getEntry("Nick:")
        pswd = self.app.getEntry("Password:")
        # Si no se introducen datos error
        if self.nick == "" or pswd == "":
            self.app.warningBox("Error", "Usuario o clave incorrectos")
            self.app.stop()
            return
        self.user = User(self.nick, pswd)
        self.server = Server(self.user)
        # Si el servidor da error se lanza mensaje de error
        if self.server.register() is False:
            self.app.warningBox("Error", "Usuario o clave incorrectos")
            self.app.stop()
            return
        # En otro caso se lanza un objeto connection y se lanza la aplicación
        self.connection = Connection(self.user.nick, self.user.ip, self.user.port, self)
        self.app.setLabel("title", "Cliente Multimedia P2P - Redes2 - " + self.nick)

    """
      FUNCIÓN: void showLayout()
      DESCRIPCIÓN: Actualización del layout de la interfaz
    """
    def showLayout(self):
        if self.call is True:
            self.app.hideButton("Conectar")
            self.app.hideButton("Listar usuarios")
            self.app.showButton("Colgar")
            self.app.showButton("Pausar")
        else:
            self.app.setStatusbar("", field=0)
            self.app.setStatusbar("", field=1)
            self.app.hideButton("Colgar")
            self.app.hideButton("Pausar")
            self.app.showButton("Conectar")
            self.app.showButton("Listar usuarios")

    """
      FUNCIÓN: void pause()
      DESCRIPCIÓN: Inhabilitación de pausar llamada, cuando lo hace el otro usuario
    """
    def pause(self):
        # Mostrar mensaje de llamada pausada
        self.app.infoBox("Llamada pausada", "Llamada pausada")
        self.app.setLabel("title", "Cliente Multimedia P2P - Redes2 - " + self.nick + " Llamada en pausa")
        # Actualización de flag de pausa
        self.paused = True
        self.app.disableButton("Pausar")

    """
      FUNCIÓN: void resume()
      DESCRIPCIÓN: Habilitación de pausar llamada, cuando el otro usuario 
                   continúa la llamada
    """
    def resume(self):
        # Mostrar mensaje de llamada reanudada
        self.app.infoBox("Llamada reanudada", "Llamada reanudada")
        self.app.setLabel("title", "Cliente Multimedia P2P - Redes2 - " + self.nick)
        # Actualización de flag de pausa
        self.paused = False
        self.app.enableButton("Pausar")

def main():
    vc = VideoClient("640x520")

    vc.start()


if __name__ == '__main__':
    main()
