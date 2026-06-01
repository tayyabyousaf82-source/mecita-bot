#!/usr/bin/env python3
import os, logging, asyncio, aiohttp, sqlite3, re, traceback
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler
)
from telegram.error import NetworkError, TimedOut, RetryAfter, Conflict

BOT_TOKEN    = os.environ.get("BOT_TOKEN", "")
CHECK_INTERVAL = 30
FREE_LIMIT   = 3
DB_PATH      = "/tmp/extranjeria.db"

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ASK_PROVINCIA, ASK_TRAMITE, ASK_OFICINA = range(3)

PROVINCIAS = [
    "A Coruña","Albacete","Alicante","Almería","Araba","Asturias",
    "Ávila","Badajoz","Barcelona","Bizkaia","Burgos","Cáceres",
    "Cádiz","Cantabria","Castellón","Ceuta","Ciudad Real","Córdoba",
    "Cuenca","Gipuzkoa","Girona","Granada","Guadalajara","Huelva",
    "Huesca","Illes Balears","Jaén","La Rioja","Las Palmas","León",
    "Lleida","Lugo","Madrid","Málaga","Melilla","Murcia","Navarra",
    "Ourense","Palencia","Pontevedra","Salamanca","S.Cruz Tenerife",
    "Segovia","Sevilla","Soria","Tarragona","Teruel","Toledo",
    "Valencia","Valladolid","Zamora","Zaragoza"
]

PROVINCIA_CODES = {
    "A Coruña":"15","Albacete":"02","Alicante":"03","Almería":"04",
    "Araba":"01","Asturias":"33","Ávila":"05","Badajoz":"06",
    "Barcelona":"08","Bizkaia":"48","Burgos":"09","Cáceres":"10",
    "Cádiz":"11","Cantabria":"39","Castellón":"12","Ceuta":"51",
    "Ciudad Real":"13","Córdoba":"14","Cuenca":"16","Gipuzkoa":"20",
    "Girona":"17","Granada":"18","Guadalajara":"19","Huelva":"21",
    "Huesca":"22","Illes Balears":"07","Jaén":"23","La Rioja":"26",
    "Las Palmas":"35","León":"24","Lleida":"25","Lugo":"27",
    "Madrid":"28","Málaga":"29","Melilla":"52","Murcia":"30",
    "Navarra":"31","Ourense":"32","Palencia":"34","Pontevedra":"36",
    "Salamanca":"37","S.Cruz Tenerife":"38","Segovia":"40",
    "Sevilla":"41","Soria":"42","Tarragona":"43","Teruel":"44",
    "Toledo":"45","Valencia":"46","Valladolid":"47","Zamora":"49",
    "Zaragoza":"50"
}

DEFAULT_TRAMITES = [
    "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
    "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
    "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
    "AUTORIZACION DE REGRESO",
    "POLICIA-ASIGNACION DE NIE",
    "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
]

TRAMITES_POR_PROVINCIA = {
    "Barcelona": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "POLICIA TARJETA CONFLICTO UCRANIA",
        "POLICIA-EXP.TARJETA ASOCIADA AL ACUERDO DE RETIRADA (BREXIT)",
        "POLICIA-EXPEDICION DE TARJETAS CUYA AUTORIZACION RESUELVE OTRA ADMINISTRACION",
        "AUTORIZACION DE REGRESO",
        "POLICIA - CERTIFICADOS CONCORDANCIA",
        "POLICIA- EXPEDICION/RENOVACION DE DOCUMENTOS DE VIAJE",
        "POLICIA-CARTA DE INVITACION",
        "POLICIA-CERTIFICADOS (DE RESIDENCIA, DE NO RESIDENTE, DE CONCORDANCIA)",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA - TITULOS DE VIAJE",
        "POLICIA-ASIGNACION NIE NO RESIDENTE NO COMUNITARIO",
        "POLICIA-CERTIFICADOS (RESIDENCIA Y CONCORDANCIA)",
    ],
    "Madrid": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "POLICIA TARJETA CONFLICTO UCRANIA",
        "POLICIA-EXP.TARJETA ASOCIADA AL ACUERDO DE RETIRADA (BREXIT)",
        "POLICIA-EXPEDICION DE TARJETAS CUYA AUTORIZACION RESUELVE OTRA ADMINISTRACION",
        "AUTORIZACION DE REGRESO",
        "POLICIA - CERTIFICADOS CONCORDANCIA",
        "POLICIA- EXPEDICION/RENOVACION DE DOCUMENTOS DE VIAJE",
        "POLICIA-CARTA DE INVITACION",
        "POLICIA-CERTIFICADOS (DE RESIDENCIA, DE NO RESIDENTE, DE CONCORDANCIA)",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA - TITULOS DE VIAJE",
        "POLICIA-ASIGNACION NIE NO RESIDENTE NO COMUNITARIO",
        "POLICIA-CERTIFICADOS (RESIDENCIA Y CONCORDANCIA)",
    ],
    "Alicante": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "POLICIA TARJETA CONFLICTO UCRANIA",
        "POLICIA-EXP.TARJETA ASOCIADA AL ACUERDO DE RETIRADA (BREXIT)",
        "AUTORIZACION DE REGRESO",
        "POLICIA-CARTA DE INVITACION",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA-ASIGNACION NIE NO RESIDENTE NO COMUNITARIO",
    ],
    "Valencia": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "POLICIA TARJETA CONFLICTO UCRANIA",
        "POLICIA-EXP.TARJETA ASOCIADA AL ACUERDO DE RETIRADA (BREXIT)",
        "AUTORIZACION DE REGRESO",
        "POLICIA - CERTIFICADOS CONCORDANCIA",
        "POLICIA-CARTA DE INVITACION",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA - TITULOS DE VIAJE",
    ],
    "Málaga": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "POLICIA TARJETA CONFLICTO UCRANIA",
        "AUTORIZACION DE REGRESO",
        "POLICIA-CARTA DE INVITACION",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
        "POLICIA-ASIGNACION DE NIE",
    ],
    "Sevilla": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "POLICIA TARJETA CONFLICTO UCRANIA",
        "AUTORIZACION DE REGRESO",
        "POLICIA - CERTIFICADOS CONCORDANCIA",
        "POLICIA-CARTA DE INVITACION",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
        "POLICIA-ASIGNACION DE NIE",
    ],
    "Murcia": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "POLICIA TARJETA CONFLICTO UCRANIA",
        "AUTORIZACION DE REGRESO",
        "POLICIA-CARTA DE INVITACION",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
        "POLICIA-ASIGNACION DE NIE",
    ],
    "Bizkaia": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "POLICIA TARJETA CONFLICTO UCRANIA",
        "POLICIA-EXP.TARJETA ASOCIADA AL ACUERDO DE RETIRADA (BREXIT)",
        "AUTORIZACION DE REGRESO",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
    ],
    "Gipuzkoa": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "POLICIA TARJETA CONFLICTO UCRANIA",
        "AUTORIZACION DE REGRESO",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
    ],
    "Girona": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "POLICIA TARJETA CONFLICTO UCRANIA",
        "AUTORIZACION DE REGRESO",
        "POLICIA-CARTA DE INVITACION",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
    ],
    "Illes Balears": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "POLICIA TARJETA CONFLICTO UCRANIA",
        "POLICIA-EXP.TARJETA ASOCIADA AL ACUERDO DE RETIRADA (BREXIT)",
        "AUTORIZACION DE REGRESO",
        "POLICIA-CARTA DE INVITACION",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
    ],
    "Las Palmas": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "POLICIA TARJETA CONFLICTO UCRANIA",
        "AUTORIZACION DE REGRESO",
        "POLICIA-CARTA DE INVITACION",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
    ],
    "S.Cruz Tenerife": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "POLICIA TARJETA CONFLICTO UCRANIA",
        "AUTORIZACION DE REGRESO",
        "POLICIA-CARTA DE INVITACION",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
    ],
    "Zaragoza": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "POLICIA TARJETA CONFLICTO UCRANIA",
        "AUTORIZACION DE REGRESO",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
    ],
    "Lleida": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "POLICIA- SOLICITUD DE ASILO",
        "AUTORIZACION DE REGRESO",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
    ],
    "Navarra": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "POLICIA TARJETA CONFLICTO UCRANIA",
        "AUTORIZACION DE REGRESO",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
    ],
    "Tarragona": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "AUTORIZACION DE REGRESO",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
    ],
    "Cádiz": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "AUTORIZACION DE REGRESO",
        "POLICIA-CARTA DE INVITACION",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
    ],
    "Granada": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "AUTORIZACION DE REGRESO",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
    ],
    "Almería": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "AUTORIZACION DE REGRESO",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
    ],
    "Asturias": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "POLICIA TARJETA CONFLICTO UCRANIA",
        "AUTORIZACION DE REGRESO",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
    ],
    "A Coruña": [
        "POLICIA-TOMA DE HUELLAS (EXPEDICION DE TARJETA) INICIAL, RENOVACION, DUPLICADO Y LEY 14/2013",
        "POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.",
        "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)",
        "AUTORIZACION DE REGRESO",
        "POLICIA-ASIGNACION DE NIE",
        "POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO RESIDENTES)",
    ],
}

OFICINAS_POR_PROVINCIA = {
    "Barcelona": [
        "CNP RAMBLA GUIPUSCOA 74, BARCELONA",
        "CNP COMISARIA LHOSPITALET DE LLOBREGAT",
        "CNP COMISARIA BADALONA",
        "CNP COMISARIA CASTELLDEFELS",
        "CNP COMISARIA CERDANYOLA DEL VALLES",
        "CNP COMISARIA CORNELLA DE LLOBREGAT",
        "CNP COMISARIA SANT FELIU DE LLOBREGAT",
        "CNP COMISARIA EL PRAT DE LLOBREGAT",
        "CNP COMISARIA SANT BOI DE LLOBREGAT",
        "CNP COMISARIA VILADECANS",
        "CNP COMISARIA IGUALADA",
        "CNP COMISARIA MATARO",
        "CNP COMISARIA GRANOLLERS",
        "CNP COMISARIA RUBI",
        "CNP COMISARIA SABADELL",
        "CNP COMISARIA MONTCADA I REIXAC",
        "CNP COMISARIA RIPOLLET",
        "CNP COMISARIA SANT ADRIA DEL BESOS",
        "CNP COMISARIA SANT CUGAT DEL VALLES",
        "CNP COMISARIA SANTA COLOMA DE GRAMENET",
        "CNP COMISARIA TERRASSA",
        "CNP COMISARIA VIC",
        "CNP COMISARIA MANRESA",
        "CNP COMISARIA VILAFRANCA DEL PENEDES",
        "CNP COMISARIA VILANOVA I LA GELTRU",
    ],
    "Madrid": [
        "CNP COMISARIA GENERAL EXTRANJERIA C/MIGUEL ANGEL 5",
        "CNP COMISARIA ALCALA DE HENARES",
        "CNP COMISARIA ALCOBENDAS",
        "CNP COMISARIA ALCORCON",
        "CNP COMISARIA ARGANDA DEL REY",
        "CNP COMISARIA BOADILLA DEL MONTE",
        "CNP COMISARIA COLLADO VILLALBA",
        "CNP COMISARIA FUENLABRADA",
        "CNP COMISARIA GETAFE",
        "CNP COMISARIA LEGANES",
        "CNP COMISARIA MAJADAHONDA",
        "CNP COMISARIA MOSTOLES",
        "CNP COMISARIA PARLA",
        "CNP COMISARIA PINTO",
        "CNP COMISARIA POZUELO DE ALARCON",
        "CNP COMISARIA TORREJON DE ARDOZ",
        "CNP COMISARIA VALDEMORO",
        "CNP COMISARIA COSLADA",
        "CNP COMISARIA RIVAS VACIAMADRID",
        "CNP COMISARIA ARANJUEZ",
        "CNP COMISARIA COLMENAR VIEJO",
        "CNP COMISARIA TRES CANTOS",
        "CNP COMISARIA SAN FERNANDO DE HENARES",
        "CNP COMISARIA NAVALCARNERO",
        "CNP COMISARIA HUMANES DE MADRID",
    ],
    "Alicante": [
        "CNP COMISARIA ALICANTE, C/JORGE JUAN 18",
        "CNP COMISARIA BENIDORM",
        "CNP COMISARIA DENIA",
        "CNP COMISARIA ELX/ELCHE",
        "CNP COMISARIA ORIHUELA",
        "CNP COMISARIA TORREVIEJA",
        "CNP COMISARIA VILLENA",
        "CNP COMISARIA ALCOY/ALCOI",
        "CNP COMISARIA CALPE",
        "CNP COMISARIA ALTEA",
        "CNP COMISARIA GUARDAMAR DEL SEGURA",
        "CNP COMISARIA SANTA POLA",
        "CNP COMISARIA PETRER",
    ],
    "Valencia": [
        "CNP COMISARIA GRAN VIA RAMON Y CAJAL 40, VALENCIA",
        "CNP COMISARIA GANDIA","CNP COMISARIA ONTINYENT",
        "CNP COMISARIA SAGUNTO","CNP COMISARIA TORRENT",
        "CNP COMISARIA ALZIRA","CNP COMISARIA XATIVA",
        "CNP COMISARIA PATERNA","CNP COMISARIA BURJASSOT",
        "CNP COMISARIA MISLATA","CNP COMISARIA MANISES",
        "CNP COMISARIA REQUENA",
    ],
    "Málaga": [
        "CNP COMISARIA MALAGA, AVENIDA DE LA ROSALEDA",
        "CNP COMISARIA MARBELLA","CNP COMISARIA FUENGIROLA",
        "CNP COMISARIA TORREMOLINOS","CNP COMISARIA VELEZ-MALAGA",
        "CNP COMISARIA ANTEQUERA","CNP COMISARIA RONDA",
        "CNP COMISARIA ESTEPONA","CNP COMISARIA BENALMADENA",
        "CNP COMISARIA NERJA","CNP COMISARIA ALHAURIN DE LA TORRE",
    ],
    "Sevilla": [
        "CNP COMISARIA SEVILLA, C/BORBOLLA",
        "CNP COMISARIA ALCALA DE GUADAIRA","CNP COMISARIA DOS HERMANAS",
        "CNP COMISARIA ECIJA","CNP COMISARIA LEBRIJA",
        "CNP COMISARIA MORON DE LA FRONTERA","CNP COMISARIA OSUNA",
        "CNP COMISARIA UTRERA",
    ],
    "Murcia": [
        "CNP COMISARIA MURCIA, C/RIO SEGURA","CNP COMISARIA CARTAGENA",
        "CNP COMISARIA LORCA","CNP COMISARIA MOLINA DE SEGURA",
        "CNP COMISARIA YECLA","CNP COMISARIA CIEZA",
        "CNP COMISARIA MAZARRON","CNP COMISARIA JUMILLA",
        "CNP COMISARIA AGUILAS","CNP COMISARIA SAN JAVIER",
        "CNP COMISARIA TORRE PACHECO",
    ],
    "Bizkaia": [
        "CNP COMISARIA BILBAO, C/LARRAKOETXEA","CNP COMISARIA BARAKALDO",
        "CNP COMISARIA BASAURI","CNP COMISARIA GETXO",
        "CNP COMISARIA SESTAO","CNP COMISARIA DURANGO",
    ],
    "Gipuzkoa": [
        "CNP COMISARIA SAN SEBASTIAN, PASEO LARRATXO",
        "CNP COMISARIA IRUN","CNP COMISARIA EIBAR","CNP COMISARIA TOLOSA",
    ],
    "Girona": [
        "CNP COMISARIA GIRONA, C/JULIA DE CHIA","CNP COMISARIA BLANES",
        "CNP COMISARIA FIGUERES","CNP COMISARIA LLORET DE MAR",
        "CNP COMISARIA OLOT","CNP COMISARIA ROSES",
        "CNP COMISARIA SANT FELIU DE GUIXOLS",
    ],
    "Illes Balears": [
        "CNP COMISARIA PALMA, VIA ALEMANYA 2","CNP COMISARIA IBIZA",
        "CNP COMISARIA MANACOR","CNP COMISARIA INCA",
        "CNP COMISARIA MAHON/MAO","CNP COMISARIA CALVIA",
        "CNP COMISARIA LLUCMAJOR",
    ],
    "Las Palmas": [
        "CNP COMISARIA LAS PALMAS GC, C/HORTENSIA","CNP COMISARIA TELDE",
        "CNP COMISARIA MASPALOMAS","CNP COMISARIA ARRECIFE",
        "CNP COMISARIA SANTA LUCIA DE TIRAJANA",
    ],
    "S.Cruz Tenerife": [
        "CNP COMISARIA SANTA CRUZ TENERIFE","CNP COMISARIA LA LAGUNA",
        "CNP COMISARIA ARONA","CNP COMISARIA ADEJE",
        "CNP COMISARIA PUERTO DE LA CRUZ","CNP COMISARIA SANTA CRUZ DE LA PALMA",
    ],
    "Granada": [
        "CNP COMISARIA GRANADA, C/DUQUESA","CNP COMISARIA MOTRIL",
        "CNP COMISARIA GUADIX","CNP COMISARIA LOJA","CNP COMISARIA BAZA",
    ],
    "Zaragoza": [
        "CNP COMISARIA ZARAGOZA, C/RAMON Y CAJAL 2","CNP COMISARIA CALATAYUD",
        "CNP COMISARIA EJEA DE LOS CABALLEROS","CNP COMISARIA TARAZONA",
    ],
    "Cádiz": [
        "CNP COMISARIA CADIZ","CNP COMISARIA ALGECIRAS",
        "CNP COMISARIA JEREZ DE LA FRONTERA",
        "CNP COMISARIA LA LINEA DE LA CONCEPCION",
        "CNP COMISARIA PUERTO DE SANTA MARIA","CNP COMISARIA SAN FERNANDO",
        "CNP COMISARIA SANLUCAR DE BARRAMEDA","CNP COMISARIA TARIFA",
    ],
    "Almería": [
        "CNP COMISARIA ALMERIA, C/NAVARRO RODRIGO","CNP COMISARIA EL EJIDO",
        "CNP COMISARIA ROQUETAS DE MAR","CNP COMISARIA ADRA",
        "CNP COMISARIA VERA","CNP COMISARIA HUERCAL-OVERA",
    ],
    "Asturias": [
        "CNP COMISARIA OVIEDO, C/GENERAL YAGUE","CNP COMISARIA AVILES",
        "CNP COMISARIA GIJON","CNP COMISARIA LANGREO","CNP COMISARIA MIERES",
    ],
    "A Coruña": [
        "CNP COMISARIA A CORUNA, RAMON Y CAJAL","CNP COMISARIA FERROL",
        "CNP COMISARIA SANTIAGO DE COMPOSTELA","CNP COMISARIA OLEIROS",
    ],
    "Tarragona": [
        "CNP COMISARIA TARRAGONA","CNP COMISARIA REUS",
        "CNP COMISARIA TORTOSA","CNP COMISARIA EL VENDRELL",
        "CNP COMISARIA SALOU","CNP COMISARIA CAMBRILS",
    ],
    "Navarra": [
        "CNP COMISARIA PAMPLONA, C/YANGUAS Y MIRANDA",
        "CNP COMISARIA TUDELA","CNP COMISARIA BURLADA",
    ],
    "Cantabria": [
        "CNP COMISARIA SANTANDER, AV VALDECILLA",
        "CNP COMISARIA TORRELAVEGA","CNP COMISARIA CASTRO URDIALES",
    ],
    "Huelva": [
        "CNP COMISARIA HUELVA","CNP COMISARIA ALMONTE","CNP COMISARIA LEPE",
    ],
    "Córdoba": [
        "CNP COMISARIA CORDOBA, RONDA DE LOS TEJARES","CNP COMISARIA LUCENA",
        "CNP COMISARIA MONTILLA","CNP COMISARIA POZOBLANCO",
    ],
    "Jaén": [
        "CNP COMISARIA JAEN","CNP COMISARIA LINARES",
        "CNP COMISARIA UBEDA","CNP COMISARIA ANDUJAR",
    ],
    "Pontevedra": [
        "CNP COMISARIA VIGO, C/LALINDE","CNP COMISARIA PONTEVEDRA",
        "CNP COMISARIA VILAGARCIA DE AROUSA","CNP COMISARIA TUI",
    ],
    "Castellón": [
        "CNP COMISARIA CASTELLON DE LA PLANA","CNP COMISARIA BENICARLOS",
        "CNP COMISARIA VILA-REAL","CNP COMISARIA VINAROS",
    ],
    "Lleida": [
        "CNP LLEIDA, DE L`ENSENYANCA, 2, LLEIDA",
        "CNP COMISARIA BALAGUER","CNP COMISARIA LA SEU D URGELL",
    ],
    "Araba":   ["CNP COMISARIA VITORIA-GASTEIZ","CNP COMISARIA LLODIO"],
    "La Rioja":["CNP COMISARIA LOGRONO","CNP COMISARIA CALAHORRA"],
    "Ceuta":   ["CNP COMISARIA CEUTA"],
    "Melilla": ["CNP COMISARIA MELILLA"],
}

def get_tramites(prov):
    return TRAMITES_POR_PROVINCIA.get(prov, DEFAULT_TRAMITES)

def get_oficinas(prov):
    return OFICINAS_POR_PROVINCIA.get(prov, [])

# ── DATABASE ──────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT,
        plan TEXT DEFAULT 'free',
        plan_expiry TEXT DEFAULT NULL,
        created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        provincia TEXT, tramite TEXT, oficina TEXT,
        active INTEGER DEFAULT 1, last_notified TEXT, created_at TEXT)""")
    conn.commit(); conn.close()

def ensure_user(uid, uname):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id,username,plan,created_at) VALUES (?,?,?,?)",
        (uid, uname or "", "free", datetime.now().isoformat()))
    conn.commit(); conn.close()

def get_plan(uid):
    """Returns: 'free', 'monthly', 'lifetime'"""
    conn = sqlite3.connect(DB_PATH)
    r = conn.execute("SELECT plan, plan_expiry FROM users WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    if not r: return "free"
    plan, expiry = r
    if plan == "lifetime": return "lifetime"
    if plan == "monthly" and expiry:
        if datetime.fromisoformat(expiry) > datetime.now():
            return "monthly"
    return "free"

def set_plan(uid, plan_type, months=1):
    """plan_type: 'free', 'monthly', 'lifetime'"""
    conn = sqlite3.connect(DB_PATH)
    if plan_type == "lifetime":
        conn.execute("UPDATE users SET plan='lifetime', plan_expiry=NULL WHERE user_id=?", (uid,))
    elif plan_type == "monthly":
        expiry = (datetime.now() + timedelta(days=30*months)).isoformat()
        conn.execute("UPDATE users SET plan='monthly', plan_expiry=? WHERE user_id=?", (expiry, uid))
    else:
        conn.execute("UPDATE users SET plan='free', plan_expiry=NULL WHERE user_id=?", (uid,))
    conn.commit(); conn.close()

def get_limit(uid):
    plan = get_plan(uid)
    if plan in ("monthly", "lifetime"): return 999
    return FREE_LIMIT

def count_subs(uid):
    conn = sqlite3.connect(DB_PATH)
    n = conn.execute(
        "SELECT COUNT(*) FROM subscriptions WHERE user_id=? AND active=1",(uid,)
    ).fetchone()[0]
    conn.close(); return n

def add_sub(uid, prov, tram, ofic):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO subscriptions (user_id,provincia,tramite,oficina,created_at) VALUES (?,?,?,?,?)",
        (uid, prov, tram, ofic, datetime.now().isoformat()))
    conn.commit(); conn.close()

def get_subs(uid):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id,provincia,tramite,oficina,last_notified FROM subscriptions WHERE user_id=? AND active=1",
        (uid,)).fetchall()
    conn.close(); return rows

def del_sub(sid, uid):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE subscriptions SET active=0 WHERE id=? AND user_id=?",(sid,uid))
    conn.commit(); conn.close()

def all_active_subs():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id,user_id,provincia,tramite,oficina,last_notified FROM subscriptions WHERE active=1"
    ).fetchall()
    conn.close(); return rows

def update_notified(sid):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE subscriptions SET last_notified=? WHERE id=?",
        (datetime.now().isoformat(), sid))
    conn.commit(); conn.close()

def all_users():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close(); return [r[0] for r in rows]

# ── CHECKER ───────────────────────────────────────────────────────────────────
async def check_cita(provincia, tramite, oficina):
    pcode = PROVINCIA_CODES.get(provincia, "28")
    url = f"https://icp.administracionelectronica.gob.es/icpplus/citar?p={pcode}&locale=es"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "es-ES,es;q=0.9",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, headers=headers,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as r:
                if r.status != 200: return None
                html = await r.text()

        no_signals = [
            "en este momento no hay citas disponibles",
            "no hay citas disponibles",
            "actualmente no existen citas",
            "no existen citas disponibles",
            "sin citas disponibles",
            "no se han encontrado citas",
        ]
        html_lower = html.lower()
        for sig in no_signals:
            if sig in html_lower: return None

        yes_signals = [
            "calendari","seleccione.*fecha","cita.*disponible",
            "fecha.*disponible","hora.*disponible","elegir.*fecha",
            "seleccionar.*dia","reservar.*cita","dia.*disponible",
        ]
        for sig in yes_signals:
            if re.search(sig, html_lower):
                return {"provincia":provincia,"tramite":tramite,
                        "oficina":oficina,"url":url}
        return None
    except Exception as e:
        logger.warning(f"Check error {provincia}: {e}")
        return None

# ── KEYBOARDS ─────────────────────────────────────────────────────────────────
def provincia_keyboard():
    kb = []; row = []
    for p in PROVINCIAS:
        row.append(InlineKeyboardButton(p, callback_data=f"P:{p}"))
        if len(row) == 3: kb.append(row); row = []
    if row: kb.append(row)
    return InlineKeyboardMarkup(kb)

def tramite_keyboard(prov):
    tramites = get_tramites(prov)
    kb = []
    for i, t in enumerate(tramites):
        label = t[:55]+"..." if len(t)>55 else t
        kb.append([InlineKeyboardButton(label, callback_data=f"T:{i}")])
    return InlineKeyboardMarkup(kb)

def oficina_keyboard(prov):
    oficinas = get_oficinas(prov)
    kb = [[InlineKeyboardButton("Cualquiera", callback_data="O:Cualquiera")]]
    for o in oficinas:
        label = o[:55]+"..." if len(o)>55 else o
        kb.append([InlineKeyboardButton(label, callback_data=f"O:{o[:80]}")])
    return InlineKeyboardMarkup(kb)

# ── HANDLERS ──────────────────────────────────────────────────────────────────
async def cmd_start(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ensure_user(u.effective_user.id, u.effective_user.username)
    await u.message.reply_text(
        "🤖 Extranjeria Notify Bot\n\n"
        "Te aviso cuando haya cita disponible en Cita Previa.\n\n"
        "/agregar_aviso - Anadir aviso\n"
        "/borrar_aviso - Eliminar aviso\n"
        "/estado_cuenta - Ver tu cuenta\n"
        "/estadisticas - Estadisticas\n"
        "/contratar_suscripcion - Planes PRO\n"
        "/help - Ayuda"
    )

async def cmd_agregar(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    ensure_user(uid, u.effective_user.username)
    if count_subs(uid) >= get_limit(uid):
        plan = get_plan(uid)
        await u.message.reply_text(
            f"Alcanzaste el limite de suscripciones.\n"
            f"Plan actual: {plan}\n"
            "Contrata PRO: /contratar_suscripcion")
        return ConversationHandler.END
    await u.message.reply_text(
        "Selecciona la provincia requerida",
        reply_markup=provincia_keyboard())
    return ASK_PROVINCIA

async def cb_provincia(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    prov = q.data[2:]
    ctx.user_data["prov"] = prov
    ctx.user_data["tramites"] = get_tramites(prov)
    await q.edit_message_text(
        f"Provincia: {prov}\n\nSelecciona el tramite:",
        reply_markup=tramite_keyboard(prov))
    return ASK_TRAMITE

async def cb_tramite(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    idx = int(q.data[2:])
    tramites = ctx.user_data.get("tramites", DEFAULT_TRAMITES)
    tram = tramites[idx]
    ctx.user_data["tram"] = tram
    prov = ctx.user_data.get("prov","?")
    await q.edit_message_text(
        f"Provincia: {prov}\nTramite: {tram[:60]}\n\nSelecciona la oficina:",
        reply_markup=oficina_keyboard(prov))
    return ASK_OFICINA

async def cb_oficina(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    ofic = q.data[2:]
    prov = ctx.user_data.get("prov","?")
    tram = ctx.user_data.get("tram","?")
    uid = q.from_user.id
    add_sub(uid, prov, tram, ofic)
    await q.edit_message_text(
        f"Aviso anadido!\n\n"
        f"Provincia: {prov}\n"
        f"Tramite: {tram}\n"
        f"Oficina: {ofic}\n\n"
        f"Te avisare cuando haya cita disponible.")
    return ConversationHandler.END

async def cmd_estado(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    ensure_user(uid, u.effective_user.username)
    subs = get_subs(uid)
    plan = get_plan(uid)
    limit = get_limit(uid)
    limit_str = "Ilimitado" if limit==999 else str(limit)

    # Plan label
    if plan == "lifetime":
        plan_label = "LIFETIME (ilimitado para siempre)"
    elif plan == "monthly":
        conn = sqlite3.connect(DB_PATH)
        exp = conn.execute("SELECT plan_expiry FROM users WHERE user_id=?",(uid,)).fetchone()[0]
        conn.close()
        plan_label = f"PRO Mensual (expira: {exp[:10]})"
    else:
        plan_label = f"Gratuito ({len(subs)}/{limit_str} avisos)"

    txt = f"Tu cuenta\n\nPlan: {plan_label}\n\n"
    if subs:
        txt += "Avisos activos:\n\n"
        for sid,prov,tram,ofic,last in subs:
            last_str = last[:16] if last else "Nunca"
            txt += f"[{sid}] {prov}\n  {tram[:45]}\n  {ofic}\n  Ultimo: {last_str}\n\n"
    else:
        txt += "No tienes avisos. Usa /agregar_aviso"
    await u.message.reply_text(txt)

async def cmd_borrar(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    subs = get_subs(u.effective_user.id)
    if not subs:
        await u.message.reply_text("No tienes avisos activos."); return
    kb = []
    for sid,prov,tram,ofic,_ in subs:
        kb.append([InlineKeyboardButton(
            f"[{sid}] {prov} - {tram[:30]}", callback_data=f"DEL:{sid}")])
    kb.append([InlineKeyboardButton("Cancelar", callback_data="DEL:cancel")])
    await u.message.reply_text("Selecciona el aviso a borrar:",
                                reply_markup=InlineKeyboardMarkup(kb))

async def cb_del(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    val = q.data[4:]
    if val == "cancel":
        await q.edit_message_text("Cancelado."); return
    del_sub(int(val), q.from_user.id)
    await q.edit_message_text(f"Aviso [{val}] eliminado.")

async def cmd_contratar(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("📅 PRO Mensual (Demo)", callback_data="PLAN:monthly")],
        [InlineKeyboardButton("♾ LIFETIME (Demo)",     callback_data="PLAN:lifetime")],
    ]
    await u.message.reply_text(
        "Planes disponibles\n\n"
        "📅 PRO Mensual\n"
        "   Avisos ilimitados por 30 dias\n\n"
        "♾ LIFETIME\n"
        "   Avisos ilimitados para siempre\n"
        "   Pago unico - nunca expira\n\n"
        "Contacta al admin para activar.",
        reply_markup=InlineKeyboardMarkup(kb))

async def cb_plan(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    plan_type = q.data.split(":")[1]
    uid = q.from_user.id
    set_plan(uid, plan_type)
    if plan_type == "lifetime":
        await q.edit_message_text(
            "♾ LIFETIME activado!\n\n"
            "Avisos ilimitados para siempre. Nunca expira.")
    else:
        conn = sqlite3.connect(DB_PATH)
        exp = conn.execute(
            "SELECT plan_expiry FROM users WHERE user_id=?",(uid,)).fetchone()[0]
        conn.close()
        await q.edit_message_text(
            f"PRO Mensual activado!\n\nExpira: {exp[:10]}\nAvisos ilimitados.")

async def cmd_stats(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT tramite,COUNT(*) c FROM subscriptions WHERE active=1 "
        "GROUP BY tramite ORDER BY c DESC LIMIT 8").fetchall()
    conn.close()
    if not rows: await u.message.reply_text("Sin datos aun."); return
    txt = "Tramites mas monitorizados:\n\n"
    for i,(t,c) in enumerate(rows,1): txt += f"{i}. {t[:50]} - {c}\n"
    await u.message.reply_text(txt)

async def cmd_help(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text(
        "Ayuda\n\n"
        "1. /agregar_aviso - elige provincia, tramite, oficina\n"
        "2. Bot comprueba cada 30 segundos\n"
        "3. Cuando hay cita - recibes notificacion\n\n"
        "Planes:\n"
        "Gratis: 3 avisos\n"
        "PRO Mensual: ilimitados 30 dias\n"
        "LIFETIME: ilimitados para siempre\n\n"
        "/contratar_suscripcion - Ver planes")

# ── BACKGROUND CHECKER ────────────────────────────────────────────────────────
async def checker(app):
    logger.info("Checker started - every 30s")
    try:
        bot_info = await app.bot.get_me()
        bot_username = f"@{bot_info.username}"
    except Exception:
        bot_username = "@MiCitaBot"

    while True:
        try:
            subs = all_active_subs()
            logger.info(f"Checking {len(subs)} subscriptions")
            for sid, uid, prov, tram, ofic, last in subs:
                try:
                    result = await check_cita(prov, tram, ofic)
                    if result:
                        if last:
                            elapsed = (datetime.now()-datetime.fromisoformat(last)).total_seconds()
                            if elapsed < 1800: continue
                        kb = [[InlineKeyboardButton(
                            "Haz clic para acceder al sitio oficial",
                            url=result["url"])]]
                        msg = (
                            f"🔔Cita encontrada🔔\n\n"
                            f"✅Provincia {prov}\n\n"
                            f"✅Tramite {tram}\n\n"
                            f"✅Oficinas\n\n"
                            f"{ofic}\n\n"
                            f"{bot_username}"
                        )
                        await app.bot.send_message(
                            chat_id=uid, text=msg,
                            reply_markup=InlineKeyboardMarkup(kb))
                        update_notified(sid)
                        logger.info(f"Notified {uid} - {prov}")
                except RetryAfter as e:
                    logger.warning(f"Rate limited, waiting {e.retry_after}s")
                    await asyncio.sleep(e.retry_after)
                except (NetworkError, TimedOut):
                    logger.warning("Network error in checker, continuing")
                    await asyncio.sleep(5)
                except Exception as e:
                    logger.error(f"Sub {sid} error: {e}")
                await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Checker loop error: {e}\n{traceback.format_exc()}")
        await asyncio.sleep(CHECK_INTERVAL)

async def post_init(app: Application):
    asyncio.create_task(checker(app))

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    init_db()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    conv = ConversationHandler(
        entry_points=[CommandHandler("agregar_aviso", cmd_agregar)],
        states={
            ASK_PROVINCIA: [CallbackQueryHandler(cb_provincia, pattern="^P:")],
            ASK_TRAMITE:   [CallbackQueryHandler(cb_tramite,   pattern="^T:")],
            ASK_OFICINA:   [CallbackQueryHandler(cb_oficina,   pattern="^O:")],
        },
        fallbacks=[CommandHandler("start", cmd_start)],
        per_message=False,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("start",                 cmd_start))
    app.add_handler(CommandHandler("estado_cuenta",         cmd_estado))
    app.add_handler(CommandHandler("contratar_suscripcion", cmd_contratar))
    app.add_handler(CommandHandler("borrar_aviso",          cmd_borrar))
    app.add_handler(CommandHandler("estadisticas",          cmd_stats))
    app.add_handler(CommandHandler("help",                  cmd_help))
    app.add_handler(CallbackQueryHandler(cb_del,  pattern="^DEL:"))
    app.add_handler(CallbackQueryHandler(cb_plan, pattern="^PLAN:"))

    logger.info("Bot started!")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    main()
