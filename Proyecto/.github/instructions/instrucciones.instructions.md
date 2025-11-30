-No olvies de comentar el codigo

Objetivo General
Desarrollar una aplicación robusta en Python para registrar, gestionar y analizar gastos personales. El sistema permitirá ingresar ingresos y gastos, categorizarlos, establecer presupuestos, visualizar datos mediante gráficos y generar reportes automáticos. Además, incorporará un modelo sencillo de proyección de gastos basado en datos históricos.

Metodología
Desarrollo por fases:
  1. Planificación y Diseño
    •	Creación del diagrama entidad-relación de la base de datos Mysql.
    •	Diseño de la estructura modular del proyecto (carpetas, paquetes y componentes OOP).
  2. Implementación del Núcleo del Sistema
    •	Desarrollo de clases en programación orientada a objetos (categoría, transacción, presupuesto, gestor de base de datos).
    •	Implementación de métodos especiales (__str__, __repr__, comparaciones, etc.).
  3. Gestión de Archivos (Carga y Exportación)
    •	Importación y exportación de datos en CSV, JSON y XML.
    •	Validaciones para formatos incorrectos.
  4. Análisis y Visualización de Datos
    •	Análisis estadístico con pandas y numpy (promedios, sumatorias, variaciones por categoría y por mes).
    •	Gráficos con matplotlib, seaborn y plotnine:
      o	Gráfica de gasto mensual, comparación por categorías, Tendencias en periodos específicos.
    •	Integración de un modelo de proyección de gastos, usando:
      o	Random Forest o Regresión Lineal Simple para predecir gastos futuros basados en datos históricos.
  5. Interfaz de Usuario (CLI)
    •	Con menús interactivos, ingreso guiado de datos y mensajes de error amigables.
  6. Pruebas y Documentación
    •	Pruebas unitarias para cálculos, carga de archivos y consultas SQL.
    •	Galería de gráficos generados automáticamente.

Alcance
El proyecto permitirá registrar ingresos y gastos personales, organizar transacciones por categorías, generar estadísticas, graficar tendencias y realizar proyecciones. Incluirá almacenamiento local en SQLite, exportación/importación de datos y una interfaz de consola.
Gráficos Propuestos
  1.	Gasto mensual acumulado (línea).
  2.	Distribución por categoría (gráfico de barras o pastel).
  3.	Tendencia histórica con regresión (línea con modelo ajustado).
  4.	Proyección de gastos próximos meses (línea punteada).
Modelo de Proyecciones de Gastos
El sistema incluirá un módulo que:
  •	Recopila los gastos históricos del usuario.
  •	Aplica una Regresión Lineal Simple para estimar la tendencia.
  •	Genera una predicción de gastos futuros (ej. próximos 3–6 meses).
  •	Muestra los resultados mediante un gráfico proyectado.
El modelo tendrá:
  •	Ajuste automático según disponibilidad de datos históricos.
  •	Comparación entre gasto real y proyectado.
  
Conclusión
Esta versión de la propuesta incorpora las recomendaciones del profesor: contiene objetivos definidos, una metodología detallada, un alcance claro y elementos avanzados como análisis estadístico, visualizaciones y un modelo de proyección. El proyecto resultante será modular, escalable, útil y alineado con los criterios de la materia de Programación Avanzada en Python.


Base de datos
-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: localhost    Database: mydb
-- ------------------------------------------------------
-- Server version	8.0.44

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `categoria`
--

DROP TABLE IF EXISTS `categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categoria` (
  `Id_Categoria` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(45) NOT NULL,
  `periodicidad` varchar(45) NOT NULL,
  `tipo` varchar(45) NOT NULL COMMENT 'anual, mensual, variable',
  `descripcion` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`Id_Categoria`,`nombre`,`periodicidad`,`tipo`),
  CONSTRAINT `chk_periodicidad` CHECK ((`periodicidad` in (_utf8mb3'anual',_utf8mb3'mensual',_utf8mb3'variable')))
) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `impuesto_anual`
--

DROP TABLE IF EXISTS `impuesto_anual`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `impuesto_anual` (
  `Id_mpuesto_anual` int NOT NULL AUTO_INCREMENT,
  `anio` int DEFAULT NULL,
  `ingreso_total` double DEFAULT NULL,
  `gastos_deducibles` double DEFAULT NULL,
  `base_imponible` double DEFAULT NULL,
  `impuesto_calculado` double DEFAULT NULL,
  `impuesto_pagado` double DEFAULT NULL,
  `diferencia` double DEFAULT NULL,
  PRIMARY KEY (`Id_mpuesto_anual`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `presupuesto_especifico`
--

DROP TABLE IF EXISTS `presupuesto_especifico`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `presupuesto_especifico` (
  `Id_Presupuesto` int NOT NULL AUTO_INCREMENT,
  `anio` int DEFAULT NULL,
  `mes` int DEFAULT NULL,
  `monto` double DEFAULT NULL,
  `Categoria_Id_Categoria` int NOT NULL,
  PRIMARY KEY (`Id_Presupuesto`),
  KEY `fk_Presupuesto_Categoria1_idx` (`Categoria_Id_Categoria`),
  CONSTRAINT `fk_Presupuesto_Categoria1` FOREIGN KEY (`Categoria_Id_Categoria`) REFERENCES `categoria` (`Id_Categoria`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `presupuesto_general`
--

DROP TABLE IF EXISTS `presupuesto_general`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `presupuesto_general` (
  `Id_Presupueto_General` int NOT NULL AUTO_INCREMENT,
  `periodo` varchar(45) DEFAULT NULL,
  `anio` int DEFAULT NULL,
  `mes` int DEFAULT NULL,
  `monto_total` double DEFAULT NULL,
  PRIMARY KEY (`Id_Presupueto_General`),
  CONSTRAINT `chk_tipo` CHECK ((`periodo` in (_utf8mb4'mensual',_utf8mb4'anual')))
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `transaccion`
--

DROP TABLE IF EXISTS `transaccion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `transaccion` (
  `Id_Transaccion` int NOT NULL AUTO_INCREMENT,
  `monto` double NOT NULL,
  `cantidad` int DEFAULT NULL,
  `fecha` date DEFAULT NULL,
  `Categoria_Id_Categoria` int NOT NULL,
  `description` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`Id_Transaccion`),
  KEY `fk_Transaccion_Categoria_idx` (`Categoria_Id_Categoria`),
  CONSTRAINT `fk_Transaccion_Categoria` FOREIGN KEY (`Categoria_Id_Categoria`) REFERENCES `categoria` (`Id_Categoria`)
) ENGINE=InnoDB AUTO_INCREMENT=430 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-26 22:34:52