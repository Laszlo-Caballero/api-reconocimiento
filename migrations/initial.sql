CREATE EXTENSION IF NOT EXISTS vector;

create table imagenes(
    imagenId serial primary key,
    url TEXT,
    vector vector(512)   
)

create table productos (
    productoId serial primary key,
    nombre TEXT,
    precios jsonb,
    vendido_por varchar(255),
    marca varchar(255),
    url_venta TEXT,
    caracteristicas jsonb,
    categoria varchar(255),
    sub_categoria varchar(255),
    especificaciones jsonb
)

create table producto_imagen (
    producto_imagenId serial primary key,
    productoId int references productos(productoId),
    imagenId int references imagenes(imagenId)
)
