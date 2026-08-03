

<div align="center" dir="rtl">

<a href="https://ahmadmdm.github.io/hr-saudi-arabia-erpnext/">
  <img src="docs/images/readme-hero.svg" alt="Saudi HR — El empleado es un viaje, no un registro" width="100%">
</a>

<br>

[![Version](https://img.shields.io/badge/version-1.18.0-49D5A2?style=flat-square&labelColor=06161C)](https://github.com/ahmadmdm/hr-saudi-arabia-erpnext/releases/tag/v1.18.0)
![ERPNext](https://img.shields.io/badge/ERPNext-v15-DFA96A?style=flat-square&labelColor=06161C)
![Arabic first](https://img.shields.io/badge/Arabic-first-E9E2D0?style=flat-square&labelColor=06161C)
![HRMS](https://img.shields.io/badge/HRMS-not_required-49D5A2?style=flat-square&labelColor=06161C)
[![Quality](https://img.shields.io/github/actions/workflow/status/ahmadmdm/hr-saudi-arabia-erpnext/quality.yml?branch=version-15&style=flat-square&label=quality&labelColor=06161C)](https://github.com/ahmadmdm/hr-saudi-arabia-erpnext/actions/workflows/quality.yml)

### Sistema operativo del ciclo del empleado saudí dentro de ERPNext

**[Ingresa a la experiencia interactiva](https://ahmadmdm.github.io/hr-saudi-arabia-erpnext/)** &nbsp;·&nbsp; [Instala ahora](#التثبيت) &nbsp;·&nbsp; [Descubre la trayectoria](#مدار-الموظف) &nbsp;·&nbsp; [Contacto](#صاحب-المشروع)

</div>

---

## El empleado no es una fila en una tabla

Es un contrato que afecta al salario, una asistencia que incide en los beneficios, un permiso con política, un documento con fecha y una decisión que debe permanecer interpretable.

**Saudi HR** conecta esta trayectoria dentro de ERPNext en un solo expediente y una capa operativa en árabe independiente de HRMS. El resultado no son más formularios; es una única verdad operativa desde la cual el equipo conoce: ¿qué ocurrió? ¿por qué? ¿y quién tiene el siguiente paso?

> [!IMPORTANT]
> La aplicación es una herramienta de operación y cumplimiento basada en los requisitos laborales saudíes, y no un sustituto de la consulta legal para casos específicos.

## Trayectoria del empleado

```text
                              ┌──────── Contrato ────────┐
                       Asistencia │                       │ Cumplimiento
                              │   Expediente completo      │
                       Permiso  │  Identidad · Trabajo · Impacto    │ Salario
                              └──────── Salida ───────┘
```

| Etapa | Lo que conecta el sistema | Lo que deja para revisión |
|:--|:--|:--|
| **Contratación y contrato** | Solicitud, candidato, evaluación, oferta, contrato y período de prueba | Decisión documentada e inicio definido |
| **Operación diaria** | Turno, ubicación, asistencia, ausencias y permisos personalizados | Movimiento y beneficios interpretables |
| **Salario y obligaciones** | Proceso, ajustes, préstamos, GOSI, WPS y rangos | Cálculo y salida del sistema auditables |
| **Relaciones y cumplimiento** | Políticas, declaraciones, investigaciones, quejas e inspecciones | Responsable, fecha y evidencia de cierre |
| **Salida** | Terminación, liquidación, entrevista, EOSB y cierre final | Fin de servicio sin brechas |

## Ve el sistema en acción

<a href="https://ahmadmdm.github.io/hr-saudi-arabia-erpnext/#journey">
  <img src="docs/images/professional-hr-hub-desktop.png" alt="Centro de operaciones profesional en Saudi HR" width="100%">
</a>

<p align="center" dir="rtl"><sub>Centro de operaciones en vivo: prioridades diarias, expediente completo y cumplimiento en una sola vista.</sub></p>

## التثبيت

Este paquete está diseñado para **ERPNext v15**. Paquete probado: Saudi HR `1.18.0` — versión `v1.18.0`.

```bash
cd ~/frappe-bench
bench get-app --branch version-15 https://github.com/ahmadmdm/hr-saudi-arabia-erpnext.git
bench --site your-site.local install-app saudi_hr
bench --site your-site.local migrate
bench build --app saudi_hr
bench restart
```

Luego comienza desde:

```text
/app/saudi-hr                Espacio de trabajo
/app/professional-hr-hub     Centro de operaciones
/app/attendance-action-hub   Acciones de asistencia
/mobile-attendance           Asistencia móvil
```

> [!TIP]
> ¿Usas ERPNext v16? Ve a la [rama version-16](https://github.com/ahmadmdm/hr-saudi-arabia-erpnext/tree/version-16), o selecciona tu versión dentro del [tutorial interactivo](https://ahmadmdm.github.io/hr-saudi-arabia-erpnext/#install).

## Primer ciclo real

1. **Construye la estructura:** empresa, sucursales, departamentos, puestos, ubicaciones y permisos.
2. **Define las políticas:** turnos, permisos, contratos y alertas de documentos.
3. **Agrega un empleado de prueba:** completa su identidad, contrato, documentos y salario.
4. **Ejecuta un día real:** asistencia, luego solicitud de permiso y aprobación, luego cálculo de salario de prueba.
5. **Cierra el ciclo:** revisa los informes, alertas y salidas, luego prueba la copia de seguridad.

Comienza la ruta guiada según tu rol desde la **[Guía de operación en vivo](https://ahmadmdm.github.io/hr-saudi-arabia-erpnext/#tutorial)**.

## Documentación que necesitas cuando la requieras

- [Instalación](docs/installation.md) — Requisitos, pasos y verificación.
- [Despliegue](docs/deployment.md) — Rutas, permisos y preparación.
- [Personalización de permisos](docs/leave-policy-customization.md) — Política general, de departamento o de empleado.
- [Datos de demostración](docs/demo-data.md) — Ciclo seguro antes de producción.
- [Matriz de cumplimiento](docs/LEGAL_COMPLIANCE_MATRIX.md) — Del requisito a la función y la evidencia.
- [Plan de pruebas](docs/COMPREHENSIVE_TEST_PLAN.md) y [resultados](docs/COMPREHENSIVE_TEST_RESULTS.md).
- [Recuperación ante desastres](docs/DISASTER_RECOVERY.md) y [contrato de dependencias](DEPENDENCIES.md).

## Límites claros

- La integración en vivo con Qiwa, GOSI, Madad y Muqeem requiere credenciales y canales autorizados por las entidades.
- Las salidas gubernamentales se preparan y revisan dentro del sistema antes del envío.
- Los datos de salarios y el expediente completo están controlados por permisos a nivel de documento y registro.
- Las tareas programadas monitorean contratos, residencias, permisos y plazos legales.

## Contribución y calidad

```bash
python scripts/validate_quality.py
ruff check saudi_hr --select F
pytest -q
git diff --check
```

Envía el problema con la versión, pasos para reproducir, resultado esperado y evidencia visual si está disponible a través de [GitHub Issues](https://github.com/ahmadmdm/hr-saudi-arabia-erpnext/issues).

## Propietario del proyecto

<div dir="rtl">

**ahmad**<br>
Propietario del proyecto y supervisor de la experiencia de RRHH saudí.<br>
[ahmad8@outlook.com](mailto:ahmad8@outlook.com)

</div>

---

<div align="center" dir="rtl">

**El contrato define el salario · La asistencia define los beneficios · El cumplimiento define el plazo**

[Experiencia interactiva](https://ahmadmdm.github.io/hr-saudi-arabia-erpnext/) · [Versiones](https://github.com/ahmadmdm/hr-saudi-arabia-erpnext/releases) · [GPL-3.0](LICENSE)

</div>
