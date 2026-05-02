# data.py — All 52 Provincias, Tramites A-Z, Oficinas A-Z

def _s(d):
    """Sort dict by value A-Z"""
    return dict(sorted(d.items(), key=lambda x: x[1]))

def _sl(lst):
    """Sort list A-Z"""
    return sorted(lst)

PROVINCIA_DATA = {
    "1": {
        "name": "Álava",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4038": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "20":   "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA VITORIA-GASTEIZ - C/ JOSE LUIS IÑARRA 4",
        ])
    },
    "2": {
        "name": "Albacete",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4038": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "20":   "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA ALBACETE - C/ TEODORO CAMINO 5",
            "CNP - COMISARIA HELLIN - C/ CASTILLA LA MANCHA 2",
        ])
    },
    "3": {
        "name": "Alicante",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4094": "POLICIA - BREXIT (Tarjeta Ciudadanos Británicos)",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4038": "POLICIA - CERTIFICADOS Y ASIGNACION NIE (Comunitarios)",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4079": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA ALICANTE CENTRO - C/ MEDICO PASCUAL PEREZ 37",
            "CNP - COMISARIA BENIDORM - C/ LLUIS SITGES 3",
            "CNP - COMISARIA DENIA - C/ DIANA 14",
            "CNP - COMISARIA ELCHE - C/ CORREGIDOR JOAQUIN MENDUIÑA 30",
            "CNP - COMISARIA ELDA - C/ OSCAR ESPLA 15",
            "CNP - COMISARIA ORIHUELA - C/ JOSE ANTONIO 2",
            "CNP - COMISARIA TORREVIEJA - AV. DR. GREGORIO MARAÑON 22",
            "CNP - COMISARIA VILLENA - AV. DE LA CONSTITUCION 50",
        ])
    },
    "4": {
        "name": "Almería",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA ALMERIA CENTRO - C/ CASTRO 4",
            "CNP - COMISARIA EL EJIDO - C/ BENITAGLA 4",
            "CNP - COMISARIA ROQUETAS DE MAR - C/ JOSE MANZANO 2",
        ])
    },
    "33": {
        "name": "Asturias",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA AVILES - C/ LA MURALLA 4",
            "CNP - COMISARIA GIJON - C/ RODRIGUEZ SAN PEDRO 2",
            "CNP - COMISARIA LANGREO - C/ LLARANES 7",
            "CNP - COMISARIA OVIEDO - C/ GENERAL ELORZA 32",
        ])
    },
    "5": {
        "name": "Ávila",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4038": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "20":   "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA AVILA - C/ DUQUE DE ALBA 2",
        ])
    },
    "6": {
        "name": "Badajoz",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA BADAJOZ - C/ RAFAEL LUCENQUI 5",
            "CNP - COMISARIA DON BENITO - AV. VILLANUEVA 2",
            "CNP - COMISARIA MERIDA - C/ SAGASTA 15",
        ])
    },
    "8": {
        "name": "Barcelona",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4094": "POLICIA - BREXIT (Tarjeta Ciudadanos Británicos)",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4049": "POLICIA - CERTIFICADOS DE RESIDENCIA/NO RESIDENCIA",
            "4096": "POLICIA - CERTIFICADOS Y ASIGNACION NIE (Comunitarios)",
            "4079": "POLICIA - CERTIFICADOS Y ASIGNACION NIE (No Comunitarios)",
            "4047": "POLICIA - EXPEDICIÓN TARJETAS (Dir. Gral. Migraciones)",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4078": "POLICIA - SOLICITUD ASILO",
            "4031": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA BADALONA - AVDA. DELS VENTS 9",
            "CNP - COMISARIA CASTELLDEFELS - PLAÇA DE L'ESPERANTO 4",
            "CNP - COMISARIA CERDANYOLA DEL VALLES - VERGE DE LES FEIXES 4",
            "CNP - COMISARIA CORNELLA DE LLOBREGAT - AV. SANT ILDEFONS S/N",
            "CNP - COMISARIA EL PRAT DE LLOBREGAT - CENTRE 4",
            "CNP - COMISARIA GRANOLLERS - RICOMA 65",
            "CNP - COMISARIA IGUALADA - PRAT DE LA RIBA 13",
            "CNP - COMISARIA L'HOSPITALET DE LLOBREGAT - Rbla. Just Oliveres 43",
            "CNP - COMISARIA MANRESA - SOLER I MARCH 5",
            "CNP - COMISARIA MATARO - AV. GATASSA 15",
            "CNP - COMISARIA MONTCADA I REIXAC - MAJOR 38",
            "CNP - COMISARIA RIPOLLET - TAMARIT 78",
            "CNP - COMISARIA RUBI - TERRASSA 16",
            "CNP - COMISARIA SABADELL - BATLLEVELL 115",
            "CNP - COMISARIA SANT ADRIA DEL BESOS - AV. JOAN XXIII 2",
            "CNP - COMISARIA SANT BOI DE LLOBREGAT - RIERA BASTE 43",
            "CNP - COMISARIA SANT CUGAT DEL VALLES - VALLES 1",
            "CNP - COMISARIA SANT FELIU DE LLOBREGAT - CARRERETES 9",
            "CNP - COMISARIA SANTA COLOMA DE GRAMENET - IRLANDA 67",
            "CNP - COMISARIA TERRASSA - BALDRICH 13",
            "CNP - COMISARIA VIC - BISBE MORGADES 4",
            "CNP - COMISARIA VILADECANS - AVDA. BALLESTER 2",
            "CNP - COMISARIA VILAFRANCA DEL PENEDES - AV. RONDA DEL MAR 109",
            "CNP - COMISARIA VILANOVA I LA GELTRU - VAPOR 19",
            "CNP MALLORCA-GRANADOS - MALLORCA 213",
            "CNP - RAMBLA GUIPUSCOA 74",
        ])
    },
    "48": {
        "name": "Bizkaia",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA BARAKALDO - C/ BUEN PASTOR 1",
            "CNP - COMISARIA BASAURI - C/ ARIZ 30",
            "CNP - COMISARIA BILBAO CENTRO - C/ LUIS BRIÑAS 14",
            "CNP - COMISARIA DURANGO - C/ KURUTZIAGA 28",
            "CNP - COMISARIA GETXO - AV. LOS CHOPOS 2",
        ])
    },
    "9": {
        "name": "Burgos",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA BURGOS - C/ SANZ PASTOR 2",
            "CNP - COMISARIA MIRANDA DE EBRO - AV. NAVARRA 24",
        ])
    },
    "10": {
        "name": "Cáceres",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA CACERES - C/ MONTESINOS 2",
            "CNP - COMISARIA PLASENCIA - C/ VIDRIERAS 7",
        ])
    },
    "11": {
        "name": "Cádiz",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4094": "POLICIA - BREXIT (Tarjeta Ciudadanos Británicos)",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA ALGECIRAS - C/ JOSE ANTONIO 5",
            "CNP - COMISARIA CADIZ - C/ ANA DE VIYA 1",
            "CNP - COMISARIA EL PUERTO DE SANTA MARIA - C/ LUIS DE REQUESENS 3",
            "CNP - COMISARIA JEREZ DE LA FRONTERA - C/ SEVILLA 1",
            "CNP - COMISARIA LA LINEA DE LA CONCEPCION - C/ DUQUE DE TETUÁN 17",
            "CNP - COMISARIA SANLUCAR DE BARRAMEDA - C/ BARRAMEDA 2",
        ])
    },
    "39": {
        "name": "Cantabria",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA SANTANDER - C/ VARGAS 51",
            "CNP - COMISARIA TORRELAVEGA - C/ INDUSTRIA 3",
        ])
    },
    "12": {
        "name": "Castellón",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA CASTELLON DE LA PLANA - C/ ORFEBRES 6",
            "CNP - COMISARIA VILA-REAL - C/ MAYOR 78",
            "CNP - COMISARIA VINAROS - C/ SANT GREGORI 2",
        ])
    },
    "51": {
        "name": "Ceuta",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4031": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4078": "POLICIA - SOLICITUD ASILO",
            "20":   "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA CEUTA - C/ RECINTO SUR S/N",
        ])
    },
    "13": {
        "name": "Ciudad Real",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA CIUDAD REAL - C/ ALARCOS 20",
            "CNP - COMISARIA PUERTOLLANO - C/ JESUS FERNANDEZ MALO 1",
        ])
    },
    "14": {
        "name": "Córdoba",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA CORDOBA CENTRO - C/ POETA JUAN BERNIER 2",
            "CNP - COMISARIA LUCENA - C/ MARQUES DE COMARES 23",
            "CNP - COMISARIA POZOBLANCO - C/ DOCTOR MANUEL COBOS 1",
        ])
    },
    "16": {
        "name": "Cuenca",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA CUENCA - C/ FERMIN CABALLERO 8",
            "CNP - COMISARIA TARANCÓN - C/ GOYA 4",
        ])
    },
    "20": {
        "name": "Gipuzkoa",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA IRUN - AV. IPARRALDE 34",
            "CNP - COMISARIA SAN SEBASTIAN - C/ EASO 8",
        ])
    },
    "17": {
        "name": "Girona",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA BLANES - C/ ESPLANADA DEL PORT 1",
            "CNP - COMISARIA FIGUERES - C/ AIRÀ 10",
            "CNP - COMISARIA GIRONA - C/ BACIÀ 4",
            "CNP - COMISARIA OLOT - C/ SANT ROCA 22",
        ])
    },
    "18": {
        "name": "Granada",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA BAZA - C/ PEDRO POVEDA 2",
            "CNP - COMISARIA GRANADA CENTRO - C/ DUQUESA 21",
            "CNP - COMISARIA MOTRIL - C/ AVENIDA 1",
        ])
    },
    "19": {
        "name": "Guadalajara",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA AZUQUECA DE HENARES - AV. CONSTITUCION 17",
            "CNP - COMISARIA GUADALAJARA - C/ ARAGON 4",
        ])
    },
    "21": {
        "name": "Huelva",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA ALMONTE - C/ REAL 2",
            "CNP - COMISARIA HUELVA - C/ PLUS ULTRA 4",
            "CNP - COMISARIA LEPE - C/ CERVANTES 2",
        ])
    },
    "22": {
        "name": "Huesca",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA FRAGA - C/ PIRINEOS 2",
            "CNP - COMISARIA HUESCA - C/ RICARDO DEL ARCO 6",
            "CNP - COMISARIA MONZON - C/ SANTA BARBARA 11",
        ])
    },
    "23": {
        "name": "Jaén",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA ANDUJAR - C/ MUÑOZ GRANDE 7",
            "CNP - COMISARIA JAEN - C/ ARQUITECTO BERGES 14",
            "CNP - COMISARIA LINARES - C/ CORREDERA DE SAN MARCOS 5",
            "CNP - COMISARIA UBEDA - C/ HORNO CONTADOR 2",
        ])
    },
    "26": {
        "name": "La Rioja",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA CALAHORRA - C/ ERCILLA 4",
            "CNP - COMISARIA LOGROÑO - C/ PORTALES 3",
        ])
    },
    "35": {
        "name": "Las Palmas",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4094": "POLICIA - BREXIT (Tarjeta Ciudadanos Británicos)",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA FUERTEVENTURA (PUERTO DEL ROSARIO) - AV. PRIMERO DE MAYO 39",
            "CNP - COMISARIA LANZAROTE (ARRECIFE) - C/ JOSE ANTONIO 36",
            "CNP - COMISARIA LAS PALMAS CENTRO - C/ BUENOS AIRES 4",
            "CNP - COMISARIA MASPALOMAS - AV. TIRAJANA 14",
            "CNP - COMISARIA TELDE - C/ LEON Y CASTILLO 73",
        ])
    },
    "24": {
        "name": "León",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA LEON - C/ VILLA BENAVENTE 8",
            "CNP - COMISARIA PONFERRADA - C/ ORTEGA Y GASSET 1",
        ])
    },
    "25": {
        "name": "Lleida",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA LLEIDA - C/ DOCTOR COMBELLES 2",
        ])
    },
    "27": {
        "name": "Lugo",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA LUGO - C/ CAMPO CASTELO 7",
        ])
    },
    "28": {
        "name": "Madrid",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4094": "POLICIA - BREXIT (Tarjeta Ciudadanos Británicos)",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4049": "POLICIA - CERTIFICADOS DE RESIDENCIA/NO RESIDENCIA",
            "4096": "POLICIA - CERTIFICADOS Y ASIGNACION NIE (Comunitarios)",
            "4079": "POLICIA - CERTIFICADOS Y ASIGNACION NIE (No Comunitarios)",
            "4047": "POLICIA - EXPEDICIÓN TARJETAS (Dir. Gral. Migraciones)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4078": "POLICIA - SOLICITUD ASILO",
            "4031": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "COMISARIA ALCALA DE HENARES - AV. JUAN CARLOS I 8",
            "COMISARIA ALCOBENDAS - C/ JUAN RAMON JIMENEZ 4",
            "COMISARIA ALCORCON - C/ MOSTOLES 8",
            "COMISARIA ARGANZUELA - C/ EMBAJADORES 116",
            "COMISARIA CARABANCHEL - C/ GENERAL RICARDOS 110",
            "COMISARIA COSLADA - C/ HENARES 12",
            "COMISARIA FUENCARRAL - C/ PLASENCIA 3",
            "COMISARIA GETAFE - AV. BLAS TELLO 3",
            "COMISARIA HORTALEZA - C/ HERACLITO 2",
            "COMISARIA LATINA - C/ AVIACION ESPAÑOLA S/N",
            "COMISARIA LEGANES - C/ OBISPADO 1",
            "COMISARIA MORATALAZ - C/ CORREGIDOR DIEGO DE VALDERRABANO 13",
            "COMISARIA MOSTOLES - C/ NEVERO 2",
            "COMISARIA PARLA - C/ ARCO 2",
            "COMISARIA POZUELO DE ALARCON - C/ AGUILAS 3",
            "COMISARIA RETIRO - C/ DOCTOR ESQUERDO 26",
            "COMISARIA TETUAN - C/ RAMON Y CAJAL 9",
            "COMISARIA TORREJON DE ARDOZ - C/ MAYOR 70",
            "COMISARIA USERA - C/ PRADILLO 40",
            "COMISARIA VALLECAS - C/ SIERRA DE ALQUIFE 5",
            "OFICINA DE ASILO - PRADILLO 40",
        ])
    },
    "29": {
        "name": "Málaga",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4094": "POLICIA - BREXIT (Tarjeta Ciudadanos Británicos)",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4078": "POLICIA - SOLICITUD ASILO",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA ANTEQUERA - C/ INFANTE DON FERNANDO 40",
            "CNP - COMISARIA COIN - C/ REAL 80",
            "CNP - COMISARIA ESTEPONA - AV. ESPAÑA 140",
            "CNP - COMISARIA FUENGIROLA - C/ CAPITAN 5",
            "CNP - COMISARIA MALAGA CENTRO - C/ MAURICIO MORO PARETO 1",
            "CNP - COMISARIA MARBELLA - C/ JACINTO BENAVENTE S/N",
            "CNP - COMISARIA TORREMOLINOS - AV. PALMA DE MALLORCA 12",
            "CNP - COMISARIA VELEZ-MALAGA - C/ PINTADA 12",
        ])
    },
    "52": {
        "name": "Melilla",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4078": "POLICIA - SOLICITUD ASILO",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA MELILLA - C/ GENERAL POLAVIEJA 2",
        ])
    },
    "30": {
        "name": "Murcia",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4078": "POLICIA - SOLICITUD ASILO",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA CARTAGENA - C/ REAL 10",
            "CNP - COMISARIA LORCA - AV. EUROPA 4",
            "CNP - COMISARIA MOLINA DE SEGURA - AV. CONSTITUCION 56",
            "CNP - COMISARIA MURCIA CENTRO - C/ ACISCLO DIAZ 8",
            "CNP - COMISARIA YECLA - C/ ANTONIO NAVARRO 48",
        ])
    },
    "31": {
        "name": "Navarra",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA PAMPLONA - C/ YANGUAS Y MIRANDA 6",
            "CNP - COMISARIA TUDELA - AV. ZARAGOZA 38",
        ])
    },
    "32": {
        "name": "Ourense",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA OURENSE - C/ CORONEL CEANO 7",
        ])
    },
    "34": {
        "name": "Palencia",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA PALENCIA - C/ GENERAL AMOR 1",
        ])
    },
    "36": {
        "name": "Pontevedra",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA PONTEVEDRA - C/ JOAQUIN COSTA 5",
            "CNP - COMISARIA VILAGARCIA DE AROUSA - C/ TORO 1",
            "CNP - COMISARIA VIGO CENTRO - C/ JOAQUIN YAÑEZ 6",
            "CNP - COMISARIA VIGO COIA - C/ BARCELONA 11",
        ])
    },
    "38": {
        "name": "S.C. Tenerife",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4094": "POLICIA - BREXIT (Tarjeta Ciudadanos Británicos)",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - GOMERA (SAN SEBASTIAN) - AV. FRED OLSEN S/N",
            "CNP - ICOD DE LOS VINOS - C/ OBISPO PEREZ CACERES 1",
            "CNP - LA LAGUNA - C/ SAN AGUSTIN 30",
            "CNP - PLAYA DE LAS AMERICAS - AV. DE LOS PUEBLOS 2",
            "CNP - PUERTO DE LA CRUZ / LOS REALEJOS - AV. DEL CAMPO Y LLARENA 3",
            "OUE SANTA CRUZ DE TENERIFE - C/ LA MARINA 20",
        ])
    },
    "37": {
        "name": "Salamanca",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA SALAMANCA - C/ JULIAN SANCHEZ EL CHARRO 2",
        ])
    },
    "40": {
        "name": "Segovia",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA SEGOVIA - C/ JOSE ZORRILLA 26",
        ])
    },
    "41": {
        "name": "Sevilla",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4038": "POLICIA - CERTIFICADOS Y ASIGNACION NIE (Comunitarios)",
            "4049": "POLICIA - CERTIFICADOS DE RESIDENCIA/NO RESIDENCIA",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4078": "POLICIA - SOLICITUD ASILO",
            "4096": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA ALCALA DE GUADAIRA - C/ GARCIA MORATO 2",
            "CNP - COMISARIA DOS HERMANAS - C/ SANTA TERESA DE JOURNET 2",
            "CNP - COMISARIA SEVILLA CENTRO - C/ BUEN AIRE 1",
            "CNP - COMISARIA SEVILLA NORTE - C/ RESOLANA 18",
            "CNP - COMISARIA SEVILLA SUR - AV. KANSAS CITY S/N",
            "CNP - COMISARIA UTRERA - C/ JOSE ARPA 7",
        ])
    },
    "42": {
        "name": "Soria",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA SORIA - C/ NUMANCIA 1",
        ])
    },
    "43": {
        "name": "Tarragona",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA EL VENDRELL - AV. SANTA OLIVA 6",
            "CNP - COMISARIA REUS - C/ SANT LLORENÇ 18",
            "CNP - COMISARIA TARRAGONA - C/ CAMI DE LA PEDRERA 2",
            "CNP - COMISARIA TORTOSA - C/ MONTCADA 6",
        ])
    },
    "44": {
        "name": "Teruel",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA TERUEL - C/ NUEVA 6",
        ])
    },
    "45": {
        "name": "Toledo",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA TALAVERA DE LA REINA - AV. GREGORIO RUIZ 2",
            "CNP - COMISARIA TOLEDO - C/ BELEN 5",
        ])
    },
    "46": {
        "name": "Valencia",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4094": "POLICIA - BREXIT (Tarjeta Ciudadanos Británicos)",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4038": "POLICIA - CERTIFICADOS Y ASIGNACION NIE (Comunitarios)",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4078": "POLICIA - SOLICITUD ASILO",
            "4096": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA ALZIRA - AV. PAIS VALENCIA 1",
            "CNP - COMISARIA BURJASSOT - C/ ACADEMIA 8",
            "CNP - COMISARIA GANDIA - C/ MAJOR 67",
            "CNP - COMISARIA SAGUNTO - C/ CAMÍ REAL 177",
            "CNP - COMISARIA TORRENT - C/ PICANYA 18",
            "CNP - COMISARIA VALENCIA CENTRO - C/ LEPANTO 5",
            "CNP - COMISARIA VALENCIA PATRAIX - C/ BOTANICO CAVANILLES 37",
            "CNP - COMISARIA VALENCIA PUERTO - AV. DEL PORT 56",
        ])
    },
    "47": {
        "name": "Valladolid",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA VALLADOLID CENTRO - C/ DOCTOR CAZALLA 4",
            "CNP - COMISARIA VALLADOLID SUR - C/ PANADEROS 1",
        ])
    },
    "7": {
        "name": "Illes Balears",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4094": "POLICIA - BREXIT (Tarjeta Ciudadanos Británicos)",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA IBIZA - C/ VICENTE CUERVO 3",
            "CNP - COMISARIA INCA - C/ PAU 2",
            "CNP - COMISARIA MANACOR - C/ SOLEDAD 3",
            "CNP - COMISARIA MENORCA (MAHON) - AV. VIVES LLULL S/N",
            "CNP - COMISARIA PALMA CENTRO - C/ RUIZ DE ALDA 8",
            "CNP - COMISARIA PALMA SON CASTELLO - C/ GREMIO HERRERO 3",
        ])
    },
    "15": {
        "name": "A Coruña",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA A CORUÑA - C/ RAMON Y CAJAL 4",
            "CNP - COMISARIA FERROL - C/ DOLORES 1",
            "CNP - COMISARIA SANTIAGO DE COMPOSTELA - C/ HORREO 4",
        ])
    },
    "49": {
        "name": "Zamora",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA ZAMORA - C/ BENAVENTE 2",
        ])
    },
    "50": {
        "name": "Zaragoza",
        "tramites": _s({
            "4010": "POLICIA - ASIGNACIÓN DE NIE",
            "4036": "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4031": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4038": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
        }),
        "oficinas": _sl([
            "CNP - COMISARIA CALATAYUD - C/ ARCADAS 2",
            "CNP - COMISARIA ZARAGOZA CENTRO - C/ DOMINGO MIRAL 3",
            "CNP - COMISARIA ZARAGOZA NORTE - AV. ALCALDE CABALLERO 2",
            "CNP - COMISARIA ZARAGOZA SUR - C/ GOYA 20",
        ])
    },
}
