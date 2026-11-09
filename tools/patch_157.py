#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build 157 de Inazuma Draft - Carrera de 22 clubes.

Aplica sobre index.html:
  * 22 clubes en Carrera (dos divisiones de 11) con Royal Academy Redux en Primera.
  * Onces canonicos de 11 jugadores por club; el resto del banquillo va a agentes libres.
  * Royal Academy Redux con los cinco originales de Rogue (King 20, Samford 30, Bargie 21535,
    Stonewall 21541, Spark 21538) + seis jugadores IE1/IE2 (3 DEF, 1 MED, 2 DEL).
  * Imperial cubre los puestos de King y Samford con dos jugadores distintos.
  * Migracion unica de guardados: plantillas a 11, calendario y resultados intactos.
El script es idempotente: si el archivo ya esta parcheado, no cambia nada.
"""
import json
import re
import sys

RUTA = "index.html"


# ---------------------------------------------------------------- utilidades
def leer():
    with open(RUTA, encoding="utf-8") as f:
        return f.read()


def escribir(txt):
    with open(RUTA, "w", encoding="utf-8") as f:
        f.write(txt)


def rep(txt, viejo, nuevo, veces=1, etiqueta=""):
    n = txt.count(viejo)
    if n != veces:
        raise SystemExit("ERROR [%s]: esperaba %d coincidencias y hay %d\n%s" %
                         (etiqueta, veces, n, viejo[:160]))
    return txt.replace(viejo, nuevo)


def bloque_balanceado(txt, inicio):
    """Devuelve el bloque {...} o [...] que empieza en/tras `inicio`."""
    i = inicio
    while txt[i] not in "[{":
        i += 1
    d = 0
    ins = None
    j = i
    while j < len(txt):
        ch = txt[j]
        if ins:
            if ch == "\\":
                j += 2
                continue
            if ch == ins:
                ins = None
        else:
            if ch in "\"'`":
                ins = ch
            elif ch in "[{(":
                d += 1
            elif ch in "]})":
                d -= 1
                if d == 0:
                    return txt[i:j + 1], i, j + 1
        j += 1
    raise SystemExit("bloque sin cerrar")


def js_a_json(bloque):
    """El juego escribe \\xNN y \\' dentro de literales JS: los pasamos a JSON."""
    bloque = re.sub(r"\\x([0-9A-Fa-f]{2})", lambda m: "\\u00" + m.group(1).lower(), bloque)
    bloque = bloque.replace("\\'", "'")
    return json.loads(bloque)


def reemplazar_once(txt, ancla, jugadores):
    """Sustituye el array "once" del club cuyo objeto contiene `ancla`."""
    p = txt.index(ancla)
    q = txt.index('"once":', p)
    bloque, a, b = bloque_balanceado(txt, q + len('"once":'))
    nuevo = json.dumps(jugadores, ensure_ascii=True, separators=(",", ":"))
    return txt[:a] + nuevo + txt[b:]


# ---------------------------------------------------------------- jugadores
# Registros base tomados de los equipos originales del juego.
J = {
    "king": {"n": "Joseph King", "c": "King", "num": 1, "pos": "POR", "nat": "POR", "cara": "Genda_Koujirou",
             "tec": "Escudo de fuerza total", "reg": "Ultralunar", "rob": "Mano de pingüinos",
             "tir": "Remate halcón", "ata": "Parada en pirueta", "med": 81,
             "rat": {"tir": 86, "reg": 74, "rob": 88, "ata": 88, "vel": 66}},
    "samford": {"n": "David Samford", "c": "Samford", "num": 9, "pos": "DEL", "nat": "DEL", "cara": "Sakuma_Jirou",
                "tec": "Pingüino emperador n.º 2", "reg": "Golpe ametralladora", "rob": "Jungla profunda",
                "tir": "Pingüino emperador n.º 2", "ata": "Muro de hierro", "med": 81,
                "rat": {"tir": 83, "reg": 86, "rob": 75, "ata": 75, "vel": 79}},
    "bargie": {"n": "Argie Bargie", "c": "Bargie", "num": 2, "pos": "DEF", "nat": "DEF", "cara": "n141_royalredux_1",
               "tec": "Barrido defensivo", "reg": "Regate del pingüino", "rob": "Barrido defensivo",
               "tir": "Chut imperial", "ata": "Muro de acero", "med": 87,
               "rat": {"tir": 84, "reg": 80, "rob": 91, "ata": 74, "vel": 82}},
    "stonewall": {"n": "Caleb Stonewall", "c": "Stonewall", "num": 6, "pos": "MED", "nat": "MED",
                  "cara": "n141_royalredux_2", "tec": "Cortina de hierro", "reg": "Pase imperial",
                  "rob": "Cortina de hierro", "tir": "Cañón real", "ata": "Muro de acero", "med": 88,
                  "rat": {"tir": 88, "reg": 87, "rob": 90, "ata": 72, "vel": 84}},
    "spark": {"n": "Jonah Spark", "c": "Spark", "num": 7, "pos": "MED", "nat": "MED",
              "cara": "n141_royalredux_3", "tec": "Chispa real", "reg": "Pase eléctrico",
              "rob": "Robo relámpago", "tir": "Disparo relámpago", "ata": "Descarga", "med": 84,
              "rat": {"tir": 82, "reg": 86, "rob": 80, "ata": 71, "vel": 85}},
    "cain": {"n": "Cain", "c": "Cain", "num": 3, "pos": "DEF", "nat": "DEF", "cara": "umbra_Cain",
             "tec": "Sombra de Orión", "reg": "Remate oscuro", "rob": "Sombra de Orión",
             "tir": "Disparo de las tinieblas", "ata": "Muro sombrío", "med": 86,
             "rat": {"tir": 83, "reg": 79, "rob": 90, "ata": 73, "vel": 81}},
    "dwight": {"n": "Dwight Whittaker", "c": "Dwight", "num": 4, "pos": "DEF", "nat": "DEF",
               "cara": "equipozero_Dwight", "tec": "Bloqueo total", "reg": "Salida en tromba",
               "rob": "Bloqueo total", "tir": "Disparo cero", "ata": "Muro de acero", "med": 85,
               "rat": {"tir": 82, "reg": 80, "rob": 89, "ata": 72, "vel": 80}},
    "roger": {"n": "Roger Jolly", "c": "Roger", "num": 5, "pos": "DEF", "nat": "DEF", "cara": "calapirata_Roger",
              "tec": "Ancla pirata", "reg": "Regate del corsario", "rob": "Ancla pirata",
              "tir": "Cañonazo", "ata": "Muro del casco", "med": 73,
              "rat": {"tir": 70, "reg": 68, "rob": 77, "ata": 60, "vel": 69}},
    "venus": {"n": "Neith Venus", "c": "Neith", "num": 8, "pos": "MED", "nat": "MED", "cara": "universal_Venus",
              "tec": "Órbita lunar", "reg": "Pase cósmico", "rob": "Gravedad cero",
              "tir": "Disparo orbital", "ata": "Escudo lunar", "med": 81,
              "rat": {"tir": 79, "reg": 84, "rob": 77, "ata": 68, "vel": 80}},
    "sol": {"n": "Sol Daystar", "c": "Sol", "num": 10, "pos": "DEL", "nat": "DEL", "cara": "universal_Sol",
            "tec": "Llamarada solar", "reg": "Giro solar", "rob": "Eclipse",
            "tir": "Llamarada solar", "ata": "Corona", "med": 91,
            "rat": {"tir": 95, "reg": 88, "rob": 83, "ata": 76, "vel": 88}},
    "doug": {"n": "Doug McArthur", "c": "Doug", "num": 11, "pos": "DEL", "nat": "DEL", "cara": "mardeluna_Doug",
             "tec": "Puntería lunar", "reg": "Finta de marea", "rob": "Mareo",
             "tir": "Puntería lunar", "ata": "Ciclo", "med": 73,
             "rat": {"tir": 78, "reg": 72, "rob": 66, "ata": 58, "vel": 70}},
    "albion": {"n": "Albion Lumina", "c": "Albion", "num": 1, "pos": "POR", "nat": "POR",
               "cara": "equipozero_Albion", "tec": "Torbellino interceptor", "reg": "Bola falsa",
               "rob": "Millón de manos", "tir": "Impulso del equipo definitivo", "ata": "Despeje cohete",
               "med": 87, "rat": {"tir": 86, "reg": 69, "rob": 92, "ata": 96, "vel": 80}},
    "davy": {"n": "Davy Jones", "c": "Davy", "num": 11, "pos": "DEL", "nat": "DEL", "cara": "calapirata_Davy",
             "tec": "Cañón celestial", "reg": "Himno de Atenea", "rob": "Estela ígnea",
             "tir": "Cañón celestial", "ata": "Bloque de hielo", "med": 77,
             "rat": {"tir": 87, "reg": 86, "rob": 78, "ata": 73, "vel": 81}},
}

ONCE_ROYALREDUX = [J["king"], J["bargie"], J["cain"], J["dwight"], J["roger"],
                   J["stonewall"], J["spark"], J["venus"], J["samford"], J["sol"], J["doug"]]

# ---------------------------------------------------------------- JS nuevo
JS_HELPERS = r"""
  /* ---------------------------------------------------------------- v157
     Banquillo: los jugadores que no entran en ningun once de 11 van al mercado
     como agentes libres. Nunca se inventan caras ni se usan munecos de respaldo. */
  window.DRAFT_CAREER_ES_REDUX = function(p){
    if (!p) return false;
    var cara = String(p.cara || ""), n = String(p.n || p.nombre || "").toLowerCase().replace(/\s+/g, " ").trim();
    if (cara === "libre126_49" || cara === "libre126_59") return true;
    if (/^(joseph )?king\s*(\(redux\)|redux)$/.test(n)) return true;
    if (/^(david )?samford\s*(\(redux\)|redux)$/.test(n)) return true;
    return false;
  };
  window.DRAFT_CAREER_SPRITE_OK = function(cara){
    try {
      var A = window.ActivosDibujosReales;
      return !!(cara && A && A.heads && A.heads[cara]);
    } catch (e) { return false; }
  };
  window.DRAFT_CAREER_BANQUILLO = function(){
    var fuente = [];
    window.DRAFT_CAREER_RESERVE_ROSTER_POOL.forEach(function(p){ fuente.push(p); });
    if (typeof LIBRES_INICIALES !== "undefined") LIBRES_INICIALES.forEach(function(p){ fuente.push(p); });
    return fuente;
  };
"""


def js_carrera_helpers():
    return r"""
            /* ------------------------------------------------------------ v157
               22 clubes, onces de 11 y banquillo al mercado libre. */
            function spriteOk157(cara){
                if (!cara) return false;
                if (!window.DRAFT_CAREER_SPRITE_OK) return true;
                try { return !!window.DRAFT_CAREER_SPRITE_OK(cara); } catch (e) { return false }
            }

            function esRedux157(p){
                if (!p) return false;
                if (window.DRAFT_CAREER_ES_REDUX) { try { return !!window.DRAFT_CAREER_ES_REDUX(p); } catch (e) {} }
                return false
            }

            function banquillo157(){
                try { return window.DRAFT_CAREER_BANQUILLO ? window.DRAFT_CAREER_BANQUILLO() : [] } catch (e) { return [] }
            }

            function repartirDivisiones157(ids){
                var orden = ids.slice().sort(function(a, b) {
                    return mediaInicial141(a) - mediaInicial141(b) || a.localeCompare(b)
                });
                var total = orden.length, arriba = Math.ceil(total / 2), div = {};
                orden.forEach(function(id, i) { div[id] = i < total - arriba ? 2 : 1 });
                if (ids.indexOf("royalredux") >= 0 && div.royalredux !== 1) {
                    var baja = ids.filter(function(id) { return div[id] === 1 && id !== "royalredux" })
                        .sort(function(a, b) { return mediaInicial141(a) - mediaInicial141(b) || a.localeCompare(b) })[0];
                    if (baja) { div[baja] = 2; div.royalredux = 1 }
                }
                return div
            }

            function equilibrarDivisiones157(o){
                if (!o || !o.div) return o;
                var objetivo = Math.ceil(IDS.length / 2);
                var uno = IDS.filter(function(id) { return o.div[id] === 1 });
                var dos = IDS.filter(function(id) { return o.div[id] === 2 });
                while (uno.length > objetivo) {
                    var fuera = uno.filter(function(id) { return id !== "royalredux" })
                        .sort(function(a, b) { return mediaInicial141(a) - mediaInicial141(b) || a.localeCompare(b) })[0];
                    if (!fuera) break;
                    o.div[fuera] = 2;
                    uno = uno.filter(function(id) { return id !== fuera });
                    dos.push(fuera)
                }
                while (uno.length < objetivo && dos.length > objetivo) {
                    var entra = dos.slice().sort(function(a, b) {
                        return mediaInicial141(b) - mediaInicial141(a) || a.localeCompare(b)
                    })[0];
                    if (!entra) break;
                    o.div[entra] = 1;
                    dos = dos.filter(function(id) { return id !== entra });
                    uno.push(entra)
                }
                return o
            }

            function carasOcupadas157(o){
                var m = Object.create(null);
                IDS.forEach(function(id) {
                    (o.plantillas[id] || []).forEach(function(p) { if (p && p.cara) m[p.cara] = 1 })
                });
                if (o.economia && Array.isArray(o.economia.libres)) o.economia.libres.forEach(function(p) {
                    if (p && p.cara) m[p.cara] = 1
                });
                return m
            }

            function altasLibres157(o){
                if (!o || !o.economia) return 0;
                if (!Array.isArray(o.economia.libres)) o.economia.libres = [];
                var vistas = carasOcupadas157(o), n = 0;
                banquillo157().forEach(function(ref) {
                    if (!ref || !ref.cara || vistas[ref.cara]) return;
                    if (esRedux157(ref)) return;
                    if (!spriteOk157(ref.cara)) return;
                    vistas[ref.cara] = 1;
                    var q = Object.assign({}, ref);
                    o.pidSeq = (o.pidSeq || 0) + 1;
                    q.pid = "p" + o.pidSeq;
                    q.pos = q.pos || q.nat;
                    q.nat = q.nat || q.pos;
                    o.economia.libres.push(q);
                    n++
                });
                return n
            }

            function soltarALibres157(o, lista, liberado){
                if (!o || !o.economia) return 0;
                if (!Array.isArray(o.economia.libres)) o.economia.libres = [];
                var vistas = carasOcupadas157(o), n = 0;
                (lista || []).forEach(function(p) {
                    if (!p || !p.cara || vistas[p.cara]) return;
                    if (esRedux157(p)) return;
                    if (!spriteOk157(p.cara)) return;
                    vistas[p.cara] = 1;
                    var q = Object.assign({}, p);
                    if (!q.pid) { o.pidSeq = (o.pidSeq || 0) + 1; q.pid = "p" + o.pidSeq }
                    if (liberado) { q.liberado137 = true; q.grupo = "Liberado" }
                    o.economia.libres.push(q);
                    n++
                });
                return n
            }

            function migrarPlantillas157(o){
                if (!o || o.plantillas11v157) return false;
                var sobrantes = [];
                IDS.forEach(function(id) {
                    var canon = (eq(id).once || []).slice();
                    var actual = Array.isArray(o.plantillas[id]) ? o.plantillas[id].slice() : [];
                    var nuevos = [], usados = {};
                    canon.forEach(function(ref) {
                        var previo = null;
                        for (var i = 0; i < actual.length; i++) {
                            if (actual[i] && actual[i].cara && actual[i].cara === ref.cara) { previo = actual.splice(i, 1)[0]; break }
                        }
                        var q = Object.assign({}, ref);
                        if (previo && previo.pid) q.pid = previo.pid;
                        if (typeof q.num !== "number") q.num = ref.num;
                        if (usados[q.num]) { var n = 1; while (usados[n]) n++; q.num = n }
                        usados[q.num] = 1;
                        if (!q.pid) { o.pidSeq = (o.pidSeq || 0) + 1; q.pid = "p" + o.pidSeq }
                        nuevos.push(q)
                    });
                    actual.forEach(function(p) { if (p && p.cara) sobrantes.push(p) });
                    o.plantillas[id] = nuevos
                });
                soltarALibres157(o, sobrantes, true);
                altasLibres157(o);
                o.plantillas11v157 = true;
                o.reservasDraft63 = true;
                return true
            }

            function tieneCalendario157(o){
                if (!o || !o.liga) return false;
                return [1, 2].every(function(d) {
                    var L = o.liga[d];
                    return !!(L && Array.isArray(L.cal) && L.cal.length)
                })
            }

            function completarCalendario157(o){
                if (!tieneCalendario157(o)) return false;
                var cambiado = false;
                [1, 2].forEach(function(d) {
                    var L = o.liga[d];
                    if (!L || !Array.isArray(L.cal)) return;
                    var clubes = IDS.filter(function(id) { return o.div[id] === d });
                    var enCal = Object.create(null);
                    L.cal.forEach(function(dia) {
                        (dia || []).forEach(function(p) {
                            if (p && p.h) enCal[p.h] = 1;
                            if (p && p.a) enCal[p.a] = 1
                        })
                    });
                    var faltan = clubes.filter(function(id) { return !enCal[id] });
                    if (!faltan.length) return;
                    var rivales = clubes.filter(function(id) { return enCal[id] });
                    faltan.forEach(function(id) {
                        var dias = [];
                        rivales.forEach(function(r) {
                            dias.push({ h: id, a: r });
                            dias.push({ h: r, a: id })
                        });
                        baraja(dias).forEach(function(p) { L.cal.push([p]) });
                        cambiado = true
                    })
                });
                return cambiado
            }

"""


def main():
    txt = leer()
    if "DRAFT_CAREER_FORMAT_157" in txt:
        print("Ya estaba parcheado a la version 157.")
        return

    # 1. build
    txt = rep(txt, '<meta name="idraft-build" content="156">',
              '<meta name="idraft-build" content="157">', 1, "meta build")

    # 2. comentario del formato
    txt = rep(txt,
              "/* DRAFT_CAREER_FORMAT_63: 21 clubes; dos divisiones; 18 jugadores por plantilla. */",
              "/* DRAFT_CAREER_FORMAT_157: 22 clubes; dos divisiones de 11; once de 11 por club y "
              "el resto del banquillo como agente libre. */", 1, "comentario formato")

    # 3. clubes permitidos en Carrera
    txt = rep(txt, '"fauxshore","claustrosagrado"]);',
              '"fauxshore","claustrosagrado","royalredux"]);', 1, "allowed ids")

    # 4. formaciones base
    txt = rep(txt, '"claustrosagrado":{"POR":1,"DEF":4,"MED":3,"DEL":3}});',
              '"claustrosagrado":{"POR":1,"DEF":4,"MED":3,"DEL":3},'
              '"royalredux":{"POR":1,"DEF":4,"MED":3,"DEL":3}});', 1, "formaciones")

    # 5. Royal Academy Redux con los cinco originales + seis IE1/IE2
    txt = reemplazar_once(txt, '"royalredux":{"id":"royalredux"', ONCE_ROYALREDUX)

    # 6. Imperial sin King ni Samford (los cubren Albion Lumina y Davy Jones)
    p = txt.index('imperial:{id:"imperial"')
    q = txt.index('"once":', p)
    bloque, a, b = bloque_balanceado(txt, q + len('"once":'))
    imperial = js_a_json(bloque)
    imperial = [x for x in imperial if x["n"] not in ("Joseph King", "David Samford")]
    imperial.insert(0, J["albion"])
    imperial.append(J["davy"])
    nums = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 9]
    for jug, num in zip(imperial, nums):
        jug["num"] = num
    txt = txt[:a] + json.dumps(imperial, ensure_ascii=True, separators=(",", ":")) + txt[b:]

    # 7. datos de apoyo en la capa de datos
    ancla = 'window.DRAFT_CAREER_RESERVE_FREE_FACES = Object.freeze(['
    i = txt.index(ancla)
    fin = txt.index("]);", i) + 3
    txt = txt[:fin] + "\n" + JS_HELPERS + txt[fin:]

    # 8. esquema
    txt = rep(txt, 'var Carrera=(function(){"use strict";var ESQ=63;',
              'var Carrera=(function(){"use strict";var ESQ=64;', 1, "ESQ")

    # 9. nuevo estado: onces de 11 + agentes libres
    ini_nuevo = txt.index("function nuevoEstado(mi,seedOverride)")
    bloque_nuevo, _a, fin_nuevo = bloque_balanceado(txt, ini_nuevo)
    viejo_nuevo = txt[ini_nuevo:fin_nuevo]
    nuevo_nuevo = (
        'function nuevoEstado(mi,seedOverride){'
        'var ids=TODOS_IDS.slice();'
        'var div=repartirDivisiones157(ids);'
        'var reserveSeed=(Number(seedOverride)>>>0)||((Math.floor(Math.random()*4294967295)>>>0)||1);'
        'var pl={},seq=0,forma={};'
        'ids.forEach(function(id){var usados={},once=eq(id).once||[];'
        'pl[id]=once.map(function(p){var q=Object.assign({},p);var pos=q.nat;'
        'if(POS126.indexOf(pos)<0)pos=q.pos;if(pos==="GK")pos="POR";'
        'if(POS126.indexOf(pos)>=0){q.nat=pos;q.pos=pos}'
        'q.pid="p"+ ++seq;'
        'if(usados[q.num]){var n=1;while(usados[n])n++;q.num=n}'
        'usados[q.num]=1;return q});'
        'var f=window.DRAFT_CAREER_BASE_FORMATIONS[id]||{POR:1,DEF:4,MED:4,DEL:2};'
        'forma[id]=Object.assign({},f)});'
        'var o={v:ESQ,temp:1,mi:mi,div:div,plantillas:pl,pidSeq:seq,reserveSeed:reserveSeed,'
        'reservasDraft63:true,plantillas11v157:true,copaToca:false,liga:null,copa:null,mercado:[],'
        'palmares:{},balon:[],premiosPendientes:0,movidos:[],trofeos:[],historial:[],ultimaJornada:0,'
        'copaRonda:0,fin:false,golVer:2,preVista:0,'
        'economia:{v:1,saldos:{},ingresos:[],pagadas:[],libres:[],altasLibres:true,forma:forma}};'
        'altasLibres157(o);'
        'return o}'
    )
    txt = rep(txt, viejo_nuevo, nuevo_nuevo, 1, "nuevoEstado")

    # 10. helpers de la carrera (antes de migrar)
    txt = rep(txt, "function migrar(o){", js_carrera_helpers() + "function migrar(o){", 1, "helpers carrera")

    # 11. migrar: divisiones 11 + 11 con Royal Academy Redux en Primera
    txt = rep(txt,
              'var divValida=IDS.every(function(id){return o.div[id]===1||o.div[id]===2})&&d1===10&&d2===11;'
              'var resetLiga=versionAntes<ESQ||!divValida;',
              'if(IDS.indexOf("royalredux")>=0&&o.div.royalredux!==1)o.div.royalredux=1;'
              'equilibrarDivisiones157(o);'
              'd1=IDS.filter(function(id){return o.div[id]===1}).length;'
              'd2=IDS.filter(function(id){return o.div[id]===2}).length;'
              'var divValida=IDS.every(function(id){return o.div[id]===1||o.div[id]===2})&&d1===Math.ceil(IDS.length/2)&&d2===Math.floor(IDS.length/2);'
              'var resetLiga=!tieneCalendario157(o);',
              1, "divisiones migrar")

    # 12. migrar: fuera el relleno de reservas; entran los onces de 11
    viejo_reservas = (
        'if(versionAntes<ESQ&&!o.reservasDraft63){var excluidas=[];'
    )
    i = txt.index(viejo_reservas)
    j = txt.index("else if(!o.reservasDraft63)o.reservasDraft63=true;", i) + len("else if(!o.reservasDraft63)o.reservasDraft63=true;")
    txt = txt[:i] + 'migrarPlantillas157(o);' + txt[j:]

    # 12b. el estado base no debe marcar la migracion como hecha
    txt = rep(txt,
              'Object.keys(base).forEach(function(k){if(o[k]===void 0||o[k]===null)o[k]=base[k]});',
              'Object.keys(base).forEach(function(k){if(k==="plantillas11v157")return;if(o[k]===void 0||o[k]===null)o[k]=base[k]});',
              1, "flag migracion")

    # 13. migrar: completar el calendario existente con los clubes nuevos
    txt = rep(txt, "retirarRedux148(o);", "retirarRedux148(o);\n                completarCalendario157(o);\n                o.plantillas11v157=true;", 1, "calendario migrar")

    # 14. migrar: forma de cada club segun su once real
    txt = rep(txt,
              'if(window.Tecnicas143)window.Tecnicas143.carrera(o);',
              'if(window.Tecnicas143)window.Tecnicas143.carrera(o);'
              'if(o.economia&&o.economia.forma){IDS.forEach(function(id){'
              'var f={POR:0,DEF:0,MED:0,DEL:0};'
              '(o.plantillas[id]||[]).forEach(function(p){var pos=POS126.indexOf(p.nat)>=0?p.nat:p.pos;if(f[pos]!==void 0)f[pos]++});'
              'o.economia.forma[id]=f})}',
              1, "forma migrar")

    # 15. textos de la interfaz
    txt = rep(txt,
              "var side=el2.querySelector(\"#cpSide\");side.innerHTML='<div class=\"cp-hint\">Toca un escudo para ver la plantilla y empezar.<br><br><b style=\"color:#ffd21f\">'+(IDS.length-20)+\"21 clubes</b>, 10 en Primera y 11 en Segunda: los que m\\xE1s media tienen juegan arriba.</div>\";",
              "var side=el2.querySelector(\"#cpSide\");side.innerHTML='<div class=\"cp-hint\">Toca un escudo para ver la plantilla y empezar.<br><br><b style=\"color:#ffd21f\">'+IDS.length+\" clubes</b>, 11 en Primera y 11 en Segunda: los que m\\xE1s media tienen juegan arriba.</div>\";",
              1, "texto careerPick principal")

    txt = rep(txt,
              "n.innerHTML='<div class=\"cp-hint\">Toca un escudo para ver la plantilla y empezar.<br><br><b style=\"color:#ffd21f\">'+(T.length-20)+\" equipos en Tercera</b>, 10 en Segunda y 10 en Primera: los que m\\\\xE1s media tienen juegan arriba.</div>\";",
              "n.innerHTML='<div class=\"cp-hint\">Toca un escudo para ver la plantilla y empezar.<br><br><b style=\"color:#ffd21f\">'+T.length+\" clubes</b>, 11 en Primera y 11 en Segunda: los que m\\\\xE1s media tienen juegan arriba.</div>\";",
              1, "texto careerPick secundario")

    escribir(txt)
    print("index.html parcheado a la build 157.")


if __name__ == "__main__":
    main()
