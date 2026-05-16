CREATE EXTENSION IF NOT EXISTS vector;

create table imagenes(
    imagenId serial primary key,
    url TEXT,
    vector vector(512),
    productoId integer,
    foreign key (productoId) references productos(productoId)   
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
    especificaciones jsonb,
    vector_nombre vector(512)
)
