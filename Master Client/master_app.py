from os import system, name
import requests
from datetime import datetime

#----------------------------------------------------- Variables globales -----------------------------------------------------

base_url = "http://127.0.0.1:5000" # Cambia la url por la de tu servidor

username = "any_username" # Esta variable guarda el nombre de usuario.
name = "any_name" # Esta variable guarda el nombre del paciente o doctor associado al usuario.
role = "any_role" # Esta variable guarda el rol del usuario para determinar la interfaz que necesitaras. 
token = "" # Esta variable guarda el token de acceso al servidor.

#----------------------------------------------------------- Gestion ----------------------------------------------------------

def login(username, password):
    """
    Esta funcion envia el usuario y la contraseña al servidor para verificar tu identidad y recibir un token de acceso.

    Args:
        username: Nombre de usuario
        password: Contraseña del usuario

    Returns:
        Diccionario:
            "token": Un codigo encriptado que te da acceso al servidor.
            "expires_at": Fecha en la que expira el token de acceso.
            "role": Role del usuario, usado para definir la interfaz que necesitaras.
        None: Algo ha fallado.
    """
    try:
        response = requests.post(base_url + "/auth/login/", data={"username": username, "password": password})

        if response.status_code == 200:
            return response.json()
        
        return None
    except Exception:
        return None
    
def get_users(role: str|None = None):
    """
    Esta funcion pide al servidor que le envie todos los usuarios de la base de datos.

    Args:
        role - Opcional: El rol que quieres que el servidor filtre.

    Returns:
        users: Listado de usuarios devueltos por el servidor.
        user: Usuario devuelto por el servidor.
        None: Algo ha fallado.
    """
    try:
        headers = {
            'Authorization': "Bearer " + token
        }

        params = {}

        if role != "" and role is not None:
            params["role"] = role

        response = requests.get(base_url + "/api/user/", params=params, headers=headers)

        if response.status_code == 200:
            return response.json()
        
        return None
    except Exception:
        return None
    
def get_user_by_username(username):
    """
    Esta funcion pide al servidor que le envie un usuario especifico en la base de datos.

    Args:
        username: El nombre de usuario que identifica al usuario que quieres que te envie el servidor.

    Returns:
        user: Usuario devuelto por el servidor.
        None: Algo ha fallado.
    """
    try:
        headers = {
            'Authorization': "Bearer " + token
        }

        response = requests.get(base_url + "/api/user/username/" + str(username), headers=headers)

        if response.status_code == 200:
            return response.json()
        
        return None
    except Exception:
        return None

#------------------------------------------------------------- HUB ------------------------------------------------------------

class colors:
    """
    Codigos de colores para la interfaz grafica.
    """
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

def start_program():
    """
    Esta es la primera funcion que se ejecuta. Muestra la pantalla de inicio de session.
    Si el inicio de session se cumple con exito, te redirije a la funcion "main_menu()".
    """
    global username
    global name
    global role
    global token
    username = "admin"
    password = "admin"
    data = login(username, password)
    if data is not None:
        role = data["role"]
        token = data["token"]

        list_users()

    '''while True:
        clear_terminal()
        print("-"*100)
        print("Bienvenido/a a Odontocare!")
        print("Por favor, inicie session para continuar.")
        print("-"*100)
        username = input("Nombre de usuario: ")
        password = input("Contraseña: ")
        data = login(username, password)
        if data is not None:
            role = data["role"]
            token = data["token"]

            if role == "patient" or role == "doctor" or role == "secretary":
                user = get_users()
            else:
                user = get_user_by_username(username)

            if user["patient_name"] is not None:
                name = user["patient_name"]
            elif user["doctor_name"] is not None:
                name = user["doctor_name"]
            else:
                name = username

            main_menu()
            break
        error_message("El nombre de usuario o la contraseña no coinciden.")'''

def list_users():
    """
    Esta funcion te permite ver un listado de usuarios.
    Tambien puede filtrar los usuarios por rol.
    Funcion exclusiva del rol administrador.
    """
    users = get_users()

    clear_terminal()
    print("-"*100)
    for user in users:
        print(f"ID: {user["id"]}")
        print(f"Nombre de usuario: {user["username"]}")
        if user["role"] == "admin":
            print(f"Rol: Admin")
        elif user["role"] == "customer":
            print(f"Rol: Cliente")
        print("-"*100)
    input(f"Presiona \"ENTER\" para continuar...")

def success_message(message):
    """
    Esta funcion se encarga de procesar los mensajes de exito en la pantalla.
    """
    print(colors.GREEN)
    clear_terminal()
    print(message)
    input(f"Presiona \"ENTER\" para continuar...")
    print(colors.WHITE)

def error_message(error):
    """
    Esta funcion se encarga de procesar los mensajes de error en la pantalla.
    """
    print(colors.RED)
    clear_terminal()
    print(f"Error: " + error)
    input(f"Presiona \"ENTER\" para continuar...")
    print(colors.WHITE)

def clear_terminal():
    """
    Esta funcion se encarga de limpiar la terminal. Sirve para tener la interfaz limpia.
    """
    if name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')

start_program()
