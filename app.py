# Se importa las librerias de el framework Flask, como render_template para renderizar las plantillas HTML, 
# request para manejar las solicitudes HTTP, redirect para redirigir a otras rutas, session para manejar sesiones de usuario, 
# jsonify para devolver respuestas JSON y flash para mostrar mensajes flash en la interfaz de usuario.
from flask import Flask, render_template, request, redirect, session, jsonify, flash
# Las librerias de flask_login se utilizan para manejar la autenticación y autorización de usuarios en la aplicación web
# LoginManager junto con login_user, logout, login_required y UserMixin se encargan de gestionar el proceso de inicio de sesión, cierre de sesión y protección de rutas.
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
# pymysql es una biblioteca de Python puro para conectarse a bases de datos MySQL y MariaDB.
# Esta libreria no requiere de extenciones de C, haciendolo sensillo de instalar 
import pymysql

from werkzeug.utils import secure_filename  
import os
 
app = Flask(__name__) # Crea la instancia de flask, necesario para determinar la ubicación de los recursos del proyecto

app.secret_key = 'secret_key' # se crea una clave secreta para el uso de sesiones, el cual protege la información de los usuarios que se encuentren dentro de la sesion.
def Conexion():
    conn = pymysql.connect( # Establece la conexion a la base de datos, esta funcion se llama cada vez que se realiza una consulta
        host='localhost',   # a la base de datos, permitiendo reutilizar el codigo facilmente.
        user='root',
        password='10092005',
        database='frutix',
        autocommit=False   # Desactiva el uso del autocommit para manejar las transacciones manualmente, lo que permite realizar rollbacks en caso de errores.
                           # fomentando la atomicidad de las operaciones y la integridad de los datos en la base de datos.                
    )
    return conn

class User(UserMixin):                      # Se define la clase User la cual contiene los atributos de los usuarios para manejar la autenticacion y autorizacion de usuarios,
    def __init__(self, username, rol, id):  # facilitando la gestion de sesiones y el control de acceso a las diversas rutas del proyecto.
        self.id = id
        self.username = username
        self.rol = rol                                        
    
login_manager = LoginManager()  # Se crea una instancia de LoginManager, el cual administra los procesos de inicio y cierre de sesion,
login_manager.init_app(app)     # Este funciona en conjunto con UserMixin para la gestion de usuarios y proteccion de rutas del proyecto
login_manager.login_view = '/'  # Establece la ruta de inicio de sesión, redirigiendo a los usuarios no autenticados a la pagina de inicio de sesión
  
@login_manager.user_loader # user_loader carga un usuario obteniendo su ID de la base de datos y sus propiedades, permitiendo que Flask-login
def load_user(user_id):    # maneje la autorizacion del usuario.
    conn = Conexion()
    cur = conn.cursor()

    cur.execute("SELECT ID_U, Nombre, Rol FROM USUARIOS WHERE ID_U = %s", (user_id,)) # Ejecuta una consulta a la BD para obtener la informacion del usuario
    user = cur.fetchone()                                                             # necesario para la carga del usuario a la sesion  

    cur.close() # Cierra el cursor y la conexion de la base de datos para liberar recursos y evitar posibles fugas de memoria.
    conn.close()

    if user:
        return User(username=user[1], rol=user[2], id=user[0]) # Si se encuentra el usuario en la base de datos, se crea una instancia de la clase User
    return None

@app.route('/logout')
@login_required
def logout():
    logout_user() # Elimina la informacion del usuario de la sesion.
    session.clear() # Limpia la sesion del usuario, eliminando sus datos y permisos almacenados.
    return redirect('/') # redirige al usuario para iniciar sesion nuevamente

@app.route('/', methods=['GET', 'POST']) # Se usan los metodos GET y POST para manejar el formulario de inicio de sesion, permitiendo el ingreso de sus credenciales
def inicio_Sesion():                     # redirigiendo al usuario a la pagina correspondiente segun su rol
    if request.method == 'POST':

        Nombre_usuario = request.form['usuario']  # Obtiene el nombre y contraseña del usuario desde el formulario de HTML
        Contraseña = request.form['password']

        conn = Conexion()
        cur = conn.cursor() # Inicializa la conexion y cursor de la base de datos para la ejecucion de la consulta el cual obtiene la informacion de los usuarios
                            # y comparar las credenciales ingresadas para asi autenticar al usuario.
        cur.execute(
            "SELECT ID_U, Nombre, Contraseña, Rol FROM USUARIOS WHERE Nombre = %s",
            (Nombre_usuario,)
        )
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and user[2] == Contraseña: # Verifica si el usuario existe y si la contraseña coincide.

            user_obj = User(
                username=user[1],
                rol=user[3],  # Si la contraseña es correcta crea la instancia del usuario con la informacion obtenidad de la base de datos.
                id=user[0]
            )

            login_user(user_obj) 
            session['rol'] = user[3] # Almacena el rol del usuario en la sesion, la cual se usa en para las varias funciones del proyecto.

            if user[3] == 1:
                return redirect('/login_adm')  # Compara el rol del usuario para redirigirlo a la pagina con las funciones correspondientes a su rol.
            elif user[3] == 2:
                return redirect('/login_gerente')
            else:
                return redirect('/login_empleado')

        else:
            return render_template('inicio.html', error='Usuario o contraseña incorrectos') # Si no son correctos, muestra un mensaje de error.

    return render_template("inicio.html")

@app.route('/login_adm')
def login_admin():
    return render_template('login_adm.html') # Renderiza la pagina con todas la funciones disponibles del proyecto para el administrador

@app.route('/login_empleado')
def login_empleado():
    return render_template('login_empleado.html') # Renderiza la pagina solo con acceso a la pagina de ventas e inventario.
 
@app.route('/login_gerente')
def login_gerente():
    return render_template('login_gerente.html') # Renderiza la pagina con acceso a las paginas de ventas, inventario y caja, pero sin acceso a la gestion de usuarios, caja y gastos.

#------------------------INVENTARIO-------------------------------
@app.route('/inventario')
@login_required
def inventario():
    conn = Conexion()
    cur = conn.cursor()
    categoria = request.args.get('categoria') # Obtiene la categoria seleccionada por el usuario para filtrar los productos,
    consulta = """SELECT \"Activo\" AS ESTADO, p.nombre, p.cantidad, p.precio, p.merma, p.categoria, e.nombre_embolsado AS Tipo_Venta, p.codigo 
                FROM frutix.embolsado e 
                JOIN frutix.mm_prodtip pr ON pr.ID_embolsado = e.id_em
                JOIN frutix.productos p on pr.ID_producto = p.codigo
                WHERE p.estado = 'Activo'""" # Consulta para obtener la informacion de los productos del inventario, mostrando solo los productos activos, ademas de mostrar su tipo de venta usando un JOIN con las tablas mm_prodtip y embolsado.
    if categoria: # En caso de que se seleccione una categoria se agrega la clausula WHERE, sirviendo para filtrar los productos.
        consulta += " AND p.categoria = %s"
        cur.execute(consulta, (categoria,))
    else:
        cur.execute(consulta) # En caso de que se seleccione la opcion de "Mostrar todo" se ejecuta la consulta sin la clausula.
    
    inventario = cur.fetchall()
    
    return render_template('inventario.html', Inventario=inventario)

@app.route('/Modificar_producto', methods=['POST'])
def modificar_producto():
    conn = Conexion()
    if request.method == 'POST':
        id_producto = request.form['ID'] # Obtiene los datos del formulario para modificar el producto seleccionado en la base de datos.
        nombre = request.form['nombre']
        precio = float(request.form['precio'])
        cantidad = request.form['cantidad']
        merma = request.form['merma']
        categoria = request.form['categoria']
        tipo_venta = request.form['unidad']

        with conn.cursor() as cur:
            cur.execute("UPDATE productos SET Nombre=%s, precio=%s, cantidad=%s, merma=%s, categoria=%s WHERE codigo=%s",
                        (nombre, precio, cantidad, merma, categoria, id_producto))
            cur.execute("UPDATE mm_prodtip SET ID_embolsado=%s WHERE ID_producto=%s", (tipo_venta, id_producto))
            conn.commit()
    return redirect('/inventario')

@app.route('/Eliminar_producto', methods=['POST'])
def eliminar_producto():
    id_producto = request.form['ID'] # Obtiene el ID del producto donde se encuentra el boton de eliminar
    if request.method == 'POST':
        conn = Conexion()
        with conn.cursor() as cur:
            cur.execute("UPDATE productos SET Estado = 'Inactivo' WHERE codigo = %s", (id_producto)) # Elimina el producto de la base de datos usando su ID.
        conn.commit()
    return redirect('/inventario')

@app.route("/BuscarProd", methods=['POST'])
def Buscar_Producto():
    Nombre_Producto = request.form['Buscar']
    busca = f"%{Nombre_Producto}%"
    if request.method == 'POST':
        conn = Conexion()
        with conn.cursor() as cur:
            cur.execute("""SELECT \"Activo\" AS ESTADO, p.nombre, p.cantidad, p.precio, p.merma, p.categoria, e.nombre_embolsado AS Tipo_Venta, p.codigo 
                FROM frutix.embolsado e 
                JOIN frutix.mm_prodtip pr ON pr.ID_embolsado = e.id_em
                JOIN frutix.productos p on pr.ID_producto = p.codigo
                WHERE p.estado = 'Activo' AND p.nombre LIKE %s""", (busca)) 
        
        Filtro = cur.fetchall()
    return render_template('inventario.html', Inventario=Filtro)

EXTENSIONESPROD = {'png', 'jpg'}

def ArchivoPermitido(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSIONESPROD
    
@app.route('/agregarproductos.html', methods=['GET', 'POST'])
def agregar_producto():
    conn = Conexion()
    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = float(request.form['precio'])
        cantidad = request.form['cantidad']
        merma = request.form['merma'] # Obtiene los datos del formulario para agregar el producto nuevo a la base de datos
        categoria = request.form['categoria']
        tipo_venta = request.form['tipo_venta']
        
        foto = request.files.get('Imagen')

        if foto and ArchivoPermitido(foto.filename):
            extension = foto.filename.rsplit('.', 1)[1].lower()
            nombre_archivo = secure_filename(f"{nombre}.{extension}")
            ruta = os.path.join("static", nombre_archivo)
            foto.save(ruta)
        else:
            return render_template('agregarproductos.html', error='Archivo no permitido')

        with conn.cursor() as cur:
            cur.execute("INSERT INTO productos (Nombre, precio, cantidad, merma, categoria) VALUES (%s, %s, %s, %s, %s)",
                        (nombre, precio, cantidad, merma, categoria)) # Ingresa los datos en la BD
            producto_id = cur.lastrowid # Obtiene el ID del ultimo producto agregado para relacionarlo a la tabla mm_prodtip
            cur.execute("INSERT INTO mm_prodtip (ID_producto, ID_embolsado) VALUES (%s, %s)",
                        (producto_id, tipo_venta))
            conn.commit()
               
    return render_template('agregarproductos.html') 


#------------------------VENTAS-------------------------------
@app.route('/ventas')
@login_required
def ventas():
    conn = Conexion()
    cur = conn.cursor()
    cur.execute("""SELECT p.codigo, p.nombre, p.cantidad, p.precio, p.merma, p.categoria,e.nombre_embolsado AS Tipo_Venta 
                FROM frutix.embolsado e 
                JOIN frutix.mm_prodtip pr ON pr.ID_embolsado = e.id_em
                JOIN frutix.productos p on pr.ID_producto = p.codigo
                WHERE p.estado = 'Activo'""") # Consulta para obtener la informacion de los productos del inventario, mostrando solo los productos activos, ademas de mostrar su tipo de venta usando un JOIN con las tablas mm_prodtip y embolsado.
    Productos = cur.fetchall()
    return render_template('ventas.html', productos=Productos) # Obtiene los productos del inventario los cuales se muestran en la pagina de ventas

@app.route('/Procesar_venta', methods=['POST'])
@login_required
def procesar_venta():
    conn = Conexion()
    cur = conn.cursor()
    
    empleado = current_user.id # Obtiene el ID del usuario para con el fin de registrar el empleado que realizo la venta.

    productos_vendidos = [] # Inicializa una lista de productos vendidos, la cual almacena cada producto con su cantidad para ser mostrado en el concepto de venta
    total = 0
    detalles = [] # Guarda los detalles de los productos vendidos para almacenarlo en la tabla mm_vp, para tener un registro detallado de cada venta

    for producto, vendidos in request.form.items(): # Por cada producto en el formulario se obtiene su cantidad, calculando su subtotal e ingresando su informacion
                                                    # a la base de datos, ademas de agregarlo a la lista de productos vendidos para mostrarlo en el concepto de venta.
        if producto.startswith("productos["): # Verifica que el producto tenga el formato correcto para que se procesen solo los productos seleccionados en el formulario.
            cantidad = int(vendidos) # Convierte la cantidad de cada producto vendido a entero para evitar errores de formato como TypeError.

            if cantidad >= 0:                                           # Verifica que la cantidad sea mayor o igual a 0, para evitar errores de formato como ValueError,
                                                                        # ademas de evitar que se ingresen cantidades negativas.
                id_producto = int(producto.split("[")[1].split("]")[0]) # Obtiene el ID del producto a partir del nombre del campo del formulario, 
                                                                   # el cual tiene el formato "productos[ID]", extrayendo el ID para usarlo en las consultas de la base de datos.
                cur.execute(
                    "SELECT nombre, precio FROM frutix.productos WHERE codigo = %s",
                    (id_producto,)
                )
                producto = cur.fetchone()

                nombre = producto[0]
                precio = float(producto[1])

                subtotal = precio * cantidad # Realiza el calculo del subtotal de cada producto para asi obtener el total de la venta.
                total += subtotal

                productos_vendidos.append(f"{nombre} x{cantidad}") # Agrega el producto vendido a la lista de productos vendidos.

                detalles.append((id_producto, cantidad, precio)) # Almacena los detalles del producto vendido en la lista de detalles para ingresarlo a la tabla mm_vp.
                
            if id_producto is None:
                flash("La cantidad del producto debe ser mayor a 0", "error") # En caso de que no se seleccione una cantidad para un producto, 
                conn.rollback()                                               # se muestra un mensaje de error indicando que la cantidad debe ser mayor a 0.
                return redirect('/ventas')

    concepto = ", ".join(productos_vendidos) # Une los productos vendidos en una cadena de texto para mostrarlo y almacenarlo en el concepto de cadena en la base de datos,
                                             # Se vera de esta forma en el apartado de caja.
    cur.execute("INSERT INTO Fecha (Fecha) VALUES (CURDATE())") # Almacena la fecha actual en la tabla Fecha con CURDATE() el cual la almacena con el formato Año-Mes-Dia
    id_fecha = cur.lastrowid # Obtiene el ID de la ultima fecha almacenada 

    cur.execute("INSERT INTO Hora (Hora) VALUES (CURTIME())") # Almacena la hora actual en la tabla Hora con CURTIME() el cual la almacena con el formato Hora:Minuto:Segundo
    id_hora = cur.lastrowid # Obtiene el ID de la ultima hora almacenada para relacionarla con la venta realizada.
    
    cur.execute("""
        INSERT INTO ventas (Concepto, Fecha, Hora, Total, Empleado)
        VALUES (%s, %s, %s, %s, %s)
    """, (concepto, id_fecha, id_hora, total, empleado)) # Almacena la venta en la tabla ventas, ingresando el empleado que la realizo
    
    conn.commit()

    id_venta = cur.lastrowid # Obtiene el ID de la ultima venta realizada para relacionarla con los detalles de la venta en la tabla mm_vp.

    for id_producto, cantidad, precio in detalles:
        try:
            cur.execute("""
            INSERT INTO mm_vp (ID_Producto, ID_Venta, cantidad, Precio_unitario)
            VALUES (%s, %s, %s, %s)
        """, (id_producto, id_venta, cantidad, precio)) # se repite por cada producto vendido 
            cur.execute("""
                UPDATE productos p SET Cantidad = Cantidad - %s WHERE p.codigo = %s
            """, (cantidad, id_producto)) # Actualiza la cantidad de cada producto vendido en la base de datos, restando la cantidad vendida a la cantidad actual del producto para mantener el inventario actualizado.
        except Exception as e:
            print("ERROR EN mm_vp:", e)

    conn.commit()

    return redirect('/ventas')

@app.route('/filtrar_productos')
def filtrar_productos():
    conn = Conexion()
    categoria = request.args.get('categoria') # Similar a inventario, se obtiene la categoria de los productos seleccionada por el usuario
                                              # para filtrar los productos mostrados en la pagina de ventas.
    cur = conn.cursor()

    if categoria == "todas":
        cur.execute("SELECT codigo, nombre, cantidad, precio FROM productos WHERE ESTADO = 'Activo'") # Si se selecciona la opcion de "Todos" obtiene todos los productos
    else:
        cur.execute("""
            SELECT codigo, nombre, cantidad, precio 
            FROM productos 
            WHERE categoria = %s and estado = 'Activo'
        """, (categoria,)) # Si selecciona una categoria se ejecuta la consulta con la clausula WHERE. 

    filas = cur.fetchall()

    productos = [] 
    for r in filas:
        productos.append({  # Se crea una lista de diccionarios con la informacion de los productos obtenida de la base de datos, 
            "nombre": r[1], # la cual se devuelve como respuesta JSON para que se muestre en el frontend y mostrar solo los productos filtrados.
            "codigo": r[0],
            "cantidad": r[2],
            "precio": float(r[3])
        })

    return jsonify(productos)

#------------------------USUARIOS-------------------------------
@app.route('/usuarios')
@login_required
def usuarios():
    conn = Conexion()
    cur = conn.cursor()
    cur.execute("SELECT ID_U, Nombre, Contraseña, Rol FROM USUARIOS WHERE ESTADO = 'Activo'") # Dado a que solo el administrador tiene acceso a la gestion de usuarios,
    Usuarios = cur.fetchall()                                         # se muestra toda la informacion de los usuarios para que se puedan modificar o eliminar.
    return render_template('usuarios.html', usuarios=Usuarios)

EXTENSIONES = {'png', 'jpg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSIONES

@app.route('/Agregar_usuarios', methods=['POST'])
def Agregar_usuarios():
    conn = Conexion()
    Nombre = request.form['nombre']
    Rol = request.form['rol']                    # Obtiene los datos del formulario para agregar un nuevo usuario a la base de datos.
    Contraseña = request.form['password']
    with conn.cursor() as cur:
        cur.execute("INSERT INTO usuarios (Nombre, Contraseña, Rol) VALUES (%s, %s, %s)", (Nombre, Contraseña, Rol))
        conn.commit() # Ingresa el usuario a la base de datos y confirma la transaccion para guardar los cambios realizados.
           
    foto = request.files.get('Imagen')

    if foto and allowed_file(foto.filename):
        extension = foto.filename.rsplit('.', 1)[1].lower()
        nombre_archivo = secure_filename(f"{Nombre}.{extension}")
        ruta = os.path.join("static/uploads", nombre_archivo)
        foto.save(ruta)
    else:
        print("Archivo no permitido")
    return redirect('/usuarios')

@app.route('/Modificar_usuarios', methods=['POST'])
def modificar_usuarios():
    conn = Conexion()
    ID_usuario = request.form['ID_usuario']
    Permisos = request.form['Permisos'] # obtiene los datos del formulario para la modificacion de un usuario
    Contraseña = request.form['Contraseña']
    with conn.cursor() as cur:
        cur.execute("UPDATE USUARIOS SET Contraseña = %s, Rol = %s WHERE ID_U = %s", (Contraseña, Permisos, ID_usuario))
        conn.commit()
    return redirect('/usuarios')

@app.route('/Eliminar_usuario', methods=['POST'])
def eliminar_usuarios():
    conn = Conexion()
    ID_Usuario = request.form['ID_usuario'] # Obtiene el ID del usuario donde se encuentra el boton de eliminar
    with conn.cursor() as cur:
        cur.execute("UPDATE USUARIOS SET ESTADO = 'Inactivo' WHERE ID_U = %s", (ID_Usuario)) # Marca el usuario como inactivo en la base de datos usando el ID.
        conn.commit()
    return redirect('/usuarios')

#------------------------CAJA Y GASTOS-------------------------------
@app.route('/caja')
def caja():
    conn = Conexion()
    cur = conn.cursor() 
    cur.execute("""
        SELECT v.Concepto, v.Total, f.fecha, h.hora
        FROM ventas v
        JOIN Fecha f ON v.Fecha = f.ID_F
        JOIN Hora h ON v.Hora = h.ID_H
        ORDER BY f.Fecha DESC, h.Hora DESC
    """) # Obtiene las ventas realizadas, mostrando su concepto, total, fecha y hora, ordenandolas de la mas reciente a la mas antigua para mostrar 
         # un historial de ventas en el apartado de caja.  (Pendiente: Cambiar para que solo muestre las ventas del turno actual)
    ventas = cur.fetchall()
    cur.execute("SELECT SUM(Total) FROM ventas") # calcula el total de ventas realizadas para mostrarlo en caja como Ganacias del turno
    total_ventas = cur.fetchone()[0]
    cur.execute("""
            SELECT g.Concepto, g.Total, f.fecha, h.hora
            FROM gastos g
            JOIN Fecha f ON g.Fecha = f.ID_F    
            JOIN Hora h ON g.Hora = h.ID_H
            ORDER BY f.Fecha DESC, h.Hora DESC
    """)
    gastos = cur.fetchall()
    cur.execute("SELECT SUM(Total) FROM gastos")
    total_gastos = cur.fetchone()[0]  # Gastos funciona de forma similar a ventas, mostrando un historial de gastos realizados y 
                                      # calculando el total de gastos para mostrarlo en caja como Gastos del turno.
    return render_template('caja.html', ventas=ventas, gastos=gastos, total_ventas=total_ventas, total_gastos=total_gastos)

#----------------------GASTOS-----------------------------
@app.route('/gastos')
def gastos():
    conn = Conexion()
    cur = conn.cursor()  
    cur.execute("""
        SELECT g.ID_G, g.Concepto, g.Total, f.Fecha, h.Hora
        FROM gastos g
        JOIN Fecha f ON g.Fecha = f.ID_F    
        JOIN Hora h ON g.Hora = h.ID_H
        ORDER BY f.Fecha DESC, h.Hora DESC
    """) # Consigue los gastos realizados de la base de datos, mostrando su concepto, total, fecha y hora, ordenandolas de mas reciente a mas antiguo. (Cambiar para que solo muestre los gastos del turno actual)
    gastos = cur.fetchall()
    return render_template('gastos.html', gastos=gastos)

@app.route('/Agregar_gasto', methods=['POST'])
def agregar_gasto():
    conn = Conexion()
    concepto = request.form['concepto']
    monto = float(request.form['monto']) # Obtiene los datos del formulario para agregar un nuevo gasto a la base de datos.
    fecha = request.form['fecha']
    hora = request.form['hora']
    
    with conn.cursor() as cur:
        cur.execute("INSERT INTO Fecha (Fecha) VALUES (%s)", (fecha,)) # Almacena la fecha del gasto en la tabla Fecha, obtenida del formulario
        id_fecha = cur.lastrowid

        cur.execute("INSERT INTO Hora (Hora) VALUES (%s)", (hora,)) # Almacena la hora del gasto en la tabla Hora, junto con fecha se usan para relacionar
        id_hora = cur.lastrowid                                     # el gasto al momento especificado en el formulario.

        cur.execute("""
            INSERT INTO gastos (Concepto, Total, Fecha, Hora)
            VALUES (%s, %s, %s, %s)
        """, (concepto, monto, id_fecha, id_hora)) # Almacena el gasto en la tabla gastos, ingresando su concepto, monto, fecha y hora obtenidos del formulario.
        
        conn.commit()
    return redirect('/gastos')