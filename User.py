"""
  FICHERO: User.py
  DESCRIPCIÓN: Manejo de la funcionalidad asociada al usuario
  AUTHORS: luis.lepore@estudiante.uam.es
           oriol.julian@estudiante.uam.es
"""
import socket

# Puerto para abrir conexión TCP
TCPPORT = 28003

"""
  CLASE: User
  DESCRIPCIÓN: Funcionalidad asociada al usuario
  AUTHORS: luis.lepore@estudiante.uam.es
           oriol.julian@estudiante.uam.es
"""
class User(object):
    """
      FUNCIÓN: void __init__(String nick, String pswd)
      ARGS_IN: nick - Nombre de usuario
               pswd - Contraseña del usuario
      DESCRIPCIÓN: Constructor
    """
    def __init__(self, nick, pswd):
        self.nick=nick

        # Acceso a un servidor cualquiera, para obtener la ip de tu equipo
        s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.ip=s.getsockname()[0]
        s.close()
        
        self.port = TCPPORT
        self.pswd = pswd
        self.version = "V0"

    """
      FUNCIÓN: String[] getUsers(usersString)
      ARGS_IN: usersString - Cadena con los nombres de usuarios 
               y otros datos separados por #
      DESCRIPCIÓN: Transforma la cadena de usuarios pasada 
                   por el servidor en un array de nicks
    """
    def getUsers(self, usersString):
        usersArray = usersString.split('#')
        users = []
        u = usersArray[0].split()
        users.append(u[3])
        for i in range (1,len(usersArray)):
            u = usersArray[i].split()
            users.append(u[0])
        return users
