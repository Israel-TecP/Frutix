from flask import Flask, render_template, request, redirect, session, jsonify
 
app = Flask(__name__)

import pymysql  # pymysql es una biblioteca de Python puro para conectarse a bases de datos MySQL y MariaDB.
                # Esta libreria no requiere de extenciones de C, haciendolo sensillo de instalar 

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='10092005',
    database='frutix'
)
  
@app.route('/')
def inicio():
   return render_template('inicio.html')

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
    cur = conn.cursor()
    categoria = request.args.get('categoria')
    consulta = """SELECT \"Activo\" AS ESTADO, p.nombre, p.cantidad, p.precio, p.merma, p.categoria,
                e.nombre_embolsado AS Tipo_Venta FROM frutix.embolsado e JOIN frutix.mm_prodtip pr ON pr.ID_embolsado = e.id_em
                join frutix.productos p on pr.ID_producto = p.codigo"""
    if categoria:
        consulta += " WHERE p.categoria = %s"
        cur.execute(consulta, (categoria,))
    else:
        cur.execute(consulta)
    
    inventario = cur.fetchall()
    
    return render_template('inventario.html', Inventario=inventario)
