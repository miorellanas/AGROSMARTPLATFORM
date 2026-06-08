let carrito = JSON.parse(localStorage.getItem("carrito")) || []

function renderizarCarrito() {

    const carritoContainer =
        document.getElementById("carrito-container")

    carritoContainer.innerHTML = ""

    let subtotal = 0

    if(carrito.length === 0){

        carritoContainer.innerHTML =
            "<p>Carrito vacío</p>"

    }

    carrito.forEach((producto, index) => {

        subtotal += producto.precio_clp * producto.cantidad

        carritoContainer.innerHTML += `

        <div class="carrito-item">

            <h6>
                ${producto.nombre}
            </h6>
            <p class="text-muted mb-1">

                Producto ID:
                ${producto.id_producto}

            </p>

            <p class="mb-1">
                Cantidad:
                ${producto.cantidad}
            </p>

            <p class="mb-1">
                CLP $
                ${producto.precio_clp.toLocaleString()}
            </p>

            <p class="fw-bold">
                Total:
                CLP $
                ${(producto.precio_clp * producto.cantidad).toLocaleString()}
            </p>

            <button
                class="btn btn-sm btn-danger"
                onclick="eliminarProducto(${index})">

                Eliminar

            </button>

        </div>
        `
    })

    document.getElementById("subtotal").innerText =
        subtotal.toLocaleString()

    localStorage.setItem(
        "carrito",
        JSON.stringify(carrito)
    )
}

function agregarAlCarrito(producto){

    const productoExistente =

        carrito.find(

            item =>

                item.id_producto === producto.id_producto

                &&

                item.id_sucursal === producto.id_sucursal

        )

    if(productoExistente){
        if(
            productoExistente.cantidad
            >=
            producto.stock_disponible
        ){
            alert(
                "No hay stock suficiente"
            )

            return

        }


        productoExistente.cantidad += 1

    }

    else{

        if(

            producto.stock_disponible <= 0

        ){

            alert(

                "Producto sin stock"

            )

            return

        }


        producto.cantidad = 1

        carrito.push(producto)

    }


    renderizarCarrito()

}

function eliminarProducto(index){

    carrito.splice(index, 1)

    renderizarCarrito()
}

fetch("http://127.0.0.1:5000/precios")

.then(response => response.json())

.then(data => {

    const container =
        document.getElementById("productos-container")

    data.forEach(producto => {

        container.innerHTML += `

        <div class="col-md-4 mb-4">

            <div class="card shadow h-100">

                <div class="card-body d-flex flex-column">

                    <h5 class="card-title">

                        ${producto.nombre}

                    </h5>
                    
                    <p class="text-muted mb-1">

                        Producto ID:
                        ${producto.id_producto}

                    </p>

                    <p class="card-text">

                        ${producto.descripcion}

                    </p>

                    <p>

                        <strong>

                            ${producto.precio_original}
                            ${producto.moneda}

                        </strong>

                    </p>

                    <p class="text-success">

                        CLP $
                        ${producto.precio_clp.toLocaleString()}

                    </p>

                    <p>

                        Stock total:

                        <strong>

                            ${producto.stock_total}

                        </strong>

                    </p>


                    <label class="form-label">

                        Sucursal

                    </label>


                    <select

                        class="form-select mb-3"

                        id="sucursal-${producto.id_producto}"

                    >

                        ${producto.sucursales.map(

                            sucursal => `

                            <option

                                value="${sucursal.id_sucursal}"

                                data-stock="${sucursal.disponible}"

                            >
                                ${sucursal.id_sucursal}

                                ${sucursal.nombre_sucursal}

                                (

                                ${sucursal.disponible}
                                disponibles

                                )

                            </option>

                            `

                        ).join("")}

                    </select>


                    <button

                        class="btn btn-success mt-auto"

                        onclick='agregarAlCarritoConSucursal(

                            ${JSON.stringify(producto)}

                        )'

                        ${producto.stock_total <= 0 ? "disabled" : ""}

                    >

                        ${

                            producto.stock_total <= 0

                            ?

                            "Sin stock"

                            :

                            "Agregar al carrito"

                        }

                    </button>

                </div>

            </div>

        </div>

        `

    })
})

function agregarAlCarritoConSucursal(producto){

    const select =

        document.getElementById(

            `sucursal-${producto.id_producto}`

        )


    const idSucursal =

        select.value


    const stockDisponible =

        parseInt(

            select.options[

                select.selectedIndex

            ].dataset.stock

        )


    producto.id_sucursal =

        idSucursal


    producto.stock_disponible =

        stockDisponible


    agregarAlCarrito(

        producto

    )

}

renderizarCarrito()

const formularioCheckout =
    document.getElementById("checkout-form")


if (formularioCheckout) {

    console.log("Formulario encontrado")

    formularioCheckout.addEventListener(

        "submit",

        async function (e) {

            console.log("Botón presionado")

            e.preventDefault()

            const carrito =
                JSON.parse(
                    localStorage.getItem("carrito")
                ) || []


            if (carrito.length === 0) {

                alert(
                    "El carrito está vacío"
                )

                return
            }


            const cliente = {

                nombre:
                    document.getElementById(
                        "nombre"
                    ).value,

                email:
                    document.getElementById(
                        "email"
                    ).value,

                telefono:
                    document.getElementById(
                        "telefono"
                    ).value,

                calle:
                    document.getElementById(
                        "calle"
                    ).value,

                numero:
                    document.getElementById(
                        "numero"
                    ).value,

                comuna:
                    document.getElementById(
                        "comuna"
                    ).value,

                referencia:
                    document.getElementById(
                        "referencia"
                    ).value

            }


            try {

                const response =
                    await fetch(

                        "http://127.0.0.1:5000/crear_pedido",

                        {

                            method: "POST",

                            headers: {

                                "Content-Type":
                                    "application/json"

                            },

                            body: JSON.stringify({

                                cliente: cliente,
                                carrito: carrito

                            })

                        }

                    )


                const data =
                    await response.json()


                if (data.id_pedido) {

                    alert(

                        "Pedido creado correctamente\n\n" +
                        "Pedido #" +
                        data.id_pedido

                    )


                    localStorage.removeItem(
                        "carrito"
                    )


                    window.location.href =
                        "/tienda"

                }

                else {

                    alert(
                        "Error al guardar pedido"
                    )

                    console.log(data)

                }

            }

            catch (error) {

                console.log(error)

                alert(
                    "Error de conexión con el servidor"
                )

            }

        }

    )

}