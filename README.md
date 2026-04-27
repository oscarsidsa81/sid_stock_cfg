Módulo técnico de Odoo (v15) para anclar IDs externos estables (ir.model.data) sobre registros de configuración de inventario que ya existen en la base de datos.

    Objetivo principal: que otros módulos personalizados puedan referenciar rutas, ubicaciones, tipos de operación, reglas y secuencias con xml_id predecibles y permanentes.

¿Qué problema resuelve?

En muchas bases de datos Odoo, parte de la configuración operativa (almacenes, rutas, reglas de aprovisionamiento, secuencias, etc.) se crea manualmente o vía importación. Cuando esos registros no tienen un xml_id estable:

    es difícil referenciarlos desde XML/Python en módulos personalizados,

    los despliegues entre entornos (DEV/TEST/PROD) son más frágiles,

    y aparecen dependencias sobre id internos que cambian según la base.

sid_stock_cfg soluciona esto creando (solo si hace falta) entradas en ir.model.data dentro del módulo sid_stock_cfg, apuntando a registros ya existentes.
Alcance funcional

El plan de anclaje incluye 299 registros repartidos en estos modelos:

    stock.rule (140)

    ir.sequence (53)

    stock.location.route (45)

    stock.location (29)

    stock.picking.type (28)

    stock.warehouse (3)

    res.partner (1)

Ejemplos de xml_id anclados:

    sid_stock_cfg.stock_picking_type__mad__outgoing__seq2__entrega_a_cliente__c1

    sid_stock_cfg.res_partner__almacen_sidsa_alcobendas__c1

Cómo funciona internamente

El módulo define un post_init_hook que recorre un plan determinista (XMLID_PLAN) y aplica la lógica de alta de ir.model.data.
Reglas de creación

Para cada entrada del plan (model, res_id, name):

    Si el registro destino no existe → no falla la instalación; se registra warning.

    Si ya existe sid_stock_cfg.name y apunta al mismo registro → no hace cambios.

    Si existe sid_stock_cfg.name pero apunta a otro registro → crea una variante segura name__id_<res_id> para evitar colisiones.

    Si no existe → crea ir.model.data con:

        module = sid_stock_cfg

        name = <name del plan>

        noupdate = True

Esta estrategia evita sobreescrituras peligrosas y mantiene idempotencia en reinstalaciones/actualizaciones.
Qué sí hace y qué no hace
Sí hace

    Crear/anclar IDs externos estables para registros existentes.

    Registrar métricas de ejecución (created, exists, collision, etc.) en logs.

    Trabajar de forma segura ante colisiones de nombre.

No hace

    No crea stock.location, stock.rule, stock.picking.type, etc. de negocio.

    No modifica campos funcionales de esos registros.

    No elimina ir.model.data previos.

Instalación

    Copia el módulo en tu addons_path.

    Actualiza listado de apps en Odoo.

    Instala sid_stock_cfg.

Dependencia declarada:

    stock

El hook se ejecuta automáticamente al instalar (post_init_hook).
Uso desde otros módulos

Una vez instalado, puedes referenciar los registros anclados por xml_id, por ejemplo:

<field name="picking_type_id" ref="sid_stock_cfg.stock_picking_type__mad__outgoing__seq2__entrega_a_cliente__c1"/>

Y en Python:

record = self.env.ref("sid_stock_cfg.stock_picking_type__mad__outgoing__seq2__entrega_a_cliente__c1")

Estructura del repositorio

    __manifest__.py: metadatos del módulo y registro del post_init_hook.

    hooks.py: plan principal (XMLID_PLAN) + lógica de creación segura en ir.model.data.

    xmlid_plan.py: copia del plan determinista para uso auxiliar/inspección.

    plan_validation.py: utilidades para validar formato y duplicados en planes.

    tests/test_plan_validation.py: pruebas unitarias de validación.

Pruebas

El repositorio incluye tests unitarios para la validación de planes de XMLID:

python -m unittest tests/test_plan_validation.py


Simulación rápida (para ver cómo queda)

Si quieres ver el comportamiento sin instalar en Odoo, puedes ejecutar una simulación local:

```bash
python examples/simulate_plan_normalization.py
```

La simulación muestra:

- Plan de entrada con casos de duplicados y tildes.
- Reporte de `validate_xmlid_plan` (`errors`, `duplicate_names`, `non_ascii_names`).
- Resúmenes compactos de duplicados/no-ASCII/renombres.
- Plan final normalizado (`execution_plan`) con nombres deterministas (`__id_<res_id>` cuando aplica).

Ejemplo esperado (extracto):

```text
res_id=101: stock_rule__vendor_madrid_cliente__seq20__mad_stock_customers__c1__id_101
res_id=102: stock_rule__vendor_madrid_cliente__seq20__mad_stock_customers__c1__id_102
res_id=103: stock_rule__madrid_preparacion__seq20__devolucion__c1__id_103
res_id=104: stock_rule__madrid_preparacion__seq20__devolucion__c1__id_104
```

Notas operativas

    Este módulo es especialmente útil como módulo ancla/base técnica en ecosistemas con múltiples personalizaciones.

    Recomendado mantenerlo pequeño y estable, y versionar cambios del XMLID_PLAN con cuidado.

    Si amplías el plan, procura seguir la convención de nombres actual para conservar legibilidad y trazabilidad.

Licencia

LGPL-3


## Lógica del módulo (para futuras migraciones)

Este módulo actúa como **ancla de XMLIDs**: no crea registros funcionales nuevos de stock, sino que fija IDs externos estables (`ir.model.data`) sobre registros que **ya existen** en la base de datos. 

### Flujo de ejecución

Al instalar el módulo, Odoo ejecuta `post_init_hook`, que recorre `XMLID_PLAN` y procesa cada elemento (`model`, `res_id`, `name`). 

Para cada entrada, aplica esta lógica:

1. **Registro destino no existe**  
   - No rompe instalación.
   - Deja warning y continúa.
   
2. **Ya existe `sid_stock_cfg.<name>` y apunta al mismo registro**  
   - No modifica nada (`exists`), manteniendo idempotencia.  
   
3. **Ya existe `sid_stock_cfg.<name>` pero apunta a otro registro**  
   - No sobrescribe.
   - Intenta crear nombre alternativo seguro: `name__id_<res_id>`. 

4. **No existe XMLID en `sid_stock_cfg`**  
   - Crea `ir.model.data` con:
     - `module = sid_stock_cfg`
     - `name = <name del plan>`
     - `model`, `res_id`
     - `noupdate = True`

Al final deja un resumen de ejecución por estados (`created`, `exists`, `created_suffixed`, `missing_record`, `collision`). 

### Qué guardar en mente para migraciones

- Este módulo sirve para **estabilizar legado** (registros ya creados manualmente/importados).
- Para registros nuevos de negocio, conviene declarar XMLID en su módulo funcional.
- El campo `current_xml_id` dentro del plan funciona como snapshot de referencia del XMLID original detectado al exportar. 