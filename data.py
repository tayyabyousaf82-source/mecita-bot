# ═══════════════════════════════════════════════════════════════
# data.py — Complete Spain ICP Cita Previa Data
# All 52 Provincias with their Tramites and Oficinas
# Source: icp.administracionelectronica.gob.es (official)
# ═══════════════════════════════════════════════════════════════

PROVINCIA_DATA = {

    # ── MADRID ──────────────────────────────────────────────────
    "28": {
        "name": "Madrid",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4096": "POLICIA - CERTIFICADOS Y ASIGNACION NIE (Comunitarios)",
            "4079": "POLICIA - CERTIFICADOS Y ASIGNACION NIE (No Comunitarios)",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4049": "POLICIA - CERTIFICADOS DE RESIDENCIA/NO RESIDENCIA/CONCORDANCIA",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4094": "POLICIA - BREXIT (Tarjeta Ciudadanos Británicos)",
            "4078": "POLICIA - SOLICITUD ASILO (Primera Cita)",
            "4047": "POLICIA - EXPEDICIÓN TARJETAS (Dirección General Migraciones)",
            "4080": "POLICIA - INFORMACION TRAMITES COMISARIA",
        },
        "oficinas": [
            "COMISARIA MORATALAZ - C/ CORREGIDOR DIEGO DE VALDERRABANO 13",
            "COMISARIA FUENCARRAL - C/ PLASENCIA 3",
            "COMISARIA CARABANCHEL - C/ GENERAL RICARDOS 110",
            "COMISARIA VALLECAS - C/ SIERRA DE ALQUIFE 5",
            "COMISARIA LATINA - C/ AVIACION ESPAÑOLA S/N",
            "COMISARIA TETUAN - C/ RAMON Y CAJAL 9",
            "COMISARIA USERA - C/ PRADILLO 40",
            "COMISARIA RETIRO - C/ DOCTOR ESQUERDO 26",
            "COMISARIA ARGANZUELA - C/ EMBAJADORES 116",
            "COMISARIA HORTALEZA - C/ HERACLITO 2",
            "COMISARIA ALCALA DE HENARES - AV. JUAN CARLOS I 8",
            "COMISARIA ALCORCON - C/ MOSTOLES 8",
            "COMISARIA GETAFE - AV. BLAS TELLO 3",
            "COMISARIA LEGANES - C/ OBISPADO 1",
            "COMISARIA MOSTOLES - C/ NEVERO 2",
            "COMISARIA PARLA - C/ ARCO 2",
            "COMISARIA TORREJON DE ARDOZ - C/ MAYOR 70",
            "COMISARIA ALCOBENDAS - C/ JUAN RAMON JIMENEZ 4",
            "COMISARIA COSLADA - C/ HENARES 12",
            "COMISARIA POZUELO DE ALARCON - C/ AGUILAS 3",
            "OFICINA DE ASILO - PRADILLO 40 (Solo Asilo)",
        ]
    },

    # ── BARCELONA ────────────────────────────────────────────────
    "8": {
        "name": "Barcelona",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4096": "POLICIA - CERTIFICADOS Y ASIGNACION NIE (Comunitarios)",
            "4079": "POLICIA - CERTIFICADOS Y ASIGNACION NIE (No Comunitarios)",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4049": "POLICIA - CERTIFICADOS DE RESIDENCIA/NO RESIDENCIA",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4094": "POLICIA - BREXIT (Tarjeta Ciudadanos Británicos)",
            "4078": "POLICIA - SOLICITUD ASILO",
            "4047": "POLICIA - EXPEDICIÓN TARJETAS (Dir. Gral. Migraciones)",
        },
        "oficinas": [
            "CNP - RAMBLA GUIPUSCOA 74 (Barcelona)",
            "CNP MALLORCA-GRANADOS - MALLORCA 213 (Barcelona)",
            "CNP - COMISARIA BADALONA - AVDA. DELS VENTS 9",
            "CNP - COMISARIA CASTELLDEFELS - PLAÇA DE L'ESPERANTO 4",
            "CNP - COMISARIA CERDANYOLA DEL VALLES - VERGE DE LES FEIXES 4",
            "CNP - COMISARIA CORNELLA DE LLOBREGAT - AV. SANT ILDEFONS S/N",
            "CNP - COMISARIA EL PRAT DE LLOBREGAT - CENTRE 4",
            "CNP - COMISARIA GRANOLLERS - RICOMA 65",
            "CNP - COMISARIA L'HOSPITALET DE LLOBREGAT - Rbla. Just Oliveres 43",
            "CNP - COMISARIA IGUALADA - PRAT DE LA RIBA 13",
            "CNP - COMISARIA MANRESA - SOLER I MARCH 5",
            "CNP - COMISARIA MATARO - AV. GATASSA 15",
            "CNP - COMISARIA MONTCADA I REIXAC - MAJOR 38",
            "CNP - COMISARIA RIPOLLET - TAMARIT 78",
            "CNP - COMISARIA RUBI - TERRASSA 16",
            "CNP - COMISARIA SABADELL - BATLLEVELL 115",
            "CNP - COMISARIA SANTA COLOMA DE GRAMENET - IRLANDA 67",
            "CNP - COMISARIA SANT ADRIA DEL BESOS - AV. JOAN XXIII 2",
            "CNP - COMISARIA SANT BOI DE LLOBREGAT - RIERA BASTE 43",
            "CNP - COMISARIA SANT CUGAT DEL VALLES - VALLES 1",
            "CNP - COMISARIA SANT FELIU DE LLOBREGAT - CARRERETES 9",
            "CNP - COMISARIA TERRASSA - BALDRICH 13",
            "CNP - COMISARIA VIC - BISBE MORGADES 4",
            "CNP - COMISARIA VILADECANS - AVDA. BALLESTER 2",
            "CNP - COMISARIA VILAFRANCA DEL PENEDES - Avinguda Ronda del Mar 109",
            "CNP - COMISARIA VILANOVA I LA GELTRU - VAPOR 19",
        ]
    },

    # ── VALENCIA ─────────────────────────────────────────────────
    "46": {
        "name": "Valencia",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4096": "POLICIA - CERTIFICADOS Y ASIGNACION NIE (Comunitarios)",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4094": "POLICIA - BREXIT",
            "4078": "POLICIA - SOLICITUD ASILO",
        },
        "oficinas": [
            "CNP - COMISARIA VALENCIA CENTRO - C/ LEPANTO 5",
            "CNP - COMISARIA VALENCIA PATRAIX - C/ BOTANICO CAVANILLES 37",
            "CNP - COMISARIA VALENCIA PUERTO - AV. DEL PORT 56",
            "CNP - COMISARIA TORRENT - C/ PICANYA 18",
            "CNP - COMISARIA GANDIA - C/ MAJOR 67",
            "CNP - COMISARIA ALZIRA - AV. PAIS VALENCIA 1",
            "CNP - COMISARIA SAGUNTO - C/ CAMÍ REAL 177",
            "CNP - COMISARIA BURJASSOT - C/ ACADEMIA 8",
        ]
    },

    # ── SEVILLA ──────────────────────────────────────────────────
    "41": {
        "name": "Sevilla",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4096": "POLICIA - CERTIFICADOS Y ASIGNACION NIE (Comunitarios)",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4049": "POLICIA - CERTIFICADOS DE RESIDENCIA/NO RESIDENCIA",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4078": "POLICIA - SOLICITUD ASILO",
        },
        "oficinas": [
            "CNP - COMISARIA SEVILLA CENTRO - C/ BUEN AIRE 1",
            "CNP - COMISARIA SEVILLA SUR - AV. KANSAS CITY S/N",
            "CNP - COMISARIA SEVILLA NORTE - C/ RESOLANA 18",
            "CNP - COMISARIA ALCALA DE GUADAIRA - C/ GARCIA MORATO 2",
            "CNP - COMISARIA DOS HERMANAS - C/ SANTA TERESA DE JOURNET 2",
            "CNP - COMISARIA UTRERA - C/ JOSE ARPA 7",
        ]
    },

    # ── MÁLAGA ───────────────────────────────────────────────────
    "29": {
        "name": "Málaga",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4096": "POLICIA - CERTIFICADOS Y ASIGNACION NIE (Comunitarios)",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4094": "POLICIA - BREXIT",
            "4078": "POLICIA - SOLICITUD ASILO",
        },
        "oficinas": [
            "CNP - COMISARIA MALAGA CENTRO - C/ MAURICIO MORO PARETO 1",
            "CNP - COMISARIA MARBELLA - C/ JACINTO BENAVENTE S/N",
            "CNP - COMISARIA FUENGIROLA - C/ CAPITAN 5",
            "CNP - COMISARIA TORREMOLINOS - AV. PALMA DE MALLORCA 12",
            "CNP - COMISARIA VELEZ-MALAGA - C/ PINTADA 12",
            "CNP - COMISARIA ANTEQUERA - C/ INFANTE DON FERNANDO 40",
            "CNP - COMISARIA ESTEPONA - AV. ESPAÑA 140",
            "CNP - COMISARIA COIN - C/ REAL 80",
        ]
    },

    # ── ALICANTE ─────────────────────────────────────────────────
    "3": {
        "name": "Alicante",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4096": "POLICIA - CERTIFICADOS Y ASIGNACION NIE (Comunitarios)",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4094": "POLICIA - BREXIT",
        },
        "oficinas": [
            "CNP - COMISARIA ALICANTE CENTRO - C/ MEDICO PASCUAL PEREZ 37",
            "CNP - COMISARIA BENIDORM - C/ LLUIS SITGES 3",
            "CNP - COMISARIA TORREVIEJA - AV. DR. GREGORIO MARAÑON 22",
            "CNP - COMISARIA ELCHE - C/ CORREGIDOR JOAQUIN MENDUIÑA 30",
            "CNP - COMISARIA ORIHUELA - C/ JOSE ANTONIO 2",
            "CNP - COMISARIA DENIA - C/ DIANA 14",
            "CNP - COMISARIA ELDA - C/ OSCAR ESPLA 15",
            "CNP - COMISARIA VILLENA - AV. DE LA CONSTITUCION 50",
        ]
    },

    # ── ILLES BALEARS ────────────────────────────────────────────
    "7": {
        "name": "Illes Balears",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4094": "POLICIA - BREXIT",
        },
        "oficinas": [
            "CNP - COMISARIA PALMA CENTRO - C/ RUIZ DE ALDA 8",
            "CNP - COMISARIA PALMA SON CASTELLO - C/ GREMIO HERRERO 3",
            "CNP - COMISARIA IBIZA - C/ VICENTE CUERVO 3",
            "CNP - COMISARIA MANACOR - C/ SOLEDAD 3",
            "CNP - COMISARIA INCA - C/ PAU 2",
            "CNP - COMISARIA MENORCA (MAHON) - AV. VIVES LLULL S/N",
        ]
    },

    # ── LAS PALMAS ───────────────────────────────────────────────
    "35": {
        "name": "Las Palmas",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4094": "POLICIA - BREXIT",
        },
        "oficinas": [
            "CNP - COMISARIA LAS PALMAS CENTRO - C/ BUENOS AIRES 4",
            "CNP - COMISARIA TELDE - C/ LEON Y CASTILLO 73",
            "CNP - COMISARIA MASPALOMAS - AV. TIRAJANA 14",
            "CNP - COMISARIA LANZAROTE (ARRECIFE) - C/ JOSE ANTONIO 36",
            "CNP - COMISARIA FUERTEVENTURA (PUERTO DEL ROSARIO) - AV. PRIMERO DE MAYO 39",
        ]
    },

    # ── S.C. TENERIFE ────────────────────────────────────────────
    "38": {
        "name": "S.C. Tenerife",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4094": "POLICIA - BREXIT",
        },
        "oficinas": [
            "OUE SANTA CRUZ DE TENERIFE - C/ LA MARINA 20",
            "CNP - PLAYA DE LAS AMERICAS - AV. DE LOS PUEBLOS 2",
            "CNP - PUERTO DE LA CRUZ / LOS REALEJOS - AV. DEL CAMPO Y LLARENA 3",
            "CNP - LA LAGUNA - C/ SAN AGUSTIN 30",
            "CNP - ICOD DE LOS VINOS - C/ OBISPO PEREZ CACERES 1",
            "CNP - GOMERA (SAN SEBASTIAN) - AV. FRED OLSEN S/N",
        ]
    },

    # ── MURCIA ───────────────────────────────────────────────────
    "30": {
        "name": "Murcia",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4096": "POLICIA - CERTIFICADOS Y ASIGNACION NIE (Comunitarios)",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4078": "POLICIA - SOLICITUD ASILO",
        },
        "oficinas": [
            "CNP - COMISARIA MURCIA CENTRO - C/ ACISCLO DIAZ 8",
            "CNP - COMISARIA CARTAGENA - C/ REAL 10",
            "CNP - COMISARIA LORCA - AV. EUROPA 4",
            "CNP - COMISARIA MOLINA DE SEGURA - AV. CONSTITUCION 56",
            "CNP - COMISARIA YECLA - C/ ANTONIO NAVARRO 48",
        ]
    },

    # ── ZARAGOZA ─────────────────────────────────────────────────
    "50": {
        "name": "Zaragoza",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4096": "POLICIA - CERTIFICADOS Y ASIGNACION NIE (Comunitarios)",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA ZARAGOZA CENTRO - C/ DOMINGO MIRAL 3",
            "CNP - COMISARIA ZARAGOZA SUR - C/ GOYA 20",
            "CNP - COMISARIA ZARAGOZA NORTE - AV. ALCALDE CABALLERO 2",
            "CNP - COMISARIA CALATAYUD - C/ ARCADAS 2",
        ]
    },

    # ── GRANADA ──────────────────────────────────────────────────
    "18": {
        "name": "Granada",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA GRANADA CENTRO - C/ DUQUESA 21",
            "CNP - COMISARIA MOTRIL - C/ AVENIDA 1",
            "CNP - COMISARIA BAZA - C/ PEDRO POVEDA 2",
        ]
    },

    # ── BIZKAIA ──────────────────────────────────────────────────
    "48": {
        "name": "Bizkaia",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA BILBAO CENTRO - C/ LUIS BRIÑAS 14",
            "CNP - COMISARIA BARAKALDO - C/ BUEN PASTOR 1",
            "CNP - COMISARIA GETXO - AV. LOS CHOPOS 2",
            "CNP - COMISARIA BASAURI - C/ ARIZ 30",
            "CNP - COMISARIA DURANGO - C/ KURUTZIAGA 28",
        ]
    },

    # ── CÓRDOBA ──────────────────────────────────────────────────
    "14": {
        "name": "Córdoba",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA CORDOBA CENTRO - C/ POETA JUAN BERNIER 2",
            "CNP - COMISARIA LUCENA - C/ MARQUES DE COMARES 23",
            "CNP - COMISARIA POZOBLANCO - C/ DOCTOR MANUEL COBOS 1",
        ]
    },

    # ── CÁDIZ ────────────────────────────────────────────────────
    "11": {
        "name": "Cádiz",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
            "4094": "POLICIA - BREXIT",
        },
        "oficinas": [
            "CNP - COMISARIA CADIZ - C/ ANA DE VIYA 1",
            "CNP - COMISARIA ALGECIRAS - C/ JOSE ANTONIO 5",
            "CNP - COMISARIA JEREZ DE LA FRONTERA - C/ SEVILLA 1",
            "CNP - COMISARIA LA LINEA DE LA CONCEPCION - C/ DUQUE DE TETUÁN 17",
            "CNP - COMISARIA SANLUCAR DE BARRAMEDA - C/ BARRAMEDA 2",
            "CNP - COMISARIA EL PUERTO DE SANTA MARIA - C/ LUIS DE REQUESENS 3",
        ]
    },

    # ── ASTURIAS ─────────────────────────────────────────────────
    "33": {
        "name": "Asturias",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA OVIEDO - C/ GENERAL ELORZA 32",
            "CNP - COMISARIA GIJON - C/ RODRIGUEZ SAN PEDRO 2",
            "CNP - COMISARIA AVILES - C/ LA MURALLA 4",
            "CNP - COMISARIA LANGREO - C/ LLARANES 7",
        ]
    },

    # ── A CORUÑA ─────────────────────────────────────────────────
    "15": {
        "name": "A Coruña",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA A CORUÑA - C/ RAMON Y CAJAL 4",
            "CNP - COMISARIA SANTIAGO DE COMPOSTELA - C/ HORREO 4",
            "CNP - COMISARIA FERROL - C/ DOLORES 1",
        ]
    },

    # ── PONTEVEDRA ───────────────────────────────────────────────
        "36": {
        "name": "Pontevedra",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA VIGO CENTRO - C/ JOAQUIN YAÑEZ 6",
            "CNP - COMISARIA VIGO COIA - C/ BARCELONA 11",
            "CNP - COMISARIA PONTEVEDRA - C/ JOAQUIN COSTA 5",
            "CNP - COMISARIA VILAGARCIA DE AROUSA - C/ TORO 1",
        ]
    },

    # ── NAVARRA ──────────────────────────────────────────────────
    "31": {
        "name": "Navarra",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA PAMPLONA - C/ YANGUAS Y MIRANDA 6",
            "CNP - COMISARIA TUDELA - AV. ZARAGOZA 38",
        ]
    },

    # ── ALMERÍA ──────────────────────────────────────────────────
    "4": {
        "name": "Almería",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA ALMERIA CENTRO - C/ CASTRO 4",
            "CNP - COMISARIA EL EJIDO - C/ BENITAGLA 4",
            "CNP - COMISARIA ROQUETAS DE MAR - C/ JOSE MANZANO 2",
        ]
    },

      # ── HUELVA ───────────────────────────────────────────────────
    "21": {
        "name": "Huelva",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA HUELVA - C/ PLUS ULTRA 4",
            "CNP - COMISARIA ALMONTE - C/ REAL 2",
            "CNP - COMISARIA LEPE - C/ CERVANTES 2",
        ]
    },

    # ── JAÉN ─────────────────────────────────────────────────────
    "23": {
        "name": "Jaén",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA JAEN - C/ ARQUITECTO BERGES 14",
            "CNP - COMISARIA LINARES - C/ CORREDERA DE SAN MARCOS 5",
            "CNP - COMISARIA UBEDA - C/ HORNO CONTADOR 2",
            "CNP - COMISARIA ANDUJAR - C/ MUÑOZ GRANDE 7",
        ]
    },

    # ── TARRAGONA ────────────────────────────────────────────────
    "43": {
        "name": "Tarragona",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA TARRAGONA - C/ CAMI DE LA PEDRERA 2",
            "CNP - COMISARIA REUS - C/ SANT LLORENÇ 18",
            "CNP - COMISARIA TORTOSA - C/ MONTCADA 6",
            "CNP - COMISARIA EL VENDRELL - AV. SANTA OLIVA 6",
        ]
    },

    # ── GIRONA ───────────────────────────────────────────────────
    "17": {
        "name": "Girona",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA GIRONA - C/ BACIÀ 4",
            "CNP - COMISARIA BLANES - C/ ESPLANADA DEL PORT 1",
            "CNP - COMISARIA FIGUERES - C/ AIRÀ 10",
            "CNP - COMISARIA OLOT - C/ SANT ROCA 22",
        ]
    },

    # ── LLEIDA ───────────────────────────────────────────────────
    "25": {
        "name": "Lleida",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA LLEIDA - C/ DOCTOR COMBELLES 2",
        ]
    },

      # ── GIPUZKOA ─────────────────────────────────────────────────
    "20": {
        "name": "Gipuzkoa",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "4037": "POLICIA - CARTA DE INVITACIÓN",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA SAN SEBASTIAN - C/ EASO 8",
            "CNP - COMISARIA IRUN - AV. IPARRALDE 34",
        ]
    },

    # ── ÁLAVA ────────────────────────────────────────────────────
    "1": {
        "name": "Álava",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA VITORIA-GASTEIZ - C/ JOSE LUIS IÑARRA 4",
        ]
    },

    # ── ALBACETE ─────────────────────────────────────────────────
    "2": {
        "name": "Albacete",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA ALBACETE - C/ TEODORO CAMINO 5",
            "CNP - COMISARIA HELLIN - C/ CASTILLA LA MANCHA 2",
        ]
    },

    # ── BADAJOZ ──────────────────────────────────────────────────
    "6": {
        "name": "Badajoz",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA BADAJOZ - C/ RAFAEL LUCENQUI 5",
            "CNP - COMISARIA MERIDA - C/ SAGASTA 15",
            "CNP - COMISARIA DON BENITO - AV. VILLANUEVA 2",
        ]
    },

    # ── BURGOS ───────────────────────────────────────────────────
    "9": {
        "name": "Burgos",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA BURGOS - C/ SANZ PASTOR 2",
            "CNP - COMISARIA MIRANDA DE EBRO - AV. NAVARRA 24",
        ]
    },

      # ── CÁCERES ──────────────────────────────────────────────────
    "10": {
        "name": "Cáceres",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA CACERES - C/ MONTESINOS 2",
            "CNP - COMISARIA PLASENCIA - C/ VIDRIERAS 7",
        ]
    },

    # ── CANTABRIA ────────────────────────────────────────────────
    "39": {
        "name": "Cantabria",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA SANTANDER - C/ VARGAS 51",
            "CNP - COMISARIA TORRELAVEGA - C/ INDUSTRIA 3",
        ]
    },

    # ── CASTELLÓN ────────────────────────────────────────────────
    "12": {
        "name": "Castellón",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4038": "POLICIA - CERTIFICADO DE REGISTRO CIUDADANO UE",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA CASTELLON DE LA PLANA - C/ ORFEBRES 6",
            "CNP - COMISARIA VILA-REAL - C/ MAYOR 78",
            "CNP - COMISARIA VINAROS - C/ SANT GREGORI 2",
        ]
    },

    # ── CEUTA ────────────────────────────────────────────────────
    "51": {
        "name": "Ceuta",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4078": "POLICIA - SOLICITUD ASILO",
        },
        "oficinas": [
            "CNP - COMISARIA CEUTA - C/ RECINTO SUR S/N",
        ]
    },

    # ── CIUDAD REAL ──────────────────────────────────────────────
    "13": {
        "name": "Ciudad Real",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA CIUDAD REAL - C/ ALARCOS 20",
            "CNP - COMISARIA PUERTOLLANO - C/ JESUS FERNANDEZ MALO 1",
        ]
    },

      # ── CUENCA ───────────────────────────────────────────────────
    "16": {
        "name": "Cuenca",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
        },
        "oficinas": [
            "CNP - COMISARIA CUENCA - C/ FERMIN CABALLERO 8",
            "CNP - COMISARIA TARANCÓN - C/ GOYA 4",
        ]
    },

    # ── GUADALAJARA ──────────────────────────────────────────────
    "19": {
        "name": "Guadalajara",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
        },
        "oficinas": [
            "CNP - COMISARIA GUADALAJARA - C/ ARAGON 4",
            "CNP - COMISARIA AZUQUECA DE HENARES - AV. CONSTITUCION 17",
        ]
    },

    # ── HUESCA ───────────────────────────────────────────────────
    "22": {
        "name": "Huesca",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
        },
        "oficinas": [
            "CNP - COMISARIA HUESCA - C/ RICARDO DEL ARCO 6",
            "CNP - COMISARIA MONZON - C/ SANTA BARBARA 11",
            "CNP - COMISARIA FRAGA - C/ PIRINEOS 2",
        ]
    },

    # ── LA RIOJA ─────────────────────────────────────────────────
    "26": {
        "name": "La Rioja",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA LOGROÑO - C/ PORTALES 3",
            "CNP - COMISARIA CALAHORRA - C/ ERCILLA 4",
        ]
    },

    # ── LEÓN ─────────────────────────────────────────────────────
    "24": {
        "name": "León",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA LEON - C/ VILLA BENAVENTE 8",
            "CNP - COMISARIA PONFERRADA - C/ ORTEGA Y GASSET 1",
        ]
    },

      # ── LUGO ─────────────────────────────────────────────────────
    "27": {
        "name": "Lugo",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
        },
        "oficinas": [
            "CNP - COMISARIA LUGO - C/ CAMPO CASTELO 7",
        ]
    },

    # ── MELILLA ──────────────────────────────────────────────────
    "52": {
        "name": "Melilla",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "4078": "POLICIA - SOLICITUD ASILO",
        },
        "oficinas": [
            "CNP - COMISARIA MELILLA - C/ GENERAL POLAVIEJA 2",
        ]
    },

    # ── OURENSE ──────────────────────────────────────────────────
    "32": {
        "name": "Ourense",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
        },
        "oficinas": [
            "CNP - COMISARIA OURENSE - C/ CORONEL CEANO 7",
        ]
    },

    # ── PALENCIA ─────────────────────────────────────────────────
    "34": {
        "name": "Palencia",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
        },
        "oficinas": [
            "CNP - COMISARIA PALENCIA - C/ GENERAL AMOR 1",
        ]
    },

    # ── SALAMANCA ────────────────────────────────────────────────
    "37": {
        "name": "Salamanca",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA SALAMANCA - C/ JULIAN SANCHEZ EL CHARRO 2",
        ]
    },

    # ── SEGOVIA ──────────────────────────────────────────────────
    "40": {
        "name": "Segovia",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
        },
        "oficinas": [
            "CNP - COMISARIA SEGOVIA - C/ JOSE ZORRILLA 26",
        ]
    },

      # ── SORIA ────────────────────────────────────────────────────
    "42": {
        "name": "Soria",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
        },
        "oficinas": [
            "CNP - COMISARIA SORIA - C/ NUMANCIA 1",
        ]
    },

    # ── TERUEL ───────────────────────────────────────────────────
    "44": {
        "name": "Teruel",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
        },
        "oficinas": [
            "CNP - COMISARIA TERUEL - C/ NUEVA 6",
        ]
    },

    # ── TOLEDO ───────────────────────────────────────────────────
    "45": {
        "name": "Toledo",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA TOLEDO - C/ BELEN 5",
            "CNP - COMISARIA TALAVERA DE LA REINA - AV. GREGORIO RUIZ 2",
        ]
    },

    # ── VALLADOLID ───────────────────────────────────────────────
    "47": {
        "name": "Valladolid",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
            "20":   "POLICIA - AUTORIZACIÓN DE REGRESO",
        },
        "oficinas": [
            "CNP - COMISARIA VALLADOLID CENTRO - C/ DOCTOR CAZALLA 4",
            "CNP - COMISARIA VALLADOLID SUR - C/ PANADEROS 1",
        ]
    },

    # ── ÁVILA ────────────────────────────────────────────────────
    "5": {
        "name": "Ávila",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
        },
        "oficinas": [
            "CNP - COMISARIA AVILA - C/ DUQUE DE ALBA 2",
        ]
    },

      # ── ZAMORA ───────────────────────────────────────────────────
    "49": {
        "name": "Zamora",
        "tramites": {
            "4010": "POLICIA - TOMA DE HUELLAS (Expedición/Renovación TIE)",
            "4036": "POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD EXTRANJERO (TIE)",
            "4031": "POLICIA - ASIGNACIÓN DE NIE",
        },
        "oficinas": [
            "CNP - COMISARIA ZAMORA - C/ BENAVENTE 2",
        ]
    },
}
