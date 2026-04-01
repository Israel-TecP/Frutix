from flask import Flask, render_template, request, redirect, session, jsonify
 
app = Flask(__name__)

app.secret_key = 'clave_secreta'

# DATOS de pruebaaaa de productos  y los filtre por categoria
def obtener_productos():
    return [
        {
            "id_productos": 1,
            "nombre": "Platano",
            "precio": 10,
            "cantidad": 20,
            "imagen": "platano.png",  # (aquí va la ruta desde tu BD)
            "categoria": "frutas"
        },
        {
            "id_productos": 2,
            "nombre": "Zanahoria",
            "precio": 8,
            "cantidad": 15,
            "imagen": "zanahoria.png",
            "categoria": "verduras"
        },
        {
            "id_productos": 3,
            "nombre": "pollo",
            "precio": 50,
            "cantidad": 10,
            "imagen": "pollo.png",
            "categoria": "carne"
        },
        {
            "id_productos": 4,
            "nombre": "Azúcar",
            "precio": 12,
            "cantidad": 25,
            "imagen": "azucar.png",
            "categoria": "abarrotes"
        },
        {
            "id_productos": 5,
            "nombre": "Sal",
            "precio": 5,
            "cantidad": 30,
            "imagen": "sal.png",
            "categoria": "condimentos"
        },
        {
            "id_productos": 6,
            "nombre": "Chocolate",
            "precio": 15,
            "cantidad": 18,
            "imagen": "chocolate.png",
            "categoria": "dulces"
        }
    ]



@app.route('/')
def inicio():
    return render_template('inicio.html')

#Es temporal para revisar las vistas
@app.route('/login', methods=['POST'])
def login():
    usuario = request.form['usuario']
    password = request.form['password']

    if usuario == "admin" and password == "123":
        session['usuario'] = 'admin'
        return redirect('/login_adm')
    
    elif usuario == "gerente" and password == "123":
        session['usuario'] = 'gerente'
        return redirect('/login_gerente')
    
    elif usuario == "empleado" and password == "123":
        session['usuario'] = 'empleado'
        return redirect('/login_empleado')
    
    else:
        return "Usuario o contraseña incorrectos"
#Cerrar la sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/login_adm')
def login_admin():
    return render_template('login_adm.html')


@app.route('/login_empleado')
def login_empleado():
    return render_template('login_empleado.html')


@app.route('/login_gerente')
def login_gerente():
    return render_template('login_gerente.html')

#------------------------INVENTARIO-------------------------------
#Dependiendo de la sesión
@app.route('/inventario')
def inventario():
    if 'usuario' not in session:
        return redirect('/')
    return render_template('inventario.html', tipo_usuario=session['usuario'])
#-------------------------AGREGAR-----------------------------
@app.route('/agregar_producto')
def agregar_producto():
    if 'usuario' not in session:
        return redirect('/')
    return render_template('agregarproducto.html', tipo_usuario=session['usuario'])
#-------------------------------------------------------
@app.route('/gastos')
def gastos():
    if 'usuario' not in session:
        return redirect('/')
    return render_template('gastos.html', tipo_usuario=session['usuario'])
#-------------------------------------------------------
@app.route('/caja')
def caja():
    if 'usuario' not in session:
        return redirect('/')

    # Datos de prueba
    ventas = [
        {"concepto": "Venta #0033", "monto": 58},
        {"concepto": "Venta #0032", "monto": 154}
    ]

    gastos = [
        {"concepto": "Compra de tostadas", "monto": -180}
    ]

    # total
    movimientos = ventas + gastos

    # antes del return
    total = sum(m['monto'] for m in movimientos)
    egresos = sum(m['monto'] for m in movimientos if m['monto'] < 0)

    return render_template(
        'caja.html',
        tipo_usuario=session['usuario'],
        movimientos=movimientos,
        total=total,
        egresos=abs(egresos)
    )
#---------------------USUARIOS----------------------------------
@app.route('/usuarios')
def usuarios():
    if 'usuario' not in session or session['usuario'] != 'admin':
        return redirect('/')

    # solo para probar
    usuarios = [
        {"nombre": "Edelmy", "rol": "admin", "password": "1234"},
        {"nombre": "Xiomara", "rol": "gerente", "password": "4321"},
        {"nombre": "Cesar", "rol": "empleado", "password": "2143"},
    ]

    return render_template(
        'usuarios.html',
        tipo_usuario=session['usuario'],
        usuarios=usuarios
    )
#-------------------------------------------------------
 
@app.route('/ventas')
def ventas():
    if 'usuario' not in session:
        return redirect('/')

    session['rol'] = session['usuario']

    return render_template(
        "ventas.html",
        productos=obtener_productos()
    )
@app.route('/procesar_venta', methods=['POST'])
def procesar_venta():

    datos = request.form.to_dict(flat=False)
    total = 0

    for key, value in datos.items():
        if "productos" in key:
            cantidad = int(value[0]) if value[0] else 0

            if cantidad > 0:
                id_producto = key.split('[')[1].split(']')[0]

                # ===== BASE DE DATOS (AQUI VA LO REAL) =====
                # buscar producto
                # restar stock
                # guardar venta

                precio = 10  # simulación
                total += precio * cantidad

    return jsonify({
        "mensaje": "✅ Venta realizada correctamente",
        "total": total
    })
if __name__ == '__main__':
    app.run(debug=True)

