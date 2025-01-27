-- Primero eliminar datos existentes para evitar conflictos
DELETE FROM registros_detalletransaccion;
DELETE FROM registros_transaccion;
DELETE FROM registros_cuenta;
DELETE FROM registros_categoria_ecuacion_contable;

-- Insertar categorías con IDs específicos y campo id_categoria explícito
INSERT INTO registros_categoria_ecuacion_contable (id_categoria, nombre_categoria) VALUES 
(1, 'Activos'),
(2, 'Pasivos'),
(3, 'Patrimonio'),
(4, 'Costos/Gastos'),
(5, 'Ingresos');

-- Verificar que las categorías se insertaron correctamente
SELECT * FROM registros_categoria_ecuacion_contable;

-- Luego insertar las cuentas del PCGE de 2 dígitos
INSERT INTO registros_cuenta (id_cuenta, nombre_cuenta, id_categoria_id, activo) VALUES 
-- Elemento 1: ACTIVO DISPONIBLE Y EXIGIBLE (categoría_id = 1)
(10, 'Efectivo y equivalentes de efectivo', 1, true),
(11, 'Inversiones financieras', 1, true),
(12, 'Cuentas por cobrar comerciales – terceros', 1, true),
(13, 'Cuentas por cobrar comerciales – relacionadas', 1, true),
(14, 'Cuentas por cobrar al personal, accionistas y directores', 1, true),
(16, 'Cuentas por cobrar diversas – terceros', 1, true),
(17, 'Cuentas por cobrar diversas – relacionadas', 1, true),
(18, 'Servicios y otros contratados por anticipado', 1, true),
(19, 'Estimación de cuentas de cobranza dudosa', 1, true),

-- Elemento 2: ACTIVO REALIZABLE (categoría_id = 1)
(20, 'Mercaderías', 1, true),
(21, 'Productos terminados', 1, true),
(22, 'Subproductos, desechos y desperdicios', 1, true),
(23, 'Productos en proceso', 1, true),
(24, 'Materias primas', 1, true),
(25, 'Materiales auxiliares, suministros y repuestos', 1, true),
(26, 'Envases y embalajes', 1, true),
(27, 'Activos no corrientes mantenidos para la venta', 1, true),
(28, 'Existencias por recibir', 1, true),
(29, 'Desvalorización de existencias', 1, true),

-- Elemento 3: ACTIVO INMOVILIZADO (categoría_id = 1)
(30, 'Inversiones mobiliarias', 1, true),
(31, 'Propiedades de inversión', 1, true),
(32, 'Activos por derecho de uso', 1, true),
(33, 'Propiedad, planta y equipo', 1, true),
(34, 'Intangibles', 1, true),
(35, 'Activos biológicos', 1, true),
(36, 'Desvalorización de activo inmovilizado', 1, true),
(37, 'Activo diferido', 1, true),
(38, 'Otros activos', 1, true),
(39, 'Depreciación y amortización acumulados', 1, true),

-- Elemento 4: PASIVO (categoría_id = 2)
(40, 'Tributos y aportes por pagar', 2, true),
(41, 'Remuneraciones y participaciones por pagar', 2, true),
(42, 'Cuentas por pagar comerciales - terceros', 2, true),
(43, 'Cuentas por pagar comerciales - relacionadas', 2, true),
(44, 'Cuentas por pagar a los accionistas y directores', 2, true),
(45, 'Obligaciones financieras', 2, true),
(46, 'Cuentas por pagar diversas – terceros', 2, true),
(47, 'Cuentas por pagar diversas – relacionadas', 2, true),
(48, 'Provisiones', 2, true),
(49, 'Pasivo diferido', 2, true),

-- Elemento 5: PATRIMONIO (categoría_id = 3)
(50, 'Capital', 3, true),
(51, 'Acciones de inversión', 3, true),
(52, 'Capital adicional', 3, true),
(56, 'Resultados no realizados', 3, true),
(57, 'Excedente de revaluación', 3, true),
(58, 'Reservas', 3, true),
(59, 'Resultados acumulados', 3, true),

-- Elemento 6: GASTOS POR NATURALEZA (categoría_id = 4)
(60, 'Compras', 4, true),
(61, 'Variación de existencias', 4, true),
(62, 'Gastos de personal, directores y gerentes', 4, true),
(63, 'Gastos de servicios prestados por terceros', 4, true),
(64, 'Gastos por tributos', 4, true),
(65, 'Otros gastos de gestión', 4, true),
(66, 'Pérdida por medición de activos no financieros', 4, true),
(67, 'Gastos financieros', 4, true),
(68, 'Valuación y deterioro de activos y provisiones', 4, true),
(69, 'Costo de ventas', 4, true),

-- Elemento 7: INGRESOS (categoría_id = 5)
(70, 'Ventas', 5, true),
(71, 'Variación de la producción almacenada', 5, true),
(72, 'Producción de activo inmovilizado', 5, true),
(73, 'Descuentos, rebajas y bonificaciones obtenidos', 5, true),
(74, 'Descuentos, rebajas y bonificaciones concedidos', 5, true),
(75, 'Otros ingresos de gestión', 5, true),
(76, 'Ganancia por medición de activos no financieros', 5, true),
(77, 'Ingresos financieros', 5, true),
(78, 'Cargas cubiertas por provisiones', 5, true),
(79, 'Cargas imputables a cuentas de costos y gastos', 5, true),

-- Elemento 8: SALDOS INTERMEDIARIOS DE GESTIÓN (categoría_id = 5)
(80, 'Margen comercial', 5, true),
(81, 'Producción del ejercicio', 5, true),
(82, 'Valor agregado', 5, true),
(83, 'Excedente bruto de explotación', 5, true),
(84, 'Resultado de explotación', 5, true),
(85, 'Resultado antes de participaciones e impuestos', 5, true),
(88, 'Impuesto a la renta', 5, true),
(89, 'Determinación del resultado del ejercicio', 5, true),

-- Elemento 9: CONTABILIDAD ANALÍTICA DE EXPLOTACIÓN (categoría_id = 4)
(90, 'Cuentas de control', 4, true),
(91, 'Costos por distribuir', 4, true),
(92, 'Costos de producción', 4, true),
(93, 'Centros de costos', 4, true),
(94, 'Gastos administrativos', 4, true),
(95, 'Gastos de ventas', 4, true),
(96, 'Costos de servicios', 4, true),
(97, 'Costos financieros', 4, true);
