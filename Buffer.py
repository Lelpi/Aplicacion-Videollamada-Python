"""
  FICHERO: Buffer.py
  DESCRIPCIÓN: Manejo del buffer circular 
               para almacenar frames
  AUTHORS: luis.lepore@estudiante.uam.es
           oriol.julian@estudiante.uam.es
"""
# Size of the buffer
SIZE = 40

"""
  CLASE: Buffer
  DESCRIPCIÓN: Implementación del buffer circular
  AUTHORS: luis.lepore@estudiante.uam.es
           oriol.julian@estudiante.uam.es
"""
class Buffer(object):

    """
      FUNCIÓN: void __init__()
      DESCRIPCIÓN: Constructor
    """
    def __init__(self):
        self.buff = []
        # Inicializar el buffer a None
        for i in range(0, SIZE):
            self.buff.append(None)

        # Puntero al primer espacio vacío
        self.head = 0
        # Puntero al primer elemento
        self.tail = -1
        # Último ID extraído
        self.lastID = 0
        self.reproduce = False

    """
      FUNCIÓN: void push()
      ARGS_IN: elem - array elemento a introducir, 
               con elem[0]=id
      DESCRIPCIÓN: Introduce elemento en el buffer
    """
    def push(self, elem):
        # Si se ha extraído ya un elemento posterior
        # al llegado se desecha
        if int(elem[0]) < self.lastID:
            return

        self.buff[self.head] = elem
        # Si el buffer está lleno se sobreescribe
        # el primer elemento
        if self.head == self.tail:
            self.tail = (self.tail + 1) % SIZE
        # Si el buffer estaba vacío el
        # último elemento introducido es el primero
        if self.tail == -1:
            self.tail = self.head
        self.head = (self.head + 1) % SIZE
        # Si ya se ha superado 3/4 del tamaño del buffer se podrá hacer pop
        if len(self.buff) > SIZE * 3/4:
            self.reproduce = True

    """
      FUNCIÓN: void pop()
      DESCRIPCIÓN: Extrae un elemento del buffer
      ARGS_OUT: array elemento del buffer
    """
    def pop(self):
        # Si está vacío o no se ha alcanzado el valor óptimo de ocupación no se devuelve nada
        if self.tail == -1 or not self.reproduce:
            return None

        e = self.buff[self.tail]
        self.buff[self.tail] = None
        self.lastID = int(e[0])
        self.tail = (self.tail + 1) % SIZE
        # Si el buffer queda vacío se reinicia el puntero de cola y
        # se espera a que se vuelva a llenar a 3/4 de la ocupación
        if self.tail == self.head:
            self.tail = -1
            self.reproduce = False
        return e
