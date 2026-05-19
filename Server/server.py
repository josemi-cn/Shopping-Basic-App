from os import system, name
import json
import jwt
import datetime
from functools import wraps
from flask import Flask, jsonify, request, abort, Blueprint, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from jsonschema import validate, ValidationError
import pandas as pd
from pathlib import Path
import sqlite3

db = SQLAlchemy()

JWT_SECRET_KEY = "clave_secreta_jwt_para_firmar_tokens"
JWT_EXPIRATION_DELTA = datetime.timedelta(hours=1)

#------------------------------------------------------------ Clases ----------------------------------------------------------

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

class User(db.Model):
    """
    Hola
    """
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)
    commands = db.relationship("Command", backref="users")

    def to_dict(self):
        """Convierte el usuario a un diccionario para la respuesta JSON"""
        return {
            "id": self.id, 
            "username": self.username,
            "password": self.password,
            "name": self.name, 
            "role": self.role
            }
        
    def get_data(self):
        return {
            "id": self.id, 
            "username": self.username,
            "password": self.password,
            "name": self.name, 
            "role": self.role
            }

class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    image = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def to_dict(self):
        """Convierte el doctor a un diccionario para la respuesta JSON"""
        return {
            "id": self.id, 
            "image": self.image, 
            "name": self.name, 
            "price": self.price
            }
    
    def get_data(self):
        return {
            "id": self.id, 
            "image": self.image, 
            "name": self.name, 
            "price": self.price
            }
    
command_product = db.Table('command_product',
    db.Column('command_id', db.Integer, db.ForeignKey('commands.id')),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'))
    )

class Command(db.Model):
    __tablename__ = "commands"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    products = db.relationship('Product', secondary=command_product, backref='commands')
    ready = db.Column(db.Boolean, nullable=False)
    delivering = db.Column(db.Boolean, nullable=False)
    delivered = db.Column(db.Boolean, nullable=False)

    def to_dict(self):
        """Convierte el centro a un diccionario para la respuesta JSON"""
        array_products = []
        for product in self.products:
            array_products.append(product.to_dict())
        return {
            "id": self.id, 
            "user_id": self.user_id, 
            "products": array_products,
            "ready": self.ready, 
            "delivering": self.delivering, 
            "delivered": self.delivered
            }

    def get_data(self):
        """Convierte el centro a un diccionario para la respuesta JSON"""
        return {
            "id": self.id, 
            "user_id": self.user_id, 
            "ready": self.ready, 
            "delivering": self.delivering, 
            "delivered": self.delivered
            }
    
#----------------------------------------------------- Persistencia de datos --------------------------------------------------

databaseFile = "database.db"

def createDatabase(user : User):
    """
    Creates the database file with SQLite, with all the tables and the default admin user.
    """
    conn = sqlite3.connect(databaseFile)

    conn.execute('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        name TEXT,
        role TEXT
    );
    ''')

    conn.execute(f"INSERT INTO users VALUES ({user.id},\"{user.username}\",\"{user.password}\",\"{user.name}\",\"{user.role}\");")

    conn.commit()

    conn.execute('''
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image TEXT,
        name TEXT,
        price FLOAT
    );
    ''')

    conn.commit()
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS commands(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        ready BOOLEAN,
        delivering BOOLEAN,
        delivered BOOLEAN,
        FOREIGN KEY(user_id) REFERENCES user(id)
    );
    ''')
    
    conn.commit()
    conn.close()

def loadUsers():
    """
    Carga los usuarios almacenados en su respectivo archivo CSV y los guarda en la base de datos interna.
    """
    conn = sqlite3.connect(databaseFile)

    cursor = conn.execute("SELECT * FROM users;")
    for i in cursor:
        user = User(
            id=i[0],
            username=i[1],
            password=i[2],
            name=i[3],
            role=i[4]
        )
        db.session.add(user)
        db.session.commit()

    conn.close()

def addUser(user : User):
    """
    Carga los usuarios almacenados en la base de datos interna y los guarda en su respectivo archivo CSV.
    """
    conn = sqlite3.connect(databaseFile)
    conn.execute(f"INSERT INTO users VALUES ({user.id},\"{user.username}\",\"{user.password}\",\"{user.name}\",\"{user.role}\");")

    conn.commit()
    conn.close()

def updateUser(user : User):
    """
    Carga los usuarios almacenados en la base de datos interna y los guarda en su respectivo archivo CSV.
    """
    conn = sqlite3.connect(databaseFile)
    
    conn.execute(f"""
        UPDATE users
        SET username = \"{user.username}\",
        password = \"{user.password}\",
        name = \"{user.name}\",
        role = \"{user.role}\"
        WHERE id = {user.id};
    """)

    conn.commit()
    conn.close()

def deleteUser(user : User):
    """
    Carga los usuarios almacenados en la base de datos interna y los guarda en su respectivo archivo CSV.
    """
    conn = sqlite3.connect(databaseFile)
    
    conn.execute(f"DELETE FROM users WHERE id = {user.id};")

    conn.commit()
    conn.close()

def loadProducts():
    """
    Carga los productos almacenados en su respectivo archivo CSV y los guarda en la base de datos interna.
    """
    conn = sqlite3.connect(databaseFile)

    cursor = conn.execute("SELECT * FROM products;")
    for i in cursor:
        product = Product(
            id=i[0],
            image=i[1],
            name=i[2],
            price=i[3]
        )
        db.session.add(product)
        db.session.commit()

    conn.close()

def addProduct(product : Product):
    """
    Carga los productos almacenados en la base de datos interna y los guarda en su respectivo archivo CSV.
    """
    conn = sqlite3.connect(databaseFile)
    conn.execute(f"INSERT INTO products VALUES ({product.id},\"{product.image}\",\"{product.name}\",{product.price});")

    conn.commit()
    conn.close()

def updateProduct(product : Product):
    """
    Carga los productos almacenados en la base de datos interna y los guarda en su respectivo archivo CSV.
    """
    conn = sqlite3.connect(databaseFile)
    
    conn.execute(f"""
        UPDATE products
        SET image = \"{product.image}\",
        name = \"{product.name}\",
        price = {product.price}
        WHERE id = {product.id};
    """)

    conn.commit()
    conn.close()

def deleteProduct(product : Product):
    """
    Carga los productos almacenados en la base de datos interna y los guarda en su respectivo archivo CSV.
    """
    conn = sqlite3.connect(databaseFile)
    
    conn.execute(f"DELETE FROM products WHERE id = {product.id};")

    conn.commit()
    conn.close()

def loadCommands():
    """
    Carga los pedidos almacenados en su respectivo archivo CSV y los guarda en la base de datos interna.
    """
    conn = sqlite3.connect(databaseFile)

    cursor = conn.execute("SELECT * FROM commands;")
    for i in cursor:
        command = Command(
            id=i[0],
            user_id=i[1],
            name=i[2],
            ready=i[3],
            delivering=i[4],
            delivered=i[5]
        )
        db.session.add(command)
        db.session.commit()

    conn.close()

def addCommand(command : Command):
    """
    Carga los pedidos almacenados en la base de datos interna y los guarda en su respectivo archivo CSV.
    """
    conn = sqlite3.connect(databaseFile)
    conn.execute(f"INSERT INTO commands VALUES ({command.id},\"{command.user_id}\",{command.ready},{command.delivering},{command.delivered});")

    conn.commit()
    conn.close()

def updateCommand(command : Command):
    """
    Carga los pedidos almacenados en la base de datos interna y los guarda en su respectivo archivo CSV.
    """
    conn = sqlite3.connect(databaseFile)
    
    conn.execute(f"""
        UPDATE commands
        SET user_id = \"{command.user_id}\",
        ready = {command.ready},
        delivering = {command.delivering},
        delivered = {command.delivered}
        WHERE id = {command.id};
    """)

    conn.commit()
    conn.close()

def deleteCommand(command : Command):
    """
    Carga los pedidos almacenados en la base de datos interna y los guarda en su respectivo archivo CSV.
    """
    conn = sqlite3.connect(databaseFile)
    
    conn.execute(f"DELETE FROM commands WHERE id = {command.id};")

    conn.commit()
    conn.close()

#-------------------------------------------------------- Autentificacion -----------------------------------------------------

def generate_jwt_token(username):
    """
    Genera un token JWT para un usuario

    Args:
        username: Nombre de usuario

    Returns:
        str: Token JWT generado
    """
    # TODO: Implementa este método para generar un token JWT usando la biblioteca PyJWT
    # El token debe incluir:
    # - 'sub' (subject): username
    # - 'iat' (issued at): Tiempo de emisión
    # - 'exp' (expiration): Tiempo de expiración
    # Usa JWT_SECRET_KEY para firmar el token
    now = datetime.datetime.utcnow()
    expiration = now + JWT_EXPIRATION_DELTA

    payload = {
        'sub': username,
        'iat': now,
        'exp': expiration
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

def jwt_required(func):
    """
    Decorador que verifica la autenticación mediante token JWT

    Para usar este decorador, añade @jwt_required a las funciones que requieran autenticación.
    El token debe enviarse en la cabecera 'Authorization' con formato: 'Bearer TOKEN'

    Args:
        func: Función a decorar

    Returns:
        Function: Función decorada con verificación de autenticación JWT
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # TODO: Implementa la lógica del decorador según las instrucciones
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Token no proporcionado"}), 401
        
        try:
            auth_type, token = auth_header.split(" ")
            if auth_type.lower() != "bearer":
                return jsonify({"error": "Formato de autorizacion invalido"}), 401
            
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms="HS256")

            return func(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token invalido"}), 401
        except (jwt.InvalidTokenError, ValueError):
            return jsonify({"error": "Token invalido"}), 401
    return decorated_function
        
def requires_role(role_required):
    """
    Decorador que verifica la autenticación mediante token JWT e identifica su rol para limitar el acceso a ciertas funciones.

    Para usar este decorador, añade @requires_role a las funciones que requieran autenticación, junto con un listado de los roles con derecho a acceder a la funcion.
    
    El token debe enviarse en la cabecera 'Authorization' con formato: 'Bearer TOKEN'

    Args:
        func: Función a decorar

    Returns:
        Function: Función decorada con verificación de autenticación JWT
    """
    def decorador_interno(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'mensaje': 'Token no proporcionado'}), 401
            
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
                username = payload['sub']
                
                user = get_user_internal(username).get_json()

                user_role = user['role']
                if user_role not in role_required:
                    return jsonify({'mensaje': 'Permiso denegado'}), 403

            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                return jsonify({'mensaje': 'Token inválido'}), 401

            return f(*args, **kwargs)
        return wrapper
    return decorador_interno

#----------------------------------------------------- Funciones adicionales --------------------------------------------------

def get_users_internal():
    """
    Devuelve un listado de todos los usuarios.

    Returns:
        users: Listado de usuarios
    """
    try:
        users = User.query.all()
        return jsonify([u.to_dict() for u in users])
    except Exception as e:
        print(e)
        return jsonify({"error": "No hay usuarios en la base de datos."})
            
def get_user_internal(username):
    """
    Devuelve un usuario identificado por su nombre de usuario.

    Args:
        username: Nombre de usuario

    Returns:
        user: Usuario deseado
    """
    try:
        user = next((u for u in get_users_internal().get_json() if u["username"] == username), None)
        if user is None:
            return jsonify({"error": "Ese usuario no está en la base de datos."})
        return jsonify(user)
    except Exception as e:
        print(e)
        return jsonify({"error": "Ese usuario no está en la base de datos."})

def clear_terminal():
    """
    Esta funcion se encarga de limpiar la terminal. Sirve para tener la interfaz limpia.
    """
    if name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')

#------------------------------------------------------- Aplicación Flask -----------------------------------------------------

def create_app():
    """
    Crea y configura la aplicación Flask
    """
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    bcrypt = Bcrypt(app)
    
    with app.app_context():
        db.create_all()
        print(f"Starting server... " + colors.GREEN + "Completed." + colors.WHITE)

        if Path(databaseFile).exists():
            print(f"Loading database..." + colors.GREEN + "Completed." + colors.WHITE)
            loadUsers()
            print(f"\tLoading users... " + colors.GREEN + "Completed." + colors.WHITE)
            loadProducts()
            print(f"\tLoading products... " + colors.GREEN + "Completed." + colors.WHITE)
            loadCommands()
            print(f"\tLoading commands... " + colors.GREEN + "Completed." + colors.WHITE)
        else:
            print(f"Loading database..." + colors.RED + "Error: Database was not found." + colors.WHITE)

            user = User(
                username="admin",
                password=bcrypt.generate_password_hash('admin').decode('utf-8'),
                name="Administrador",
                role="admin"
            )
            db.session.add(user)
            db.session.commit()

            createDatabase(user)
            print(f"Creating database... " + colors.GREEN + "Completed." + colors.WHITE)
            
            print(f"\tAdministrator user was created, providing login credentials:")
            print(f"\t\tUsername: admin")
            print(f"\t\tPassword: admin")
            print(f"\tChanging the login credentials of the provided user is adviced.")

            """
            user = User(
                username="admin",
                password=bcrypt.generate_password_hash('admin').decode('utf-8'),
                name="Administrador",
                role="admin"
            )
            db.session.add(user)
            db.session.commit()

            print(f"\tCreando producto... " + colors.GREEN + "Completado." + colors.WHITE)
            product1 = Product(
                image = "",
                name = "",
                price = 10.9
            )
            print(f"\tCreando producto... " + colors.GREEN + "Completado." + colors.WHITE)
            product2 = Product(
                image = "",
                name = "",
                price = 11.9
            )
            db.session.add_all([product1, product2])
            db.session.commit()

            print(f"\tCreando pedido... " + colors.GREEN + "Completado." + colors.WHITE)
            command1 = Command(
                user_id=1,
                ready=False,
                delivering=False,
                delivered=False
            )
            print(f"\tCreando pedido... " + colors.GREEN + "Completado." + colors.WHITE)
            command2 = Command(
                user_id=1,
                ready=False,
                delivering=False,
                delivered=False
            )
            command1.products.append(product1)
            command1.products.append(product2)
            command2.products.append(product2)
            db.session.add(command1)
            db.session.add(command2)
            db.session.commit()
            """
        
        """
        db.create_all()
        print(f"Cargando archivos de datos...")

        if Path(usersPath).exists():
            print(f"\tCargando usuarios... " + colors.GREEN + "Completado." + colors.WHITE)
            loadUsers()
        else:
            print(f"\tCargando usuarios... " + colors.RED + "Error." + colors.WHITE)
                    
            print(f"\tCreando usuario de administracion... " + colors.GREEN + "Completado." + colors.WHITE)
            user = User(
                username="admin",
                password=bcrypt.generate_password_hash('admin').decode('utf-8'),
                role="admin"
            )
            db.session.add(user)
            db.session.commit()

            saveUsers()

        if Path(patientsPath).exists():
            print(f"\tCargando pacientes... " + colors.GREEN + "Completado." + colors.WHITE)
            loadPatients()
        else:
            print(f"\tCargando pacientes... " + colors.RED + "Error." + colors.WHITE)

        if Path(doctorsPath).exists():
            print(f"\tCargando doctores... " + colors.GREEN + "Completado." + colors.WHITE)
            loadDoctors()
        else:
            print(f"\tCargando doctores... " + colors.RED + "Error." + colors.WHITE)

        if Path(centersPath).exists():
            print(f"\tCargando centros... " + colors.GREEN + "Completado." + colors.WHITE)
            loadCenters()
        else:
            print(f"\tCargando centros... " + colors.RED + "Error." + colors.WHITE)

        if Path(appointmentsPath).exists():
            print(f"\tCargando citas... " + colors.GREEN + "Completado." + colors.WHITE)
            loadAppointments()
        else:
            print(f"\tCargando citas... " + colors.RED + "Error." + colors.WHITE)
                

        if Path(patientsPath).exists() == False and Path(doctorsPath).exists() == False and Path(centersPath).exists() == False and Path(appointmentsPath).exists() == False:
            while True:
                option = input("Desea crear datos de prueba? (S/N) ")
                if option.upper() == "S" or option.upper() == "N":
                    if option.upper() == "S":
                        print(f"\tCreando usuario \"paciente1\"... " + colors.GREEN + "Completado." + colors.WHITE)
                        user = User(
                            username="paciente1",
                            password=bcrypt.generate_password_hash('paciente1').decode('utf-8'),
                            role ="patient"
                        )
                        db.session.add(user)
                        db.session.commit()

                        print(f"\tCreando paciente \"José Miguel Calahuche\"... " + colors.GREEN + "Completado." + colors.WHITE)
                        patient = Patient(
                            user_id=2,
                            name="José Miguel Calahuche",
                            phone_number="627456743",
                            state="ACTIVE"
                        )
                        db.session.add(patient)
                        db.session.commit()
                        
                        print(f"\tCreando usuario \"paciente2\"... " + colors.GREEN + "Completado." + colors.WHITE)
                        user = User(
                            username="paciente2",
                            password=bcrypt.generate_password_hash('paciente2').decode('utf-8'),
                            role="patient"
                        )
                        db.session.add(user)
                        db.session.commit()
                        
                        print(f"\tCreando paciente \"José Miguel Calahuche\"... " + colors.GREEN + "Completado." + colors.WHITE)
                        patient = Patient(
                            user_id=3,
                            name="Rosa Perez",
                            phone_number="645342123",
                            state="INACTIVE"
                        )
                        db.session.add(patient)
                        db.session.commit()

                        print(f"\tCreando usuario \"paciente3\"... " + colors.GREEN + "Completado." + colors.WHITE)
                        user = User(
                            username="paciente3",
                            password=bcrypt.generate_password_hash('paciente3').decode('utf-8'),
                            role="patient"
                        )
                        db.session.add(user)
                        db.session.commit()
                        
                        print(f"\tCreando usuario \"doctor1\"... " + colors.GREEN + "Completado." + colors.WHITE)
                        user = User(
                            username="doctor1",
                            password=bcrypt.generate_password_hash('doctor1').decode('utf-8'),
                            role="doctor"
                        )
                        db.session.add(user)
                        db.session.commit()
                        
                        print(f"\tCreando doctor \"Gregory House\"... " + colors.GREEN + "Completado." + colors.WHITE)
                        doctor = Doctor(
                            user_id=5,
                            name="Gregory House",
                            specialty="Dentista"
                        )
                        db.session.add(doctor)
                        db.session.commit()
                        
                        print(f"\tCreando usuario \"doctor2\"... " + colors.GREEN + "Completado." + colors.WHITE)
                        user = User(
                            username="doctor2",
                            password=bcrypt.generate_password_hash('doctor2').decode('utf-8'),
                            role="doctor"
                        )
                        db.session.add(user)
                        db.session.commit()
                        
                        print(f"\tCreando doctor \"Pedro Martinez\"... " + colors.GREEN + "Completado." + colors.WHITE)
                        doctor = Doctor(
                            user_id=6,
                            name="Pedro Martinez",
                            specialty="Dentista"
                        )
                        db.session.add(doctor)
                        db.session.commit()
                        
                        print(f"\tCreando usuario \"doctor3\"... " + colors.GREEN + "Completado." + colors.WHITE)
                        user = User(
                            username="doctor3",
                            password=bcrypt.generate_password_hash('doctor3').decode('utf-8'),
                            role="doctor"
                        )
                        db.session.add(user)
                        db.session.commit()
                        
                        print(f"\tCreando centro \"Centro Odontológico Lliçà de Amunt\"... " + colors.GREEN + "Completado." + colors.WHITE)
                        center = Center(
                            name="Centro Odontológico Lliçà de Amunt",
                            address="Calle Baronia de Montbui, 63, 08186 Lliçà d'Amunt, Barcelona"
                        )
                        db.session.add(center)
                        db.session.commit()
                        
                        print(f"\tCreando centro \"Clínica Dental Costa Codina\"... " + colors.GREEN + "Completado." + colors.WHITE)
                        center = Center(
                            name="Clínica Dental Costa Codina",
                            address="Plaça de la Porxada, 21-23, 08401 Granollers, Barcelona"
                        )
                        db.session.add(center)
                        db.session.commit()
                        
                        print(f"\tCreando usuario \"secretario1\"... " + colors.GREEN + "Completado." + colors.WHITE)
                        user = User(
                            username="secretario1",
                            password=bcrypt.generate_password_hash('secretario1').decode('utf-8'),
                            role="secretary"
                        )
                        db.session.add(user)
                        db.session.commit()

                        now = datetime.datetime.now()

                        print(f"\tCreando cita... " + colors.GREEN + "Completado." + colors.WHITE)
                        appointment = Appointment(
                            date = datetime.datetime.strptime(f"{now.day}-{now.month}-{now.year + 1} {now.hour}:{now.minute}", "%d-%m-%Y %H:%M"), 
                            motive = "Limpieza dental", 
                            state = "Booked", 
                            patient_id = 1, 
                            doctor_id = 1, 
                            center_id = 1, 
                            register_user_id = 1, 
                        )
                        db.session.add(appointment)
                        db.session.commit()

                        print(f"\tCreando cita... " + colors.GREEN + "Completado." + colors.WHITE)
                        appointment = Appointment(
                            date = datetime.datetime.strptime(f"{now.day}-{now.month + 2}-{now.year} {now.hour}:{now.minute}", "%d-%m-%Y %H:%M"), 
                            motive = "Limpieza dental", 
                            state = "Booked", 
                            patient_id = 2, 
                            doctor_id = 1, 
                            center_id = 1, 
                            register_user_id = 1, 
                        )
                        db.session.add(appointment)
                        db.session.commit()

                        print(f"\tCreando cita... " + colors.GREEN + "Completado." + colors.WHITE)
                        appointment = Appointment(
                            date = datetime.datetime.strptime(f"{now.day}-{now.month+2}-{now.year} {now.hour}:{now.minute}", "%d-%m-%Y %H:%M"), 
                            motive = "Limpieza dental", 
                            state = "Booked", 
                            patient_id = 1, 
                            doctor_id = 2, 
                            center_id = 1, 
                            register_user_id = 1, 
                        )
                        db.session.add(appointment)
                        db.session.commit()

                        print(f"\tCreando cita... " + colors.GREEN + "Completado." + colors.WHITE)
                        appointment = Appointment(
                            date = datetime.datetime.strptime(f"12-01-{now.year - 1} 10:30", "%d-%m-%Y %H:%M"), 
                            motive = "Limpieza dental", 
                            state = "Canceled", 
                            patient_id = 2, 
                            doctor_id = 2, 
                            center_id = 2, 
                            register_user_id = 1, 
                        )
                        db.session.add(appointment)
                        db.session.commit()

                        print(f"\tCreando cita... " + colors.GREEN + "Completado." + colors.WHITE)
                        appointment = Appointment(
                            date = datetime.datetime.strptime(f"08-07-{now.year - 1} 10:30", "%d-%m-%Y %H:%M"), 
                            motive = "Limpieza dental", 
                            state = "Finished", 
                            patient_id = 2, 
                            doctor_id = 2, 
                            center_id = 2, 
                            register_user_id = 1, 
                        )
                        db.session.add(appointment)
                        db.session.commit()
        
                        saveUsers()
                        savePatients()
                        saveDoctors()
                        saveCenters()
                        saveAppointments()
                        break
                    else:
                        break
                        
        """

    main_blueprint = Blueprint('main', __name__)

    @main_blueprint.route('/', methods=['GET'])
    def main():
        return jsonify({
                'message': "Server SBA en funcionamiento!"
            }), 200
    
    img_blueprint = Blueprint('img', __name__)

    @img_blueprint.route('/<path:img_name>', methods=['GET'])
    def send_image(img_name): 
        return send_from_directory("images", img_name)

    login_blueprint = Blueprint('login', __name__)

    @login_blueprint.route('/', methods=['POST'])
    def login():
        username = request.form.get('username')
        password = request.form.get('password')

        user = get_user_internal(username).get_json()

        print(user)

        if user is not None and "error" not in user:
            if bcrypt.check_password_hash(user["password"], password):
                token = generate_jwt_token(username)
                expiration = datetime.datetime.utcnow() + JWT_EXPIRATION_DELTA

                return jsonify({
                    'token': token,
                    'expires_at': expiration.isoformat() + "Z",
                    'role': user["role"]
                }), 200
        return jsonify({'error': 'Username or password doesn\'t coincide.'}), 401
       
    user_blueprint = Blueprint('user', __name__)

    @user_blueprint.route('/', methods=['GET'])
    @requires_role(["customer", "admin"])
    def get_users():
        """
        Devuelve una lista completa con todos los usuarios a los usuarios con rol "admin".
        A los demas roles les devuelve solo su propio usuario.

        Returns:
            users: Listado de usuarios. Solo para el rol "admin"
            user: Usuario.
        """
        data = request.args
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Token no proporcionado"}), 401
        
        try:
            auth_type, token = auth_header.split(" ")
            if auth_type.lower() != "bearer":
                return jsonify({"error": "Formato de autorizacion invalido"}), 401
            
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms="HS256")

            user = get_user_internal(payload["sub"]).get_json()
        except Exception as e:
            print(e)

        data = request.args
        try:
            if user["role"] == "admin":
                if data.get("role") is not None:
                    users = User.query.filter_by(role=data.get("role")).filter(
                        User.id != user["id"]
                        ).all()
                else:
                    users = User.query.filter(
                        User.id != user["id"]
                        ).all()
                
                return jsonify([u.to_dict() for u in users])
            else:
                if user is None:
                    return jsonify({"error": "Ese usuario no está en la base de datos."})
                
                return jsonify(user), 200
        except Exception as e:
            print(e)
            return jsonify({"error": "No hay usuarios en la base de datos."})

    @user_blueprint.route('/<id>', methods=['GET'])
    @requires_role(["admin"])
    def get_user(id):
        """
        Devuelve un usuario identificado por su ID.

        Args:
            id: La ID del usuario que quieres recibir.

        Returns:
            user: Usuario al que la ID identifica.
        """
        try:
            user = User.query.filter_by(id=id).first_or_404()
            if user is None:
                return jsonify({"error": "Ese usuario no está en la base de datos."})
            return jsonify(user.to_dict()), 200
        except Exception as e:
            print(e)
            return jsonify({"error": "Ese usuario no está en la base de datos."})
        
    @user_blueprint.route('/username/<username>', methods=['GET'])
    @requires_role(["admin"])
    def get_user_by_username(username):
        """
        Devuelve un usuario identificado por su nombre de usuario.

        Args:
            username: El nombre de usuario del usuario que quieres recibir.

        Returns:
            user: Usuario al que el nombre de usuario identifica.
        """
        try:
            user = User.query.filter_by(username=username).first()
            if user is None:
                return jsonify({"error": "Ese usuario no está en la base de datos."})
            return jsonify(user.to_dict()), 200
        except Exception as e:
            print(e)
            return jsonify({"error": "Ese usuario no está en la base de datos."})

    @user_blueprint.route('/', methods=['POST'])
    @requires_role(["admin"])
    def add_user():
        """
        Agrega un nuevo usuario.
        El cuerpo de la solicitud debe incluir JSON con campos "username", "password", y "role".

        Returns:
            user: Usuario creado.
        """
        data = request.get_json()
        user = User(
            username=data["username"],
            password=bcrypt.generate_password_hash(data["password"]).decode('utf-8'),
            name=data["name"],
            role=data["role"]
        )
        db.session.add(user)
        db.session.commit()

        addUser(user)

        return jsonify(user.to_dict()), 201
    
    @user_blueprint.route('/', methods=['PUT'])
    @requires_role(["customer", "admin"])
    def update_my_user():
        """
        Modifica el usuario asignado al token.
        El cuerpo de la solicitud puede incluir JSON con campos "username", "password", y/o "role".

        Returns:
            user: Usuario modificado.
        """
        data = request.args
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Token no proporcionado"}), 401
        
        try:
            auth_type, token = auth_header.split(" ")
            if auth_type.lower() != "bearer":
                return jsonify({"error": "Formato de autorizacion invalido"}), 401
            
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms="HS256")

            user = get_user_internal(payload["sub"]).get_json()
        except Exception as e:
            print(e)

        data = request.get_json()

        try:
            user = User.query.filter_by(id=user["id"]).first_or_404()
            if user is None:
                return jsonify({"error": "Ese usuario no está en la base de datos."})
            
            if "username" in data.keys():
                user.username = data["username"]

            if "password" in data.keys():
                user.password = bcrypt.generate_password_hash(data["password"]).decode('utf-8')

            if "name" in data.keys():
                user.name = data["name"]

            db.session.commit()

            updateUser(user)

            result = user.to_dict()

            result["token"] = generate_jwt_token(user.username)
            result["expiration"] = datetime.datetime.utcnow() + JWT_EXPIRATION_DELTA

            return jsonify(result), 200
        except Exception as e:
            print(e)
            return jsonify({"error": "Ese usuario no está en la base de datos."})

    @user_blueprint.route('/<id>', methods=['PUT'])
    @requires_role(["admin"])
    def update_user(id):
        """
        Modifica un usuario identificado por una ID.
        El cuerpo de la solicitud puede incluir JSON con campos "username", "password", y/o "role".

        Returns:
            user: Usuario modificado.
        """
        data = request.args
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Token no proporcionado"}), 401
        
        try:
            auth_type, token = auth_header.split(" ")
            if auth_type.lower() != "bearer":
                return jsonify({"error": "Formato de autorizacion invalido"}), 401
            
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms="HS256")

            user = get_user_internal(payload["sub"]).get_json()
        except Exception as e:
            print(e)

        data = request.get_json()
        try:
            userMod = User.query.filter_by(id=id).first_or_404()
            if userMod is None:
                return jsonify({"error": "Ese usuario no está en la base de datos."})
            elif userMod.id == user["id"]:
                return jsonify({"error": "No está permitido modificar tu propio registro de usuario desde aquí."})
            
            if "username" in data.keys():
                userMod.username = data["username"]

            if "password" in data.keys():
                userMod.password = bcrypt.generate_password_hash(data["password"]).decode('utf-8')

            if "name" in data.keys():
                userMod.name = data["name"]

            if "role" in data.keys():
                userMod.role = data["role"]

            db.session.commit()

            updateUser(userMod)

            return jsonify(userMod.to_dict()), 200
        except Exception as e:
            print("Error:", e)
            return jsonify({"error": "Ese usuario no está en la base de datos."})

    @user_blueprint.route('/<id>', methods=['DELETE'])
    @requires_role(["admin"])
    def delete_user(id):
        """
        Elimina un usuario identificado por una ID.

        Returns:
            user: Usuario eliminado.
        """
        user = User.query.filter_by(id=id).first_or_404()
        result = user.to_dict()
        db.session.delete(user)
        db.session.commit()

        deleteUser(user)

        return jsonify(result), 200
    
    product_blueprint = Blueprint('product', __name__)

    @product_blueprint.route('/', methods=['GET'])
    @requires_role(["customer", "admin"])
    def get_products():
        """
        Devuelve una lista completa con todos los pacientes a los usuarios con rol "admin".
        Al rol "patient" les devuelve solo su propio paciente.

        Returns:
            patients: Listado de pacientes. Solo para el rol "admin".
            patient: Paciente. Solo para el rol "patient".
        """
        try:
                products = Product.query.all()
                
                return jsonify([p.to_dict() for p in products])
        except Exception as e:
            print(e)
            return jsonify({"error": "No hay productos en la base de datos."})
        
    @product_blueprint.route('/<id>', methods=['GET'])
    @requires_role(["customer", "admin"])
    def get_product(id):
        """
        Devuelve un paciente identificado por su ID.

        Args:
            id: La ID del paciente que quieres recibir.

        Returns:
            patient: Paciente al que la ID identifica.
        """
        try:
            product = Product.query.filter_by(id=id).first_or_404()
            if product is None:
                return jsonify({"error": "Ese producto no está en la base de datos."})
            return jsonify(product.to_dict()), 200
        except Exception as e:
            print(e)
            return jsonify({"error": "Ese producto no está en la base de datos."})

    @product_blueprint.route('/', methods=['POST'])
    @requires_role(["admin"])
    def add_product():
        """
        Agrega un nuevo paciente.
        El cuerpo de la solicitud debe incluir JSON con campos "user_id", "name", "phone_number", y "role".

        Returns:
            patient: Paciente creado.
        """
        data = request.get_json()

        product = Product(
            image=data["image"],
            name=data["name"],
            price=data["price"]
        )
        db.session.add(product)
        db.session.commit()

        return jsonify(product.to_dict()), 201

    @product_blueprint.route('/<id>', methods=['PUT'])
    @requires_role(["admin"])
    def update_product(id):
        """
        Modifica un producto identificado por una ID.
        El cuerpo de la solicitud puede incluir JSON con campos "user_id", "name", "phone_number", y/o "role".

        Returns:
            product: Producto modificado.
        """
        data = request.get_json()
        try:
            product = Product.query.filter_by(id=id).first_or_404()
            if product is None:
                return jsonify({"error": "Ese producto no está en la base de datos."})
            
            if data["image"] is not None:
                product.image = data["image"]

            if data["name"] is not None:
                product.name = data["name"]

            if data["price"] is not None:
                product.price = data["price"]

            db.session.commit()

            savePatients()

            return jsonify(product.to_dict()), 200
        except Exception as e:
            print(e)
            return jsonify({"error": "Ese producto no está en la base de datos."})

    @product_blueprint.route('/<id>', methods=['DELETE'])
    @requires_role(["admin"])
    def delete_product(id):
        """
        Elimina un producto identificado por una ID.

        Returns:
            product: Producto eliminado.
        """
        product = Product.query.filter_by(id=id).first_or_404()
        result = product.to_dict()
        db.session.delete(product)
        db.session.commit()
        return jsonify(result), 200

    command_blueprint = Blueprint('command', __name__)

    @command_blueprint.route('/', methods=['GET'])
    @requires_role(["customer", "admin"])
    def get_commands():
        """
        Devuelve una lista completa con todos los doctores a los usuarios con rol "admin" o "patient".
        Al rol "doctor" les devuelve solo su propio doctor.

        Returns:
            doctors: Listado de doctores. Solo para los roles "admin" y "patient".
            doctor: Doctor. Solo para el rol "doctor".
        """
        data = request.args

        try:
            if data.get("user_id")is not None:
                commands = Command.query.filter_by(user_id=data.get("user_id")).all()
            else: 
                commands = Command.query.all()
            return jsonify([c.to_dict() for c in commands])
        except Exception as e:
            print(e)
            return jsonify({"error": "No hay pedidos en la base de datos."})
        
    @command_blueprint.route('/<id>', methods=['GET'])
    @requires_role(["customer", "admin"])
    def get_command(id):
        """
        Devuelve un doctor identificado por su ID.

        Args:
            id: La ID del doctor que quieres recibir.

        Returns:
            doctor: Doctor al que la ID identifica.
        """
        try:
            command = Command.query.filter_by(id=id).first_or_404()
            if command is None:
                return jsonify({"error": "Ese pedido no está en la base de datos."})
            return jsonify(command.to_dict()), 200
        except Exception as e:
            print(e)
            return jsonify({"error": "Ese doctor no está en la base de datos."})
        
    @command_blueprint.route('/', methods=['POST'])
    @requires_role(["admin"])
    def add_command():
        """
        Agrega un nuevo doctor.
        El cuerpo de la solicitud debe incluir JSON con campos "user_id", "name", y "specialty".

        Returns:
            doctor: Doctor creado.
        """
        data = request.get_json()
        command = Command(
            user_id=data["user_id"],
            ready=False,
            delivering=False,
            delivered=False
        )
        db.session.add(command)
        db.session.commit()

        return jsonify(command.to_dict()), 201

    @command_blueprint.route('/<id>', methods=['PUT'])
    @requires_role(["admin"])
    def update_command(id):
        """
        Modifica un doctor identificado por una ID.
        El cuerpo de la solicitud puede incluir JSON con campos "user_id", "name", y/o "specialty".

        Returns:
            doctor: Doctor modificado.
        """
        data = request.get_json()
        try:
            command = Command.query.filter_by(id=id).first_or_404()
            if command is None:
                return jsonify({"error": "Ese pedido no está en la base de datos."})
                                   
            if data["user_id"] is not None:
                command.user_id = data["user_id"]

            if data["ready"] is not None:
                command.ready = data["ready"]

            if data["delivering"] is not None:
                command.delivering = data["delivering"]

            if data["delivered"] is not None:
                command.delivered = data["delivered"]

            db.session.commit()

            return jsonify(command.to_dict()), 200
        except Exception as e:
            print(e)
            return jsonify({"error": "Ese paciente no está en la base de datos."})

    @command_blueprint.route('/<id>', methods=['DELETE'])
    @requires_role(["admin"])
    def delete_command(id):
        """
        Elimina un doctor identificado por una ID.

        Returns:
            doctor: Doctor eliminado.
        """
        command = Command.query.filter_by(id=id).first_or_404()
        result = command.to_dict()
        db.session.delete(command)
        db.session.commit()
        return jsonify(result), 200

    center_blueprint = Blueprint('center', __name__)

    @center_blueprint.route('/', methods=['GET'])
    @requires_role(["customer", "admin"])
    def get_centers():
        """
        Devuelve una lista completa con todos los centros.

        Returns:
            centers: Listado de centros.
        """
        try:
            centers = Center.query.all()
            return jsonify([c.to_dict() for c in centers])
        except Exception as e:
            print(e)
            return jsonify({"error": "No hay pacientes en la base de datos."})
        
    @center_blueprint.route('/<id>', methods=['GET'])
    @requires_role(["customer", "admin"])
    def get_center(id):
        """
        Devuelve un centro identificado por su ID.

        Args:
            id: La ID del centro que quieres recibir.

        Returns:
            center: Centro al que la ID identifica.
        """
        try:
            center = Center.query.filter_by(id=id).first_or_404()
            if center is None:
                return jsonify({"error": "Ese centro no está en la base de datos."})
            return jsonify(center.to_dict()), 200
        except Exception as e:
            print(e)
            return jsonify({"error": "Ese centro no está en la base de datos."})
        
    @center_blueprint.route('/', methods=['POST'])
    @requires_role(["admin"])
    def add_center():
        """
        Agrega un nuevo centro
        El cuerpo de la solicitud debe incluir JSON con campos "user_id", "name", y "address"

        Returns:
            center: Centro creado.
        """
        data = request.get_json()
        center = Center(
            user_id=data["user_id"],
            name=data["name"],
            address=data["address"]
        )
        db.session.add(center)
        db.session.commit()

        saveCenters()

        return jsonify(center.to_dict()), 201

    @center_blueprint.route('/<id>', methods=['PUT'])
    @requires_role(["admin"])
    def update_center(id):
        """
        Modifica un center identificado por una ID.
        El cuerpo de la solicitud puede incluir JSON con campos "user_id", "name", y/o "address".

        Returns:
            center: Center modificado.
        """
        data = request.get_json()
        try:
            center = Center.query.filter_by(id=id).first_or_404()
            if center is None:
                return jsonify({"error": "Ese usuario no está en la base de datos."})
            
            if data["name"] is not None:
                center.name = data["name"]

            if data["address"] is not None:
                center.address = data["address"]

            db.session.commit()

            saveCenters()

            return jsonify(center.to_dict()), 200
        except Exception as e:
            print(e)
            return jsonify({"error": "Ese paciente no está en la base de datos."})

    @center_blueprint.route('/<id>', methods=['DELETE'])
    @requires_role(["admin"])
    def delete_center(id):
        """
        Elimina un centro identificado por una ID.

        Returns:
            center: Centro eliminado.
        """
        center = Center.query.filter_by(id=id).first_or_404()
        result = center.to_dict()
        db.session.delete(center)
        db.session.commit()
        return jsonify(result), 200

    appointment_blueprint = Blueprint('appointment', __name__)

    @appointment_blueprint.route('/', methods=['GET'])
    @requires_role(["customer", "admin"])
    def get_appointments():
        """
        Devuelve una lista completa con todas las citas.

        Returns:
            appointments: Listado de citas.
        """
        data = request.args
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Token no proporcionado"}), 401
        
        try:
            auth_type, token = auth_header.split(" ")
            if auth_type.lower() != "bearer":
                return jsonify({"error": "Formato de autorizacion invalido"}), 401
            
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms="HS256")

            user = get_user_internal(payload["sub"]).get_json()
        except Exception as e:
            print(e)

        try:
            if user["role"] == "patient":
                if user["patient_id"] is not None:
                    appointments = Appointment.query.filter_by(patient_id=user["patient_id"]).filter_by(state="Booked").filter(
                        Appointment.date >= datetime.datetime.strptime(f"{datetime.datetime.now().strftime("%d-%m-%Y")} 00:00", "%d-%m-%Y %H:%M"),
                        ).order_by(Appointment.date).all()
                else:
                    return jsonify({"error": "No tienes citas en la base de datos."})
            elif user["role"] == "doctor":
                if user["doctor_id"] is not None:
                    appointments = Appointment.query.filter_by(doctor_id=user["doctor_id"]).filter_by(state="Booked").filter(
                        Appointment.date >= datetime.datetime.strptime(f"{datetime.datetime.now().strftime("%d-%m-%Y")} 00:00", "%d-%m-%Y %H:%M"),
                        ).order_by(Appointment.date).all()
                else:
                    return jsonify({"error": "No tienes citas en la base de datos."})
            elif user["role"] == "secretary":
                appointments = Appointment.query.filter(
                    Appointment.date >= datetime.datetime.strptime(f"{datetime.datetime.now().strftime("%d-%m-%Y")} 00:00", "%d-%m-%Y %H:%M"),
                    ).order_by(Appointment.date).all()
            else:
                if data.get("doctor_id") is not None and data.get("date") is not None:
                    appointments = Appointment.query.filter(
                                Appointment.date == datetime.datetime.strptime(f"{data.get("date")}", "%d-%m-%Y %H:%M"),
                                Appointment.doctor_id == data["doctor_id"]
                                ).order_by(Appointment.date).all()
                elif data.get("date") is not None:
                    appointments = Appointment.query.filter(
                        Appointment.date >= datetime.datetime.strptime(f"{data.get("date")} 00:00", "%d-%m-%Y %H:%M"),
                        Appointment.date <= datetime.datetime.strptime(f"{data.get("date")} 23:59", "%d-%m-%Y %H:%M")
                        ).order_by(Appointment.date).all()
                elif data.get("state") is not None:
                    appointments = Appointment.query.filter_by(state=data.get("state")).order_by(Appointment.date).all()
                elif data.get("patient_id") is not None:
                    appointments = Appointment.query.filter_by(patient_id=data.get("patient_id")).order_by(Appointment.date).all()
                elif data.get("doctor_id") is not None:
                    appointments = Appointment.query.filter_by(doctor_id=data.get("doctor_id")).order_by(Appointment.date).all()
                elif data.get("center_id") is not None:
                    appointments = Appointment.query.filter_by(center_id=data.get("center_id")).order_by(Appointment.date).all()
                else:
                    appointments = Appointment.query.order_by(Appointment.date).all()

            return jsonify([a.to_dict() for a in appointments])
        except Exception as e:
            print(e)
            return jsonify({"error": "No hay citas en la base de datos."})
    
    @appointment_blueprint.route('/<id>', methods=['GET'])
    @requires_role(["admin"])
    def get_appointment(id):
        """
        Devuelve una cita identificada por su ID.

        Args:
            id: La ID de la cita que quieres recibir.

        Returns:
            appointment: Cita al que la ID identifica.
        """
        try:
            appointment = Appointment.query.filter_by(id=id).first_or_404()
            if appointment is None:
                return jsonify({"error": "Esa cita no está en la base de datos."})
            return jsonify(appointment.to_dict()), 200
        except Exception as e:
            print(e)
            return jsonify({"error": "Esa cita no está en la base de datos."})
        
    @appointment_blueprint.route('/', methods=['POST'])
    @requires_role(["admin"])
    def add_appointment():
        """
        Agrega una nueva cita.
        El cuerpo de la solicitud debe incluir JSON con campos "date", "motive", "state", "patient_id", "doctor_id", "center_id", "register_user_id".

        Returns:
            appointment: Cita creada.
        """
        data = request.get_json()

        appointment = Appointment.query.filter(
                    Appointment.date == datetime.datetime.strptime(f"{data.get("date")}", "%d-%m-%Y %H:%M"),
                    Appointment.doctor_id == data["doctor_id"]
                    ).first()
        
        if appointment is not None:
            return jsonify({"error": "El doctor ya tiene una cita en esa fecha y hora."})
        else:
            appointment = Appointment(
                date=datetime.datetime.strptime(f"{data["date"]}", "%d-%m-%Y %H:%M"),
                motive=data["motive"],
                state=data["state"],
                patient_id=data["patient_id"],
                doctor_id=data["doctor_id"],
                center_id=data["center_id"],
                register_user_id=data["register_user_id"]
            )
            db.session.add(appointment)
            db.session.commit()

            saveAppointments()

            return jsonify(appointment.to_dict()), 201

    @appointment_blueprint.route('/<id>', methods=['PUT'])
    @requires_role(["admin"])
    def update_appointment(id):
        """
        Modifica una nueva cita.
        El cuerpo de la solicitud debe incluir JSON con campos "date", "motive", "state", "patient_id", "doctor_id", "center_id", y/o "register_user_id".

        Returns:
            appointment: Cita modificada.
        """
        data = request.get_json()
        try:
            appointment = Appointment.query.filter_by(id=id).first_or_404()

            if appointment is None:
                return jsonify({"error": "Esa cita no está en la base de datos."})

            if data["date"] is not None:      
                other_appointment = Appointment.query.filter(
                            Appointment.date == datetime.datetime.strptime(f"{data["date"]}", "%d-%m-%Y %H:%M"),
                            Appointment.doctor_id == data["doctor_id"]
                            ).first()
            else:
                other_appointment = None
            
            if other_appointment is not None and appointment.date != other_appointment.date:
                return jsonify({"error": "El doctor ya tiene una cita en esa fecha y hora."})
            elif data["date"] is not None:
                appointment.date = datetime.datetime.strptime(f"{data["date"]}", "%d-%m-%Y %H:%M")

            if data["motive"] is not None:
                appointment.motive = data["motive"]

            if data["state"] is not None:
                appointment.state = data["state"]

            if data["patient_id"] is not None:
                appointment.patient_id = data["patient_id"]

            if data["doctor_id"] is not None:
                appointment.doctor_id = data["doctor_id"]

            if data["center_id"] is not None:
                appointment.center_id = data["center_id"]

            if data["register_user_id"] is not None:
                appointment.register_user_id = data["register_user_id"]

            db.session.commit()

            saveAppointments()

            return jsonify(appointment.to_dict()), 200
        except Exception as e:
            print(e)
            return jsonify({"error": "Esa cita no está en la base de datos."})

    @appointment_blueprint.route('/<id>', methods=['DELETE'])
    @requires_role(["admin"])
    def delete_appointment(id):
        """
        Elimina una cita identificada por una ID.

        Returns:
            appointment: Cita eliminada.
        """
        appointment = Appointment.query.filter_by(id=id).first_or_404()
        result = appointment.to_dict()
        db.session.delete(appointment)
        db.session.commit()
        return jsonify(result), 200

    app.register_blueprint(main_blueprint, url_prefix='/')
    app.register_blueprint(login_blueprint, url_prefix='/auth/login')
    app.register_blueprint(img_blueprint, url_prefix='/img')
    app.register_blueprint(user_blueprint, url_prefix='/api/user')
    app.register_blueprint(product_blueprint, url_prefix='/api/product')
    app.register_blueprint(command_blueprint, url_prefix='/api/command')
    
    return app

if __name__ == '__main__':
    #clear_terminal()
    app = create_app()
    app.run(host='0.0.0.0', debug=True)