"""
Cita Previa Extranjeria Monitor Bot
Uses real data from data.js - provinces, offices, tramites
"""
import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv

import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler,
)

load_dotenv()
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "60"))
BASE_URL = "https://icp.administracionelectronica.gob.es/icpco"

# Conversation states
SELECT_PROVINCE, SELECT_OFFICE, SELECT_CATEGORY, SELECT_TRAMITE, CONFIRM = range(5)

# In-memory user configs
user_configs: dict = {}

# ─── DATA FROM data.js ────────────────────────────────────────────────────────
PROVINCES = {
    "A Coruña": "15",
    "Albacete": "02",
    "Alicante": "03",
    "Almería": "04",
    "Araba": "01",
    "Asturias": "33",
    "Badajoz": "06",
    "Barcelona": "08",
    "Bizkaia": "48",
    "Burgos": "09",
    "Cantabria": "39",
    "Castellón": "12",
    "Ceuta": "51",
    "Ciudad Real": "13",
    "Cuenca": "16",
    "Cáceres": "10",
    "Cádiz": "11",
    "Córdoba": "14",
    "Gipuzkoa": "20",
    "Girona": "17",
    "Granada": "18",
    "Guadalajara": "19",
    "Huelva": "21",
    "Huesca": "22",
    "Illes Balears": "07",
    "Jaén": "23",
    "La Rioja": "26",
    "Las Palmas": "35",
    "León": "24",
    "Lleida": "25",
    "Lugo": "27",
    "Madrid": "28",
    "Melilla": "52",
    "Murcia": "30",
    "Málaga": "29",
    "Navarra": "31",
    "Ourense": "32",
    "Palencia": "34",
    "Pontevedra": "36",
    "S.Cruz Tenerife": "38",
    "Salamanca": "37",
    "Segovia": "40",
    "Sevilla": "41",
    "Soria": "42",
    "Tarragona": "43",
    "Teruel": "44",
    "Toledo": "45",
    "Valencia": "46",
    "Valladolid": "47",
    "Zamora": "49",
    "Zaragoza": "50",
    "Ávila": "05",
}

OFFICES_BY_PROVINCE = {
    "01": [
        "CNP Comisaría Oficina de tramitación, Olaguibel, 15, Vitoria-Gasteiz",
        "INSS - Araba - CAISS Nº 0, C/ Eduardo Dato, 36, Vitoria-Gasteiz",
        "Oficina de Correos - VITORIA-GASTEIZ OP-0100010, KAL POSTAS, 9, VITORIA-GASTEIZ",
        "Subdelegación del Gobierno en Alava, Olaguibel, 1, Vitoria-Gasteiz",
    ],
    "02": [
        "CNP ALBACETE BPEF, Buen Pastor, 1, Albacete",
        "CNP HELLIN, FORTUNATO ARIAS, 2, HELLIN",
        "CNP TARJETAS Expedición, CALDERON DE LA BARCA, 2, ALBACETE",
        "Oficina de Correos-ALBACETE OP-200010, DIONISIO GUARDIOLA, 24-26, ALBACETE",
        "TGSS - Administración 02/01, Avenida de España, 27, Albacete",
    ],
    "03": [
        "CNP Alcoy, Placeta Les Xiques, S/N, Alcoy",
        "CNP Alicante NIE, Ebanistería, 4-6, Alicante",
        "CNP Alicante TIE, Campo de Mirra, 6, Alicante",
        "CNP Benidorm, Apolo XI, 36, Benidorm",
        "CNP Benidorm TIE, Callosa D`Ensarria, 2, Benidorm",
        "CNP Comisaría Provincial, C/ Isabel la Católica, 25, Alicante",
        "CNP Denia, Avda Marquesado, 53, Denia",
        "CNP Elche, El Abeto, 1, Elche",
        "CNP Elda, Lamberto Amat, 26, Elda",
        "CNP Orihuela, Sol, 34, Orihuela",
        "CNP Orihuela Costa, C/ Flores, 5, Orihuela Costa",
        "CNP Torrevieja, Arquitecto Larramendi, 3, Torrevieja",
        "INSS - Alicante - CAISS Nº 1, C/ Doctor Ayela, 26-28, Alicante",
        "INSS - Alicante - CAISS Nº 3, C/ Mayor, 3, Alicante",
        "OEX ALICANTE, EBANISTERIA, 4-6, ALICANTE",
        "OEX ALTEA, SAN ISIDRO LABRADOR, 1, ALTEA",
    ],
    "04": [
        "Almería OUE, C/ Marruecos, 1, Almeria",
        "CNP ALMERIA, AVENIDA DEL MEDITERRANEO, 201, ALMERIA",
        "CNP EL EJIDO, Avenida del bulevar, 117, El Ejido",
        "CNP ROQUETAS DE MAR, Avda. Curro Romero, 46, Roquetas de Mar",
        "INSS - Almería - CAISS Nº 1, Ctra. Sierra de Alhamilla, 170, Almería",
        "Oficina de Correos-AGUADULCE - 0472001, AV CARLOS III, 649, ROQUETAS DE MAR",
        "Oficina de Correos-ALMERIA OP-0400010, AV SAN JUAN BOSCO, 35, ALMERÍA",
    ],
    "05": [
        "CNP ÁVILA, PASEO SAN ROQUE, 34, ÁVILA",
        "INSS - Ávila - CAISS Nº 1, Plaza Claudio Sánchez Albornoz, 2, Ávila",
        "Oficina de Correos-AVILA OP-500010, PZ CATEDRAL, 2, ÁVILA",
        "Oficina de Extranjería en Ávila, Hornos Caleros, 1, Ávila",
    ],
    "06": [
        "BRIGADA PROVINCIAL EXTRANJERÍA Y FRONTERAS BADAJOZ CNP, AVD. RAMÓN Y CAJAL, S/N, BADAJOZ",
        "CNP ALMENDRALEJO, Benito Pérez Galdós, S/N, ALMENDRALEJO",
        "CNP BADAJOZ, Avenida Ramón y Cajal, s/n, BADAJOZ",
        "CNP BADAJOZ CITA PREVIA POLICÍA TARJETAS, LA BOMBA, 9, BADAJOZ",
        "CNP DON BENITO, AVENIDA DE CORDOBA, S/N, DON BENITO",
        "CNP MÉRIDA BRIGADA, AVENIDA VALHONDO, 8, MERIDA-BADAJOZ",
        "CNP MÉRIDA TARJETAS, AVENIDA VALHONDO, 8, MÉRIDA-BADAJOZ",
        "CNP ZAFRA, PLAZA DEL PILAR REDONDO S/N, ZAFRA",
        "INSS - Badajoz - CAISS Nº 1, Ronda del Pilar, 15, Badajoz",
        "Oficina de Correos-BADAJOZ OP-600010, PASEO SAN FRANCISCO, S/N, BADAJOZ",
        "Oficina de Correos-MERIDA-680001, MARQUESA DE PINARES, 26, MÉRIDA",
        "OFICINA DE EXTRANJERÍA, CALLE LA BOMBA, 9, BADAJOZ",
    ],
    "08": [
        "CNP COMISARIA BADALONA, AVDA. DELS VENTS, 9, BADALONA",
        "CNP COMISARIA CASTELLDEFELS, PLAÇA DE L`ESPERANTO, 4, CASTELLDEFELS",
        "CNP COMISARIA CERDANYOLA DEL VALLES, VERGE DE LES FEIXES, 4, CERDANYOLA DEL VALLES",
        "CNP COMISARIA CORNELLA DE LLOBREGAT, AV. SANT ILDEFONS, S/N, CORNELLA DE LLOBREGAT",
        "CNP COMISARIA EL PRAT DE LLOBREGAT, CENTRE, 4, EL PRAT DE LLOBREGAT",
        "CNP COMISARIA GRANOLLERS, RICOMA, 65, GRANOLLERS",
        "CNP COMISARIA IGUALADA, PRAT DE LA RIBA, 13, IGUALADA",
        "CNP COMISARIA LHOSPITALET DE LLOBREGAT, Rbla. Just Oliveres, 43, L`HOSPITALET DE LLOBREGAT",
        "CNP COMISARIA MANRESA, SOLER I MARCH, 5, MANRESA",
        "CNP COMISARIA MATARO, AV. GATASSA, 15, MATARO",
        "CNP COMISARIA MONTCADA I REIXAC, MAJOR, 38, MONTCADA I REIXAC",
        "CNP COMISARIA RIPOLLET, TAMARIT, 78, RIPOLLET",
        "CNP COMISARIA RUBI, TERRASSA, 16, RUBI",
        "CNP COMISARIA SABADELL, BATLLEVELL, 115, SABADELL",
        "CNP COMISARIA SANT ADRIA DEL BESOS, AV. JOAN XXIII, 2, SANT ADRIA DEL BESOS",
        "CNP COMISARIA SANT BOI DE LLOBREGAT, RIERA BASTÉ, 43, SANT BOI DE LLOBREGAT",
        "CNP COMISARIA SANT CUGAT DEL VALLES, VALLES, 1, SANT CUGAT DEL VALLES",
        "CNP COMISARIA SANT FELIU DE LLOBREGAT, CARRERETES, 9, SANT FELIU DE LLOBREGAT",
        "CNP COMISARIA SANTA COLOMA DE GRAMENET, IRLANDA, 67, SANTA COLOMA DE GRAMENET",
        "CNP COMISARIA TERRASSA, BALDRICH, 13, TERRASSA",
        "CNP COMISARIA VIC, BISBE MORGADES, 4, VIC",
        "CNP COMISARIA VILADECANS, AVDA. BALLESTER, 2, VILADECANS",
        "CNP COMISARIA VILAFRANCA DEL PENEDES, Avinguda Ronda del Mar, 109, VILAFRANCA DEL PENEDES",
        "CNP COMISARIA VILANOVA I LA GELTRU, CARRER D`OLÉRDOLA, 47, Vilanova i la Geltrú",
        "CNP GUADALAJARA, Guadalajara, 1, Barcelona",
        "CNP MALLORCA GRANADOS, MALLORCA, 213, BARCELONA",
        "CNP PSJ PLANTA BAJA, PASSEIG SANT JOAN, 189, BARCELONA",
        "CNP RAMBLA GUIPUSCOA 74, RAMBLA GUIPUSCOA, 74, BARCELONA",
        "Oficina de Correos - Sabadell Suc 3- 0840794, Bocaccio, 70, Sabadell",
        "Oficina de Correos - Sant Boi de Llobregat- 0883001, Joan Salvat-Papaseit, 33, Sant Boi de Llobregat",
        "Oficina de Correos - Sant Cugat del Vallés- 0819003, Rb Can Mora, sn, Sant Cugat del Vallés",
        "Oficina de Correos - Santa Coloma de Gramenet- 0800015, Avd Francesc Maciá, 34, Santa Coloma de Gramenet",
        "Oficina de Correos - Terrassa OP- 0800016, Pç Mossen Jacint Verdaguer, 16, Terrassa",
        "Oficina de Correos - Terrassa Suc 1- 0859394, Italia, 3, Terrassa",
        "Oficina de Correos - Terrassa Suc 3- 0883194, Ps Lluis Muncunill, 57-59, Terrassa",
        "Oficina de Correos - Terrassa Suc 4- 0883294, Pau Marsal, 36-38, Terrassa",
        "Oficina de Correos - Terrassa Suc 5- 0883394, Avd Ángel Sallent, 184-186, Terrassa",
        "Oficina de Correos - VIC- 0850001, RB Hospital, 48, VIC",
        "Oficina de Correos - Viladecans- 0884001, Sant Sebastiá, 1, Viladecans",
        "Oficina de Correos - Vilanova i la Geltrú- 0880001, Pç de les Neus, 11, Vilanova i la Geltrú",
        "TGSS - Administración 08/02, C/ Arc del Teatre, 63-65, Barcelona",
        "TGSS - DIRECCIÓN PROVINCIAL, C/ Aragón, 273-275, Barcelona",
        "TGSS - URE 08/04, Travesera de Gracia, 117, Barcelona",
    ],
    "09": [
        "CNP ARANDA DE DUERO, SAN FRANCISCO, 92, ARANDA DE DUERO",
        "CNP COMISARIA BURGOS, Avenida Castilla y León, 3, BURGOS",
        "CNP COMISARIA POLICÍA UD. DOCUMENTACIÓN, Avenida Castilla y León, 3, BURGOS",
        "CNP MIRANDA DE EBRO, ANTONIO CABEZON, 14, MIRANDA DE EBRO",
        "INSS - Burgos - CAISS Nº 1, Avenida de los Derechos Humanos, 12, Burgos",
        "Oficina de Correos-BURGOS OP-900010, PZ CONDE DE CASTRO, 1, BURGOS",
        "Oficina de Correos-BURGOS SUC 1-918094, AV CASTILLA Y LEON, 46, BURGOS",
        "Oficina de Correos-BURGOS SUC 3-918294, AV AVENIDA DE LOS DERECHOS HUMANOS, 53, BURGOS",
        "Oficina de Extranjeria en Burgos, Vitoria, 34, Burgos",
    ],
    "10": [
        "CNP CACERES BPEF, Avenida Pierre de Coubertin, 13, Cáceres",
        "CNP PLASENCIA, CUEVA DE LA SERRANA, S/N, PLASENCIA",
        "CNP VALENCIA DE ALCANTARA, Canalejas, 5, VALENCIA DE ALCANTARA",
        "Oficina de Correos-CACERES OP-1000010, AVDA. ESPAÑA, 4, CÁCERES",
        "OFICINA DE EXTRANJERIA EN CACERES, C/Catedrático Antonio Silva, 7, CACERES",
        "TGSS - DIRECCIÓN PROVINCIAL, Avenida de España, 14, Cáceres",
    ],
    "11": [
        "ALGECIRAS TR OFICINA EXRANJERÍA, P. Juan de Lima, 5, Algeciras",
        "CÁDIZ COMISARÍA CUERPO N. DE POLICÍA, Avenida de Andalucía, 28, Cádiz",
        "CÁDIZ OFICINA DE EXTRANJERÍA, Acacias, 2, Cádiz",
        "CNP ALGECIRAS, AV. FUERZAS ARMADAS, 6, ALGECIRAS",
        "CNP CHICLANA DE LA FRONTERA, LA FUENTE, 7, CHICLANA DE LA FRONTERA",
        "CNP JEREZ DE LA FRONTERA, Avenida de la Universidad, 10, JEREZ DE LA FRONTERA",
        "CNP LA LINEA CONCEPCIÓN, AVENIDA MENENDEZ PELAYO, S/N, LA LÍNEA DE LA CONCEPCIÓN",
        "CNP PUERTO SANTA MARIA PUERTO REAL, Carpintero de rivera, s/n, Puerto Real",
        "CNP ROTA, AVENIDA PRINCIPES DE ESPAÑA, 113, ROTA",
        "CNP SAN FERNANDO, Avenida Contitución de 1978, S/N, SAN FERNANDO",
        "INSS - Cádiz - DIRECCIÓN PROVINCIAL, Plaza de la constitución, sn, Cádiz",
        "Oficina de Correos-ALGECIRAS OP-1100011, RUIZ ZORRILLA, 42, ALGECIRAS",
        "Oficina de Correos-ALGECIRAS SUC 1. PLAZA ALTA-1108694, TARIFA, 5, ALGECIRAS",
        "Oficina de Correos-CADIZ OP-1100010, PZ TOPETE, S/N, CÁDIZ",
        "Oficina de Correos-CADIZ SUC 2. SAN JOSÉ-1105194, AVDA MARIA AUXILIADORA, 3, CÁDIZ",
        "Oficina de Correos-CADIZ SUC 3. GIBRALTAR-1115894, AV DE LA SANIDAD PÚBLICA, S/N, CÁDIZ",
        "Oficina de Correos-CHICLANA DE LA FRONTERA-1113004, JESUS NAZARENO, 4, CHICLANA DE LA FRONTERA",
        "Oficina de Correos-CHICLANA DE LA FRONTERA SUC 1-1119094, ALAMEDA DE SOLANO, 2, CHICLANA DE LA FRONTERA",
        "Oficina de Correos-EL PUERTO DE SANTA MARIA OP-1100013, PZ DEL POLVORISTA, 1, PUERTO DE SANTA MARÍA (EL)",
        "Oficina de Correos-JEREZ DE LA FRONTERA OP-1100012, CERRON, 2, JEREZ DE LA FRONTERA",
        "Oficina de Correos-JEREZ DE LA FRONTERA SUC 1. CHAPI-1105094, AV DE LA UNIVERSIDAD, S/N, JEREZ DE LA FRONTERA",
        "Oficina de Correos-JEREZ DE LA FRONTERA SUCURSAL 4. ZONA NORTE-1115594, AV DE LA ILUSTRACION, 5, JEREZ DE LA FRONTERA",
        "Oficina de Correos-LA LINEA DE LA CONCEPCION-1130001, PZ DE LA CONSTITUCION, 17, LÍNEA DE LA CONCEPCIÓN (LA)",
        "Oficina de Correos-SAN FERNANDO-1110001, REAL, 113, SAN FERNANDO",
        "Oficina de Correos-SAN FERNANDO SUC 1 ALMIRANTE LEÓN HERRERO-1112994, AV ALMIRANTE LEON HERRERO, 15, SAN FERNANDO",
        "Oficina de Correos-SANLUCAR DE BARRAMEDA-1154002, AV DEL CERRO FALON, 6, SANLÚCAR DE BARRAMEDA",
    ],
    "15": [
        "CNP SANTIAGO COMPOSTELA EXTRANJEROS, AVD RODRIGO DE PADRON, SN, SANTIAGO DE COMPOSTELA",
        "CNP COMISARIA A CORUÑA - LONZAS, C/ Médico Devesa Núñez, 4, A Coruña",
        "CNP FERROL, AVENIDA DE SAN AMARO, S/N, FERROL",
        "CNP Santa Uxía de Ribeira, Av/ Das Airos, 21, Ribeira",
        "INSS - A Coruña - CAISS Nº 1, Avenida Pedro Barrié de la Maza, 18, A Coruña",
        "Oficina de Correos-A CORUÑA OP-1500010, RUA ALCALDE MANUEL CASAS, S/N, CORUÑA (A)",
        "Oficina de Correos-A CORUÑA SUC 1-1545694, AV. SARDIÑEIRA (ESTACION DE RENFE), S/N, CORUÑA (A)",
        "Oficina de Correos-A CORUÑA SUC 3-1545894, CL RODRIGO ALFREDO DE SANTIAGO, 38, CORUÑA (A)",
        "Oficina de Correos-FERROL OP-1500011, PRA. GALICIA, S/N, FERROL",
        "Oficina de Correos-SANTIAGO DE COMPOSTELA OP-1500012, RUA. DO FRANCO, 4, SANTIAGO DE COMPOSTELA",
        "Oficina de Extranjería en A Coruña, C/ Real, 53, A CORUÑA",
    ],
    "33": [
        "CNP AVILES, Río San Martín, 2, AVILES",
        "CNP GIJÓN, Plaza Máximo Gonzalez, s/n, Gijón",
        "CNP LUARCA, OLAVARRIETA, 25, LUARCA",
        "CNP OVIEDO - EXPEDICION TIE, Plaza de España, 3, Oviedo",
        "CNP OVIEDO - OTROS DOCUMENTOS, PLAZA DE ESPAÑA, 3, OVIEDO",
        "INSS - Asturias - CAISS Nº 1, C/ Doctor Alfredo Martínez, 6, Oviedo",
        "Oficina de Correos-AVILES-3340012, PZ DE LA MERCED, 4, AVILÉS",
        "Oficina de Correos-GIJON OP-3300011, PZ SEIS DE AGOSTO, S/N, GIJÓN",
        "Oficina de Correos-OVIEDO OP-3300010, CL ALONSO DE QUINTANILLA, 1, OVIEDO",
        "Oficina de Extranjería en Oviedo, Plaza de España, 3, Oviedo",
        "SOLICITUD INICIAL ASILO, OFICINA DE EXTRANJEROS, PLAZA DE ESPAÑA 3, OVIEDO",
    ],
    "48": [
        "CNP BILBAO JSP del País Vasco, Gordóniz, 8, Bilbao",
        "INSS - Bizkaia - CAISS Nº 1, Avenida Sabino Arana, 3, Bilbao",
        "Oficina de Correos - ALGORTA-4899003, KAL. TERRENE, 6, ALGORTA",
        "Oficina de Correos - BARAKALDO SUC 1. CRUCES-4806694, KAL. BAKE, 34, SAN VICENTE DE BARAKALDO",
        "Oficina de Correos - BARAKALDO SUC 2_ZUAZO-4817194, ENP. LOPEZ DE AYALA, 6, SAN VICENTE DE BARAKALDO",
        "Oficina de Correos - BARAKALDO OP-4800011, KAL ARANA, 8, SAN VICENTE DE BARAKALDO",
        "Oficina de Correos - BILBAO OP-4800010, AL URQUIJO, 19, BILBAO",
        "Oficina de Correos - BILBAO SUC 1. ARENAL-4806794, KAL. VIUDA DE EPALZA, 3, BILBAO",
        "Oficina de Correos - BILBAO SUC 10. MIRIBILLA-4818094, KAL. DOCTOR ESPINOSA ORIBE, 3, BILBAO",
        "Oficina de Correos - BILBAO SUC 2. DEUSTO-4806894, ET. LEHENDAKARI AGUIRRE, 22, BILBAO",
        "Oficina de Correos - BILBAO SUC 4. TXURDINAGA-4807094, ET. JULIAN GAYARRE, 84, BILBAO",
        "Oficina de Correos - BILBAO SUC 6. LA CASILLA-4807294, PZ. LA CASILLA, Z/G, BILBAO",
        "Oficina de Correos - BILBAO SUC 7. SANTUTXU-4807394, KAL. PARTICULAR DE ALLENDE, 12, BILBAO",
        "Oficina de Correos - LAS ARENAS-AREETA-4893001, KAL. SANTA ANA, 4, ARENAS (LAS)-AREETA",
        "Oficina Extranjería Bizkaia, Barroeta Aldamar, 1, Bilbao",
    ],
}

TRAMITES_POLICIA = [
    "POLICÍA-TOMA DE HUELLAS (EXPEDICIÓN DE TARJETA) INICIAL, RENOVACIÓN, DUPLICADO Y LEY 14/2013",
    "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
    "POLICIA- EXPEDICIÓN/RENOVACIÓN DE DOCUMENTOS DE SOLICITANTES DE ASILO",
    "POLICIA- SOLICITUD ASILO",
    "POLICIA-CARTA DE INVITACIÓN",
    "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
    "POLICIA-CERTIFICADOS (DE RESIDENCIA, DE NO RESIDENCIA Y DE CONCORDANCIA)",
    "POLICIA-CERTIFICADOS Y ASIGNACION NIE",
    "POLICIA-INFORMACION DE TRÁMITES DE LA COMISARÍA DE POLICIA",
    "POLICÍA - CÉDULA DE INSCRIPCIÓN",
    "POLICÍA - UCRANIA : SOLICITUD PROTECCIÓN TEMPORAL DESPLAZADOS",
    "POLICÍA TARJETA CONFLICTO UCRANIA–ПОЛІЦІЯ -КАРТКА ДЛЯ ПЕРЕМІЩЕНИХ ОСІБ ВНАСЛІДОК КОНФЛІКТУ В УКРАЇНІ",
    "POLICIA - CERTIFICADOS CONCORDANCIA",
    "POLICIA - TÍTULOS DE VIAJE",
    "POLICÍA - SOLICITUD DE APATRIDA",
    "POLICIA-ASIGNACIÓN DE NIE",
    "POLICIA-AUTORIZACIÓN DE REGRESO",
    "POLICÍA-PRORROGA DE ESTANCIA",
    "POLICÍA-RECOGIDA DE TARJETA ROJA (PROTECCIÓN INTERNACIONAL)",
    "POLICÍA-SOLICITUD TARJETA ROJA",
    "POLICÍA - COMUNICACIÓN DE CAMBIO DE DOMICILIO",
    "ASIGNACION NIE CIUDADANOS COMUNITARIOS",
    "POLICÍA - PRORROGA DE ESTANCIA CON VISADO",
    "POLICÍA - PRORROGA DE ESTANCIA SIN VISADO",
    "POLICÍA-CONSULTA N.º DE NIE ASIGNADO",
    "POLICÍA-DECLARACIÓN DE ENTRADA",
    "POLICIA - OTROS TRÁMITES COMISARIA",
    "POLICÍA-EXPEDICIÓN/RENOVACIÓN DE DOCUMENTOS DE SOLICITUD DE APATRIDIA",
    "POLICÍA-RECOGIDA CERTIFICADO Y AUTORIZACIÓN DE REGRESO",
    "POLICIA-ASILO INFORMACION",
    "POLICÍA-CERTIFICADOS UE",
    "POLICÍA-CERTIFICADOS Y ASIGNACION NIE (NO COMUNITARIOS)",
    "POLICÍA-ASIGNACIÓN NIE NO RESIDENTE NO COMUNITARIO",
    "POLICÍA-CERTIFICADOS (RESIDENCIA Y CONCORDANCIA)",
    "POLICÍA-EXP.TARJETA ASOCIADA AL ACUERDO DE RETIRADA CIUDADANOS BRITÁNICOS Y SUS FAMILIARES (BREXIT)",
    "POLICÍA-EXPEDICIÓN DE TARJETAS CUYA AUTORIZACIÓN RESUELVE LA DIRECCIÓN GENERAL DE GESTIÓN MIGRATORIA",
    "Asignación de N.I.E.",
    "Certificado de residente o no residente",
    "CERTIFICADOS UE",
]

TRAMITES_EXTRANJERIA = [
    "AUTORIZACIONES EXTRAORDINARIAS: RESIDENCIA CIR. EXC. POR RAZÓN DE ARRAIGO Y ARRAIGO EXTRAORDINARIO",
    "AUT. DE RESIDENCIA TEMPORAL POR CIRCUNS. EXCEPCIONALES POR ARRAIGO",
    "FAMILIARES DE RESIDENTES COMUNITARIOS",
    "INFORMACIÓN",
    "SOLICITUD DE AUTORIZACIONES",
    "SOLICITUD DE AUTORIZACIONES INICIALES",
    "ACCESO A 1ª AUT. DE RESIDENCIA DE LARGA DURACIÓN Y LARGA DURACIÓN UE",
    "AUTORIZACIONES DE RESIDENCIA TEMPORAL Y PERMANENTE DE FAMILIAR DE CIUDADANO DE LA UNION EUROPEA",
    "AUTORIZACIONES DE RESIDENCIA TEMPORAL POR MOTIVOS DE ARRAIGO Y OTRAS CIRCUNSTANCIAS EXCEPCIONALES",
    "AUTORIZACIONES DE TRABAJO, RENOVACIONES, PRÓRROGAS Y MODIFICACIONES",
    "RENOVACIONES, PRÓRROGAS O MODIFICACIONES",
    "Expedición de Carta de Invitación",
    "AUTORIZACIÓN DE REGRESO",
    "AUTORIZACIÓN DE RESIDENCIA DE MENORES O INCAPACITADOS NACIDOS EN ESPAÑA",
    "AUTORIZACIÓN DE RESIDENCIA DE MENORES O INCAPACITADOS NO NACIDOS EN ESPAÑA",
    "AUTORIZACIÓN DE RESIDENCIA TEMPORAL POR REAGRUPACIÓN FAMILIAR",
    "ESTANCIA POR ESTUDIOS",
    "MODIFICACIÓN de las SITUACIONES (sujeto legitimado EXTRANJERO)",
    "Recuperación de la autorización de larga duración",
    "REGISTRO",
    "RENOVACIONES DE RESIDENCIA",
    "Renovaciones, Prórrogas y Modificaciones",
    "RESIDENCIA TEMPORAL DE FAMILIARES DE PERSONAS CON NACIONALIDAD ESPAÑOLA",
    "REAGRUPACIÓN FAMILIAR",
    "RENOVACIONES DE AUT. DE RESIDENCIA y/o AUT. DE RESIDENCIA Y TRABAJO",
    "RENOVACIÓN AUTORIZACIÓN RESIDENCIA POR REAGRUPACIÓN FAMILIAR",
    "AUTORIZACIONES DE TRABAJO POR ESTUDIOS",
    "FAMILIARES DE RESIDENTES COMUNITARIOS",
    "AUTORIZACIÓN DE RESIDENCIA TEMPORAL POR CIRCUNSTANCIAS EXCEPCIONALES POR ARRAIGO",
    "AUTORIZACIÓN DE RESIDENCIA TEMPORAL POR REAGRUPACIÓN FAMILIAR",
    "ESTANCIA POR ESTUDIOS",
]

# ─── SCRAPER ──────────────────────────────────────────────────────────────────
def fetch_offices_from_web(province_code: str) -> list:
    """Fetch offices live from website for provinces not in local data."""
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
        })
        session.get(f"{BASE_URL}/index", timeout=15)
        r = session.post(f"{BASE_URL}/citar",
                         data={"form": province_code, "btnAceptar": "Aceptar"},
                         timeout=15)
        soup = BeautifulSoup(r.text, "lxml")
        sede_select = soup.find("select", {"name": "sede"})
        if not sede_select:
            return []
        offices = []
        for opt in sede_select.find_all("option"):
            val = opt.get("value", "").strip()
            text = opt.get_text(strip=True)
            if val and val != "0" and text:
                offices.append(text)
        return offices
    except Exception as e:
        logger.warning(f"Web fetch offices failed: {e}")
        return []


def get_offices_for_province(province_code: str) -> list:
    """Return offices from local data or fetch from web."""
    if province_code in OFFICES_BY_PROVINCE:
        return OFFICES_BY_PROVINCE[province_code]
    return fetch_offices_from_web(province_code)


def check_availability(province_code: str, office_name: str, tramite: str) -> dict:
    """Check if a specific office has cita available."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9",
    })
    result = {
        "available": False,
        "message": "",
        "error": None,
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        # Step 1: Home page
        session.get(f"{BASE_URL}/index", timeout=15)

        # Step 2: Select province
        r = session.post(f"{BASE_URL}/citar",
                         data={"form": province_code, "btnAceptar": "Aceptar"},
                         timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        # Find office value from dropdown
        sede_select = soup.find("select", {"name": "sede"})
        office_value = None
        if sede_select:
            for opt in sede_select.find_all("option"):
                if opt.get_text(strip=True) == office_name:
                    office_value = opt.get("value", "").strip()
                    break
            # Fallback: partial match
            if not office_value:
                for opt in sede_select.find_all("option"):
                    if office_name[:30].lower() in opt.get_text(strip=True).lower():
                        office_value = opt.get("value", "").strip()
                        break

        if not office_value:
            result["error"] = "Oficina no encontrada en el sitio web"
            return result

        # Step 3: Select office + tramite
        r2 = session.post(f"{BASE_URL}/citar",
                          data={
                              "sede": office_value,
                              "tramiteGrupo[0]": tramite,
                              "btnAceptar": "Aceptar",
                          },
                          timeout=15)
        soup2 = BeautifulSoup(r2.text, "lxml")

        page_text = soup2.get_text().lower()

        if "no hay citas disponibles" in page_text:
            result["available"] = False
            result["message"] = "No hay citas disponibles"
        elif "en este momento no" in page_text:
            result["available"] = False
            result["message"] = "Sin citas en este momento"
        else:
            # Check if we moved past selection = potentially available
            if "datos del solicitante" in page_text or "identificacion" in page_text or "solicitante" in page_text:
                result["available"] = True
                result["message"] = "¡Página de datos encontrada — cita posiblemente disponible!"
            else:
                result["available"] = False
                result["message"] = "Sin citas disponibles"

    except requests.RequestException as e:
        result["error"] = f"Error de red: {str(e)[:80]}"

    return result


# ─── SCHEDULER ────────────────────────────────────────────────────────────────
async def run_check_for_user(app: Application, chat_id: int):
    config = user_configs.get(chat_id)
    if not config or not config.get("active"):
        return

    province_name = config["province_name"]
    province_code = config["province_code"]
    office = config["office"]
    tramite = config["tramite"]

    logger.info(f"Checking [{chat_id}] {province_name} | {office[:40]} | {tramite[:40]}")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, check_availability, province_code, office, tramite)

    now = result["checked_at"]
    config["check_count"] = config.get("check_count", 0) + 1
    count = config["check_count"]

    if result["error"]:
        logger.warning(f"Error for {chat_id}: {result['error']}")
        if count % 20 == 0:
            await app.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ Error al verificar:\n{result['error']}\n\nReintenando...",
            )
        return

    if result["available"]:
        msg = (
            f"🟢 <b>¡CITA DISPONIBLE!</b>\n\n"
            f"📍 <b>Provincia:</b> {province_name}\n"
            f"🏢 <b>Oficina:</b> {office}\n"
            f"📋 <b>Trámite:</b> {tramite}\n\n"
            f"⏰ <b>Detectado:</b> {now}\n"
            f"🔢 <b>Check #{count}</b>\n\n"
            f"👉 <a href='https://icp.administracionelectronica.gob.es/icpco/index'>Reservar cita AHORA</a>"
        )
        await app.bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML",
                                   disable_web_page_preview=True)
        logger.info(f"✅ CITA AVAILABLE → {chat_id}")
    else:
        logger.info(f"❌ No cita [{chat_id}] check #{count} @ {now}")
        if count % 10 == 0:
            await app.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"🔄 <b>Monitoreando activamente...</b>\n\n"
                    f"📍 {province_name}\n"
                    f"🏢 {office[:50]}...\n"
                    f"📋 {tramite[:50]}...\n\n"
                    f"✅ {count} checks realizados\n"
                    f"⏰ Último: {now}\n"
                    f"❌ Sin citas disponibles aún — seguimos buscando"
                ),
                parse_mode="HTML"
            )


# ─── BOT HANDLERS ─────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Cita Previa Extranjería Monitor</b>\n\n"
        "Te aviso en cuanto haya cita disponible en tu oficina.\n\n"
        "📌 /monitor — Configurar y empezar\n"
        "⏹ /stop — Detener monitoreo\n"
        "📊 /status — Ver configuración actual\n"
        "❓ /help — Ayuda",
        parse_mode="HTML"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ <b>Cómo usar el bot:</b>\n\n"
        "1. /monitor → selecciona provincia\n"
        "2. Selecciona tu oficina\n"
        "3. Selecciona categoría (Policía / Extranjería)\n"
        "4. Selecciona el trámite\n"
        "5. Confirma — el bot empieza a monitorear\n\n"
        f"🔁 Verifica cada {CHECK_INTERVAL} segundos.\n"
        "🔔 Te avisa inmediatamente cuando haya cita.\n"
        "📊 Status update cada 10 checks.",
        parse_mode="HTML"
    )


async def monitor_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prov_list = sorted(PROVINCES.keys())
    keyboard = []
    for i in range(0, len(prov_list), 2):
        row = [InlineKeyboardButton(prov_list[i], callback_data=f"prov|{prov_list[i]}")]
        if i + 1 < len(prov_list):
            row.append(InlineKeyboardButton(prov_list[i+1], callback_data=f"prov|{prov_list[i+1]}"))
        keyboard.append(row)

    await update.message.reply_text(
        "📍 <b>Selecciona tu Provincia:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SELECT_PROVINCE


async def province_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    province_name = query.data.split("|", 1)[1]
    province_code = PROVINCES[province_name]

    context.user_data["province_name"] = province_name
    context.user_data["province_code"] = province_code

    await query.edit_message_text(
        f"📍 Provincia: <b>{province_name}</b>\n\n⏳ Cargando oficinas...",
        parse_mode="HTML"
    )

    # Get offices (local data or web fetch)
    offices = get_offices_for_province(province_code)

    if not offices:
        await query.edit_message_text(
            f"❌ No se encontraron oficinas para <b>{province_name}</b>.\n"
            "Usa /monitor para intentar de nuevo.",
            parse_mode="HTML"
        )
        return ConversationHandler.END

    context.user_data["offices"] = offices

    # Build office keyboard (1 per row, truncated to 40 chars)
    keyboard = []
    for i, office in enumerate(offices):
        label = office[:45] + "…" if len(office) > 45 else office
        keyboard.append([InlineKeyboardButton(label, callback_data=f"office|{i}")])

    await query.edit_message_text(
        f"📍 Provincia: <b>{province_name}</b>\n\n🏢 <b>Selecciona la Oficina:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SELECT_OFFICE


async def office_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.split("|")[1])
    offices = context.user_data["offices"]
    office = offices[idx]
    context.user_data["office"] = office

    keyboard = [
        [InlineKeyboardButton("🚔 Policía Nacional", callback_data="cat|policia")],
        [InlineKeyboardButton("🏛 Extranjería", callback_data="cat|extranjeria")],
    ]
    await query.edit_message_text(
        f"🏢 Oficina: <b>{office[:60]}</b>\n\n📋 <b>¿Qué categoría de trámite?</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SELECT_CATEGORY


async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat = query.data.split("|")[1]
    context.user_data["category"] = cat

    if cat == "policia":
        tramites = TRAMITES_POLICIA
        title = "🚔 Trámites Policía Nacional:"
    else:
        tramites = TRAMITES_EXTRANJERIA
        title = "🏛 Trámites Extranjería:"

    context.user_data["tramites_list"] = tramites

    keyboard = []
    for i, t in enumerate(tramites):
        label = t[:50] + "…" if len(t) > 50 else t
        keyboard.append([InlineKeyboardButton(label, callback_data=f"tram|{i}")])

    await query.edit_message_text(
        f"📋 <b>{title}</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SELECT_TRAMITE


async def tramite_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.split("|")[1])
    tramite = context.user_data["tramites_list"][idx]
    context.user_data["tramite"] = tramite

    province_name = context.user_data["province_name"]
    office = context.user_data["office"]

    keyboard = [[
        InlineKeyboardButton("✅ Confirmar", callback_data="confirm|yes"),
        InlineKeyboardButton("❌ Cancelar", callback_data="confirm|no"),
    ]]
    await query.edit_message_text(
        f"<b>📋 Confirmar configuración:</b>\n\n"
        f"📍 <b>Provincia:</b> {province_name}\n"
        f"🏢 <b>Oficina:</b>\n{office}\n\n"
        f"📄 <b>Trámite:</b>\n{tramite}\n\n"
        f"⏱ Verificando cada {CHECK_INTERVAL} segundos\n\n"
        f"¿Empezar monitoreo?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return CONFIRM


async def confirm_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data.split("|")[1]
    chat_id = query.message.chat_id

    if choice == "yes":
        user_configs[chat_id] = {
            "province_name": context.user_data["province_name"],
            "province_code": context.user_data["province_code"],
            "office": context.user_data["office"],
            "tramite": context.user_data["tramite"],
            "active": True,
            "check_count": 0,
            "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        await query.edit_message_text(
            f"🚀 <b>¡Monitoreo iniciado!</b>\n\n"
            f"📍 {context.user_data['province_name']}\n"
            f"🏢 {context.user_data['office'][:60]}\n"
            f"📋 {context.user_data['tramite'][:60]}\n\n"
            f"🔔 Te avisaré en cuanto haya cita disponible.",
            parse_mode="HTML"
        )
    else:
        await query.edit_message_text("❌ Cancelado. Usa /monitor para configurar de nuevo.")

    return ConversationHandler.END


async def stop_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in user_configs and user_configs[chat_id].get("active"):
        user_configs[chat_id]["active"] = False
        count = user_configs[chat_id].get("check_count", 0)
        await update.message.reply_text(
            f"⏹ Monitoreo detenido.\n✅ Se realizaron {count} verificaciones.\n\nUsa /monitor para reiniciar."
        )
    else:
        await update.message.reply_text("No hay ningún monitoreo activo.")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    config = user_configs.get(chat_id)
    if not config:
        await update.message.reply_text("No hay configuración activa. Usa /monitor para empezar.")
        return
    estado = "🟢 Activo" if config.get("active") else "🔴 Detenido"
    await update.message.reply_text(
        f"<b>Estado:</b> {estado}\n\n"
        f"📍 <b>Provincia:</b> {config['province_name']}\n"
        f"🏢 <b>Oficina:</b>\n{config['office']}\n\n"
        f"📋 <b>Trámite:</b>\n{config['tramite']}\n\n"
        f"🔢 <b>Checks:</b> {config.get('check_count', 0)}\n"
        f"🕐 <b>Iniciado:</b> {config.get('started_at', 'N/A')}\n"
        f"⏱ <b>Intervalo:</b> {CHECK_INTERVAL}s",
        parse_mode="HTML"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelado. Usa /monitor para empezar de nuevo.")
    return ConversationHandler.END


# ─── SCHEDULER ────────────────────────────────────────────────────────────────
def setup_scheduler(app: Application):
    scheduler = AsyncIOScheduler()

    async def check_all():
        for chat_id in list(user_configs.keys()):
            await run_check_for_user(app, chat_id)

    scheduler.add_job(check_all, "interval", seconds=CHECK_INTERVAL)
    scheduler.start()
    logger.info(f"Scheduler started — every {CHECK_INTERVAL}s")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set!")

    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("monitor", monitor_start)],
        states={
            SELECT_PROVINCE:  [CallbackQueryHandler(province_selected,  pattern=r"^prov\|")],
            SELECT_OFFICE:    [CallbackQueryHandler(office_selected,    pattern=r"^office\|")],
            SELECT_CATEGORY:  [CallbackQueryHandler(category_selected,  pattern=r"^cat\|")],
            SELECT_TRAMITE:   [CallbackQueryHandler(tramite_selected,   pattern=r"^tram\|")],
            CONFIRM:          [CallbackQueryHandler(confirm_selection,  pattern=r"^confirm\|")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stop", stop_monitor))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(conv)

    setup_scheduler(app)
    logger.info("Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
