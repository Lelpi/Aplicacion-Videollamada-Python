"""
  FICHERO: Server.py
  DESCRIPCIÓN: Acceso al servidor de descubrimiento
  AUTHORS: luis.lepore@estudiante.uam.es
           oriol.julian@estudiante.uam.es
"""
import socket

SERVER_URL = "vega.ii.uam.es"

# Tamaño máximo del paquete TCP recibido del servidor
MAX_BUFF = 4096

"""
  CLASE: Server
  DESCRIPCIÓN: Acceso al servidor de descubrimiento
  AUTHORS: luis.lepore@estudiante.uam.es
           oriol.julian@estudiante.uam.es
"""
class Server():
    
    """
      FUNCIÓN: void __init__(string user)
      ARGS_IN: user - nombre del usuario
      DESCRIPCIÓN: Constructor
    """
    def __init__(self, user):
        self.user = user
    
    """
      FUNCIÓN: int connect()
      DESCRIPCIÓN: Establece la conexión TCP con el servidor
      ARGS_OUT: -1 si hay error, 0 en otro caso
    """
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.socket.connect((SERVER_URL, 8000))
        except:
            return -1
        return 0

    """
      FUNCIÓN: void disconnect()
      DESCRIPCIÓN: Cierra la conexión TCP con el servidor
    """
    def disconnect(self):
        # Comando de cierre
        self.send("QUIT")
        self.socket.close()

    """
      FUNCIÓN: void send(string message)
      ARGS_IN: message - string del mensaje
      DESCRIPCIÓN: Envía trama TCP al servidor
    """
    def send(self, message):
        self.socket.send(message.encode())

    """
      FUNCIÓN: String receive(size)
      ARGS_IN: size - tamaño máximo de la trama a recibir
      DESCRIPCIÓN: Recibe trama TCP del servidor
      ARGS_OUT: string del mensaje
    """
    def receive(self, size=MAX_BUFF):
        return self.socket.recv(size).decode()

    """
      FUNCIÓN: Boolean register()
      DESCRIPCIÓN: Manda petición de registro al servidor
      ARGS_OUT: True si se ha registrado al usuario, 
                False en otro caso
    """
    def register(self):
        self.connect()

        # Comando de registro
        self.send("REGISTER " +
                  self.user.nick + " " +
                  self.user.ip + " " +
                  str(self.user.port) + " " +
                  self.user.pswd + " " +
                  self.user.version)
        ret = self.receive()
        self.disconnect()

        if ret == "NOK WRONG_PASS":
            return False
        else:
            return True

    """
      FUNCIÓN: (string, string, []) connectToUser(String nick)
      ARGS_IN: nick - nombre del usuario consultado
      DESCRIPCIÓN: Pregunta al servidor por la dirección de 
                   un usuario
      ARGS_OUT: Tupla con: 
                la ip del usuario, 
                el puerto a conectar, 
                los protocolos admitidos
    """
    def connectToUser(self, nick):
        self.connect()
        # Comando de consulta
        self.send("QUERY "+nick)
        nickInfo = self.receive()
        self.disconnect()
        
        # Si el servidor devuelve error se devuelve una tupla vacía
        if nickInfo == "NOK USER_UNKNOWN":
            return "", "", []
        info = nickInfo.split()
        # IP, Port, Protocols[]
        return info[3], int(info[4]), info[5].split('#')
