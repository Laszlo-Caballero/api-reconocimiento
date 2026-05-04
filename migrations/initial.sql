CREATE EXTENSION IF NOT EXISTS vector;

create table imagenes(
    imagenId serial primary key,
    url varchar(255),
    vector vector(1536)   
)

create table productos (
    productoId serial primary key,
    nombre varchar(255),
    precios jsonb,
    vendido_por varchar(255),
    marca varchar(255),
    url_venta varchar(255),
    caracteristicas jsonb,
    categoria varchar(255),
    sub_categoria varchar(255),
    especificaciones jsonb
)

create table producto_imagen (
    productoId int references productos(productoId),
    imagenId int references imagenes(imagenId),
    primary key (productoId, imagenId)
)
