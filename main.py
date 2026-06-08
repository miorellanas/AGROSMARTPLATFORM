
# import pymysql
# from config import mysql
from flask import (

    jsonify,
    request,
    Flask,
    render_template,
    redirect,
    session

)
from flask_mysqldb import MySQL
from MySQLdb.cursors import DictCursor
import requests

from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.integration_api_keys import IntegrationApiKeys
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.options import WebpayOptions
from transbank.common.integration_type import IntegrationType

tx_options = WebpayOptions(

    IntegrationCommerceCodes.WEBPAY_PLUS,

    IntegrationApiKeys.WEBPAY,

    IntegrationType.TEST

)
# from app import app 

app = Flask(__name__)
app.secret_key = "agrosmart_secret_key"

# CONFIG MYSQL
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin123'
app.config['MYSQL_DB'] = 'agrosmart'
app.config['MYSQL_HOST'] = 'localhost'

mysql = MySQL(app)



def obtener_valor_dolar():

    url = "https://mindicador.cl/api/dolar"

    response = requests.get(url)

    data = response.json()

    valor_dolar = data["serie"][0]["valor"]

    return valor_dolar



@app.route('/')
def home():
    return "API funcionando"

@app.route('/tienda')
def tienda():
    return render_template('index.html')

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/login')
def login():

    return render_template(

        'login.html'

    )


@app.route('/precio/<int:id_producto>', methods=['GET'])
def obtener_precio(id_producto):

    try:

        conn = mysql.connection
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id_producto,
                nombre,
                descripcion,
                precio,
                moneda
            FROM producto
            WHERE id_producto = %s
        """, (id_producto,))

        producto = cursor.fetchone()

        if producto is None:
            return {"error": "Producto no encontrado"}, 404

        precio = float(producto[3])
        moneda = producto[4]

        precio_clp = precio

        if moneda == 'USD':

            dolar = obtener_valor_dolar()
            print ("Valor del dólar:", dolar)

            precio_clp = round(precio * dolar)

        return {
            "id_producto": producto[0],
            "nombre": producto[1],
            "descripcion": producto[2],

            "precio_original": precio,
            "moneda_original": moneda,

            "precio_convertido_clp": precio_clp,
            "valor_dolar": dolar if moneda == 'USD' else None
        }

    except Exception as e:
        return {"error": str(e)}, 500


@app.route('/precios', methods=['GET'])
def obtener_productos():

    conn = mysql.connection
    cursor = conn.cursor(DictCursor)

    cursor.execute("""

        SELECT

            p.id_producto,
            p.nombre,
            p.descripcion,
            p.precio,
            p.moneda,

            SUM(
                s.cantidad - s.stock_minimo
            ) AS stock_total

        FROM producto p

        INNER JOIN stock s

            ON p.id_producto=s.id_producto

        GROUP BY

            p.id_producto

    """)

    productos=cursor.fetchall()

    resultado=[]

    valor_dolar=obtener_valor_dolar()

    for producto in productos:

        cursor.execute("""

            SELECT

                su.id_sucursal,
                su.nombre_sucursal,

                GREATEST(

                    (
                        s.cantidad -
                        s.stock_minimo
                    ),

                    0

                ) disponible

            FROM stock s

            INNER JOIN sucursal su

            ON s.id_sucursal =
            su.id_sucursal

            WHERE s.id_producto = %s

        """,

        (

            producto["id_producto"],

        ))

        sucursales=cursor.fetchall()


        precio=float(
            producto["precio"]
        )


        if producto["moneda"]=="USD":

            precio_clp=round(

                precio*
                valor_dolar

            )

        else:

            precio_clp=precio


        resultado.append({

            "id_producto":
            producto["id_producto"],

            "nombre":
            producto["nombre"],

            "descripcion":
            producto["descripcion"],

            "precio_original":
            precio,

            "moneda":
            producto["moneda"],

            "precio_clp":
            precio_clp,

            "stock_total":

            max(
                0,
                producto["stock_total"]
            ),

            "sucursales":
            sucursales

        })

    return jsonify(resultado)

@app.route(

    '/iniciar_sesion',

    methods=['POST']

)
def iniciar_sesion():

    try:

        data = request.json

        email = data['email']

        password = data['password']


        conn = mysql.connection

        cursor = conn.cursor(
            DictCursor
        )


        query = """

            SELECT

                id_usuario,
                nombre,
                email,
                rol,
                id_sucursal

            FROM usuario

            WHERE email=%s
            AND password=%s

        """


        values = (

            email,
            password

        )


        cursor.execute(

            query,
            values

        )


        usuario = cursor.fetchone()

        cursor.close()


        if usuario:

            session["usuario"] = {

                "id_usuario":

                usuario["id_usuario"],

                "nombre":

                usuario["nombre"],

                "email":

                usuario["email"],

                "rol":

                usuario["rol"],

                "id_sucursal": 

                usuario["id_sucursal"]

            }


            if usuario["rol"] == "logistica":

                return jsonify({

                    "success": True,

                    "redirect":

                    "/panel_logistica"

                })


            elif usuario["rol"] == "vendedor":

                return jsonify({

                    "success": True,

                    "redirect":

                    "/panel/vendedor"

                })
            
            elif usuario["rol"] == "cobranzas": 
                    
                    return jsonify({

                    "success": True,

                    "redirect":

                    "/panel_cobranzas"

                })

            else:

                return jsonify({

                    "success": False,

                    "message":

                    "Rol inválido"

                })


        return jsonify({

            "success": False,

            "message":

            "Credenciales incorrectas"

        })


    except Exception as e:

        print(e)

        return jsonify({

            "error": str(e)

        }), 500


@app.route('/logout')
def logout():

    session.clear()

    return redirect(

        '/login'

    )

@app.route('/panel/logistica')
def panel_logistica_obsoleto():

    print(session["usuario"])

    if "usuario" not in session:

        return redirect(

            '/login'

        )


    if session["usuario"]["rol"] != "logistica":

        return redirect(

            '/login'

        )


    return render_template(

        'panel_logistica.html',

        usuario=session["usuario"]

    )

@app.route('/panel/vendedor')
def panel_vendedor():

    if "usuario" not in session:

        return redirect(

            '/login'

        )


    if session["usuario"]["rol"] != "vendedor":

        return redirect(

            '/login'

        )


    return render_template(

        'panel_vendedor.html',

        usuario=session["usuario"]

    )

@app.route("/panel_cobranzas")
def panel_cobranzas():

    if "usuario" not in session:

        return redirect("/login")


    if session["usuario"]["rol"] != "cobranzas":

        return redirect("/")


    conn = mysql.connection

    cursor = conn.cursor()


    query = """

        SELECT

            p.id_pedido,
            c.nombre,
            p.total,
            p.estado,
            p.tipo_pedido

        FROM pedido p

        INNER JOIN cliente c

        ON p.id_cliente =
        c.id_cliente

        ORDER BY p.id_pedido DESC

    """


    cursor.execute(query)

    pedidos = cursor.fetchall()

    cursor.close()


    return render_template(

        "panel_cobranzas.html",

        pedidos=pedidos,

        usuario=session["usuario"]

    )


@app.route(
    "/aprobar_pedido/<int:id_pedido>",
    methods=["POST"]
)
def aprobar_pedido(id_pedido):

    try:

        if "usuario" not in session:

            return jsonify({

                "error":"No autorizado"

            }),401


        if session["usuario"]["rol"] != "cobranzas":

            return jsonify({

                "error":"Sin permisos"

            }),403


        conn = mysql.connection

        cursor = conn.cursor()


        query = """

            UPDATE pedido

            SET estado='pagado'

            WHERE id_pedido=%s

        """


        cursor.execute(

            query,
            (id_pedido,)

        )


        conn.commit()

        cursor.close()


        return jsonify({

            "mensaje":"Pedido aprobado"

        })

    except Exception as e:

        print(e)

        return jsonify({

            "error":str(e)

        }),500


@app.route('/productos', methods=['POST'])
def create_producto():
    try:
        data = request.get_json(force=True)
        print("DATA:", data)

        conn = mysql.connection
        cursor = conn.cursor(DictCursor)

        query = """
        INSERT INTO producto (id_producto, nombre, descripcion, precio, id_familia)
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            data['id_producto'],
            data['nombre'],
            data.get('descripcion'),
            data['precio'],
            data.get('id_familia')
        )

        cursor.execute(query, values)
        conn.commit()
        return jsonify({"mensaje": "Producto creado"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    # finally:
    #     cursor.close()
    #     conn.close()

    try:
        data = request.get_json(force=True)
        print("DATA:", data)

        conn = mysql.connection
        cursor = conn.cursor(DictCursor)

        query = """
        INSERT INTO producto (id_producto, nombre, descripcion, precio, id_familia)
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            data['id_producto'],
            data['nombre'],
            data.get('descripcion'),
            data['precio'],
            data.get('id_familia')
        )

        cursor.execute(query, values)
        conn.commit()
        return jsonify({"mensaje": "Producto creado"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    # finally:
    #     cursor.close()
    #     conn.close()

@app.route('/stock', methods=['POST'])
def create_stock():
    try:
        data = request.get_json(force=True)
        print("DATA:", data)

        conn = mysql.connection
        cursor = conn.cursor(DictCursor)

        query = """
        INSERT INTO stock (id_producto, id_sucursal, cantidad, stock_minimo, ultima_actualizacion)
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            data['id_producto'],
            data['id_sucursal'],
            data['cantidad'],
            data.get('stock_minimo'),
            data.get('ultima_actualizacion')
        )

        cursor.execute(query, values)
        conn.commit()
        return jsonify({"mensaje": "Stock creado"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500                                      
    # finally:
    #     cursor.close()    
    #     conn.close()

@app.route('/stock', methods=['GET'])
def get_stock():
    try:
        conn = mysql.connection
        cursor = conn.cursor(DictCursor)
        print(obtener_valor_dolar())

        cursor.execute("SELECT producto.id_producto, producto.nombre, sucursal.nombre_sucursal, stock.cantidad FROM stock JOIN producto ON stock.id_producto = producto.id_producto JOIN sucursal ON stock.id_sucursal = sucursal.id_sucursal")
        data = cursor.fetchall()

        if data:
            return jsonify(data)
        else:
            return jsonify({"mensaje": "Stock no encontrado"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    # finally:
    #     cursor.close()
    #     conn.close()    
    

@app.route('/stock_sucursal/<int:id_sucursal>', methods=['GET'])
def get_stock_sucursal(id_sucursal):    
    try:
        conn = mysql.connection
        cursor = conn.cursor(DictCursor)

        cursor.execute("SELECT st.id_producto, p.nombre, su.nombre_sucursal, st.cantidad FROM stock st RIGHT JOIN sucursal su ON st.id_sucursal = su.id_sucursal JOIN producto p ON st.id_producto = p.id_producto WHERE st.id_sucursal = %s", (id_sucursal,))
        data = cursor.fetchall()

        if data:
            return jsonify(data)
        else:
            return jsonify({"mensaje": "Stock no encontrado"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    # finally:
    #     cursor.close()
    #     conn.close()    

@app.route('/stock_producto/<int:id_producto>', methods=['GET'])
def get_stock_producto(id_producto):    
    try:
        conn = mysql.connection
        cursor = conn.cursor(DictCursor)

        cursor.execute("SELECT st.id_producto, p.nombre, su.nombre_sucursal, st.cantidad FROM stock st RIGHT JOIN sucursal su ON st.id_sucursal = su.id_sucursal JOIN producto p ON st.id_producto = p.id_producto WHERE st.id_producto = %s", (id_producto,))
        data = cursor.fetchall()

        if data:
            return jsonify(data)
        else:
            return jsonify({"mensaje": "Stock no encontrado"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    # finally:
    #     cursor.close()
    #     conn.close()     
    # 
@app.route('/stock/<int:id_producto>/<int:id_sucursal>', methods=['GET'])
def get_stock_producto_sucursal(id_producto, id_sucursal):    
    try:
        conn = mysql.connection 
        cursor = conn.cursor()

        query = """
        SELECT 
            st.id_producto,
            p.nombre,
            su.nombre_sucursal,
            st.cantidad,
            st.stock_minimo,
            CASE
                WHEN st.cantidad = 0 THEN 'sin_stock'
                WHEN st.cantidad <= st.stock_minimo THEN 'reponer'
                ELSE 'suficiente'
            END as estado
        FROM stock st
        JOIN producto p ON st.id_producto = p.id_producto
        JOIN sucursal su ON st.id_sucursal = su.id_sucursal
        WHERE st.id_producto = %s AND st.id_sucursal = %s
        """

        cursor.execute(query, (id_producto, id_sucursal))
        result = cursor.fetchone()

        if result:
            return jsonify({
                "id_producto": result[0],
                "nombre_producto": result[1],
                "sucursal": result[2],
                "cantidad": result[3],
                "stock_minimo": result[4],
                "estado": result[5]
            })
        else:
            return jsonify({"mensaje": "Stock no encontrado"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/productos/<int:id>', methods=['GET'])
def get_producto(id):
    try:
        conn = mysql.connection
        cursor = conn.cursor(DictCursor)

        cursor.execute("SELECT * FROM producto WHERE id_producto = %s", (id,))
        data = cursor.fetchone()

        if data:
            return jsonify(data)
        else:
            return jsonify({"mensaje": "Producto no encontrado"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    # finally:
    #     cursor.close()
    #     conn.close()    
    
@app.route('/productos', methods=['GET'])
def get_productos():
    try:
        conn = mysql.connection
        cursor = conn.cursor(DictCursor)

        cursor.execute("SELECT * FROM producto")
        data = cursor.fetchall()

        if data:
            return jsonify(data)
        else:
            return jsonify({"mensaje": "Producto no encontrado"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    # finally:
    #     cursor.close()
    #     conn.close() 


@app.route('/sub_stock/<int:id_producto>/<int:id_sucursal>', methods=['POST'])
def subtract_stock(id_producto, id_sucursal):
    try:
        data = request.json

        conn = mysql.connection
        cursor = conn.cursor(DictCursor)

        # actualizar el stock 
        query = """
        UPDATE stock
        SET cantidad = cantidad - %s
        WHERE id_producto=%s 
        AND id_sucursal=%s 
        AND (cantidad - %s) >= 0
        """
        values = (
            data['cantidad'],
            id_producto,
            id_sucursal,
            data['cantidad']
        )

        cursor.execute(query, values)

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Stock insuficiente o producto inexistente"
            }), 400

        # test resultado
        query_estado = """
        SELECT cantidad, stock_minimo,
        CASE
            WHEN cantidad = 0 THEN 'sin_stock'
            WHEN cantidad <= stock_minimo THEN 'reponer'
            ELSE 'suficiente'
        END as estado
        FROM stock
        WHERE id_producto=%s AND id_sucursal=%s
        """

        cursor.execute(query_estado, (id_producto, id_sucursal))
        result = cursor.fetchone()

        conn.commit()

        return jsonify({
            "mensaje": "Stock actualizado",
            "cantidad": result[0],
            "estado": result[2]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500   

@app.route('/add_stock/<int:id_producto>/<int:id_sucursal>', methods=['POST'])
def add_stock(id_producto, id_sucursal):
    try:
        data = request.json

        conn = mysql.connection
        cursor = conn.cursor()
    
        query = """
        UPDATE stock
        SET cantidad = cantidad + %s
        WHERE id_producto=%s AND id_sucursal=%s AND (cantidad + %s) >= 0
        """

        values = (
            data['cantidad'],
            id_producto,
            id_sucursal,
            data['cantidad']
        )
        cursor.execute(query, values)

        if cursor.rowcount == 0:
            return jsonify({
                "error": "No se pudo actualizar el stock (quedaría negativo o no existe el registro)"
            }), 400

        conn.commit()

        return jsonify({"mensaje": "Stock actualizado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500      


    except Exception as e:
        return jsonify({"error": str(e)}), 500
    # finally:
    #     cursor.close()
    #     conn.close()   



    
@app.route('/productos/<int:id>', methods=['PUT'])
def update_producto(id):
    try:
        data = request.json

        conn = mysql.connection
        cursor = conn.cursor()

        query = """
        UPDATE producto
        SET nombre=%s, descripcion=%s, precio=%s, id_familia=%s
        WHERE id_producto=%s
        """

        values = (
            data['nombre'],
            data.get('descripcion'),
            data['precio'],
            data.get('id_familia'),
            id
        )

        cursor.execute(query, values)
        conn.commit()

        return jsonify({"mensaje": "Producto actualizado"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # finally:
    #     cursor.close()
    #     conn.close()
    
@app.route('/productos/<int:id>', methods=['DELETE'])
def delete_producto(id):
    try:
        conn = mysql.connection
        cursor = conn.cursor()

        cursor.execute("DELETE FROM producto WHERE id_producto = %s", (id,))
        conn.commit()

        return jsonify({"mensaje": "Producto eliminado"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    # finally:
    #     cursor.close()
    #     conn.close()

@app.route('/crear_pedido', methods=['POST'])
def crear_pedido():

    try:

        data = request.json

        cliente = data['cliente']

        carrito = data['carrito']


        conn = mysql.connection

        cursor = conn.cursor()


        # =========================
        # CREAR CLIENTE
        # =========================

        query_cliente = """
            INSERT INTO cliente
            (
                nombre,
                email,
                telefono
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
        """

        values_cliente = (

            cliente['nombre'],
            cliente['email'],
            cliente['telefono']

        )

        cursor.execute(

            query_cliente,
            values_cliente

        )

        id_cliente = cursor.lastrowid


        # =========================
        # CREAR DIRECCION
        # =========================

        query_direccion = """
            INSERT INTO direccion
            (
                id_cliente,
                calle,
                numero,
                id_comuna,
                referencia
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """

        values_direccion = (

            id_cliente,

            cliente['calle'],

            cliente['numero'],

            cliente['comuna'],

            cliente['referencia']

        )

        cursor.execute(

            query_direccion,
            values_direccion

        )


        # =========================
        # VALIDAR STOCK
        # =========================

        for producto in carrito:

            query_stock = """

                SELECT

                    cantidad,
                    stock_minimo

                FROM stock

                WHERE id_producto=%s
                AND id_sucursal=%s

            """

            values_stock = (

                producto['id_producto'],
                producto['id_sucursal']

            )

            cursor.execute(

                query_stock,
                values_stock

            )

            stock = cursor.fetchone()


            disponible = (

                stock[0]
                -
                stock[1]

            )


            if producto['cantidad'] > disponible:

                return jsonify({

                    "error":

                    f"Stock insuficiente para el producto {producto['nombre']}"

                }), 400


        # =========================
        # CALCULAR TOTAL
        # =========================

        total = 0

        for producto in carrito:

            subtotal = (

                producto['precio_clp']
                *
                producto['cantidad']

            )

            total += subtotal


        # =========================
        # TIPO PEDIDO
        # =========================

        estado_pedido = (

            "pendiente_pago"

        )

        tipo_pedido = (

            "cliente_web"

        )


        if "usuario" in session:

            if session["usuario"]["rol"] == "vendedor":

                estado_pedido = (

                    "pendiente_aprobacion"

                )

                tipo_pedido = (

                    "venta_vendedor"

                )


        # =========================
        # CREAR PEDIDO
        # =========================

        query_pedido = """
            INSERT INTO pedido
            (
                id_cliente,
                total,
                estado,
                tipo_pedido
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
        """

        values_pedido = (

            id_cliente,
            total,
            estado_pedido,
            tipo_pedido

        )

        cursor.execute(

            query_pedido,
            values_pedido

        )

        id_pedido = cursor.lastrowid


        # =========================
        # DETALLE PEDIDO
        # =========================

        for producto in carrito:

            query_detalle = """
                INSERT INTO detalle_pedido
                (
                    id_pedido,
                    id_producto,
                    id_sucursal,
                    cantidad,
                    precio_unitario
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """

            values_detalle = (

                id_pedido,

                producto['id_producto'],

                producto['id_sucursal'],

                producto['cantidad'],

                producto['precio_clp']

            )

            cursor.execute(

                query_detalle,
                values_detalle

            )


        conn.commit()


        # =========================
        # VENTA VENDEDOR
        # =========================

        if "usuario" in session:

            if session["usuario"]["rol"] == "vendedor":

                cursor.close()

                return jsonify({

                    "id_pedido": id_pedido,

                    "tipo": "venta_vendedor",

                    "message":

                    "Venta generada correctamente"

                })


        # =========================
        # WEBPAY
        # =========================

        buy_order = str(id_pedido)

        session_id = str(id_cliente)

        amount = int(total)

        return_url = (

            "http://127.0.0.1:5000/retorno_pago"

        )


        transaction = Transaction(

            tx_options

        )

        response = transaction.create(

            buy_order,
            session_id,
            amount,
            return_url

        )


        cursor.close()


        return jsonify({

            "id_pedido": id_pedido,

            "url": response["url"],

            "token": response["token"]

        })


    except Exception as e:

        print(e)

        return jsonify({

            "error": str(e)

        }), 500
    
@app.route("/panel_logistica")
def panel_logistica():

    if "usuario" not in session:

        return redirect("/login")


    if session["usuario"]["rol"] != "logistica":

        return redirect("/")


    id_sucursal = session["usuario"]["id_sucursal"]


    conn = mysql.connection

    cursor = conn.cursor()


    query = """

        SELECT

            p.id_producto,
            p.nombre,

            s.cantidad,
            s.stock_minimo,

            (
                s.cantidad -
                s.stock_minimo
            ) disponible,

            su.nombre_sucursal

        FROM stock s

        INNER JOIN producto p

        ON s.id_producto =
        p.id_producto

        INNER JOIN sucursal su

        ON s.id_sucursal =
        su.id_sucursal

        WHERE s.id_sucursal = %s

        ORDER BY p.nombre

    """


    cursor.execute(

        query,
        (id_sucursal,)

    )


    productos = cursor.fetchall()


    cursor.close()


    return render_template(

        "panel_logistica.html",

        productos=productos,

        usuario=session["usuario"]

    )




@app.route("/retorno_pago", methods=["GET"])
def retorno_pago():

    try:

        token = request.args.get(
            "token_ws"
        )

        if "usuario" in session:

            if session["usuario"]["rol"] == "vendedor":

                cursor.close()

                return jsonify({

                    "id_pedido": id_pedido,

                    "tipo": "venta_vendedor",

                    "message":

                    "Venta generada correctamente"

                })
        
        transaction = Transaction(
            tx_options
        )


        response = transaction.commit(
            token
        )


        conn = mysql.connection
        cursor = conn.cursor()


        id_pedido = response["buy_order"]


        if response["status"] == "AUTHORIZED":

            query = """
                UPDATE pedido
                SET estado = %s
                WHERE id_pedido = %s
            """

            values = (

                "pagado",
                id_pedido

            )
            
            query_productos = """

                SELECT

                    id_producto,

                    id_sucursal,

                    cantidad

                FROM detalle_pedido

                WHERE id_pedido=%s

            """

            cursor.execute(

                query_productos,

                (

                    id_pedido,

                )

            )

            productos=cursor.fetchall()


            for producto in productos:

                query_update = """

                    UPDATE stock

                    SET

                        cantidad = cantidad - %s

                    WHERE

                        id_producto = %s

                    AND

                        id_sucursal = %s

                """

                cursor.execute(

                    query_update,

                    (

                        producto[2],

                        producto[0],

                        producto[1]

                    )

                )

        else:

            query = """
                UPDATE pedido
                SET estado = %s
                WHERE id_pedido = %s
            """

            values = (

                "rechazado",
                id_pedido

            )


        cursor.execute(
            query,
            values
        )

        conn.commit()

        cursor.close()


        return f"""

        <html>

        <head>

            <title>
                Pago AGROSMART
            </title>

            <link
                href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
                rel="stylesheet"
            >

        </head>

        <body class="bg-light">

            <div class="container mt-5">

                <div class="card shadow">

                    <div class="card-body text-center">

                        <h2>

                            Pago procesado

                        </h2>

                        <hr>

                        <h4>

                            Pedido #{id_pedido}

                        </h4>

                        <p>

                            Estado:

                            {response["status"]}

                        </p>

                        <p>

                            Monto:

                            CLP $
                            {response["amount"]}

                        </p>

                        <a
                            href="/tienda"
                            class="btn btn-success"
                        >

                            Volver a tienda

                        </a>

                    </div>

                </div>

            </div>

            <script>

                localStorage.removeItem(

                    "carrito"

                )

            </script>

        </body>

        </html>

        """

    except Exception as e:

        print(e)

        return jsonify({

            "error": str(e)

        }),500

if __name__ == "__main__":
    app.run(debug=True)


# bases json para pruebas:

# {
# 	"id_producto": 240083913,
# 	"nombre": "Regaderas RB305",
# 	"descripcion": "Regadera automatica de corto alcance",
# 	"precio": 19990,
# 	"id_familia": null
# }