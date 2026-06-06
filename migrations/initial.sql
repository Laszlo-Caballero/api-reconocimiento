CREATE EXTENSION IF NOT EXISTS vector;

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
);

create table imagenes(
    imagenId serial primary key,
    url TEXT,
    vector vector(512),
    productoId integer,
    foreign key (productoId) references productos(productoId)   
);

create table tiendas (
    tiendaId serial primary key,
    nombre TEXT not null,
    latitud float,
    longitud float,
    nodo_id integer,
    grafo jsonb,
    ancho integer,
    alto integer
);

create table producto_tienda (
    productoId integer,
    tiendaId integer,
    primary key (productoId, tiendaId),
    foreign key (productoId) references productos(productoId) on delete cascade,
    foreign key (tiendaId) references tiendas(tiendaId) on delete cascade
);

