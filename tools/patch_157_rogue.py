#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build 157 - sprites estrictos en el partido Rogue del Draft.

  * El mapa Draft->Rogue (rogue/draft-map.js) gana las tres identidades de Royal Academy
    Redux que no tenian cara propia: Argie Bargie (21535), Caleb Stonewall (21541) y
    Jonah Spark (21538).
  * El motor acepta referencias autenticas `file,row` de las plantillas Rogue cuando el
    jugador no tiene `cs` (Stonewall y Spark solo existen en r09.png).
  * La identidad manda: dos equipos del mismo partido pueden compartir personaje (Royal
    Academy y su version Redux), asi que el cupo de apariencias se controla dentro de cada
    once y los suplentes siguen evitando repetir hoja en todo el partido.
  * Solo se cae al muneco de respaldo si el jugador no tiene identidad Rogue verificada,
    cosa que ya no ocurre en ninguno de los 22 clubes de Carrera.
  * Deja un diagnostico (window.__draftOnceDebug / __draftOnceEquipos) cuando el motor
    corre embebido, para comprobar que ningun puesto usa un muñeco de respaldo.
"""
import sys

MAPA = "rogue/draft-map.js"
MOTOR = "rogue/index.html"
MARCA = "La identidad manda"
MARCA2 = "IDENTIDAD ROGUE VERIFICADA"


def leer(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def escribir(p, t):
    with open(p, "w", encoding="utf-8") as f:
        f.write(t)


def rep(txt, viejo, nuevo, etiqueta, veces=1):
    n = txt.count(viejo)
    if n != veces:
        raise SystemExit("ERROR [%s]: %d coincidencias (esperaba %d)" % (etiqueta, n, veces))
    return txt.replace(viejo, nuevo)


DRAFT_FOR_ANTES = "    // Alpino's six IE2 additions are an intentional, role-verified identity-to-sprite mapping.\n    if (mapped && (draftId === 'alpino' ? mapped.role === role : draftIdentityMatch(record.name, mapped))) return mapped;\n"

DRAFT_FOR_DESPUES = '    // El mapa Draft->Rogue es la tabla de IDENTIDAD ROGUE VERIFICADA: si hay entrada se usa\n    // siempre (sin muñecos de respaldo ni sustituciones). El nombre solo sirve de apoyo.\n    if (mapped) return mapped;\n'

ANTES = "  function buildDraftRogueTeam(team, side, sharedAssets) {\n    const chosen = draftPickEleven(team);\n    const roles = chosen.map(x => x.role);\n    const positions = layout(roles);\n    const rogueTeam = TEAM(draftTeamKey(team, side));\n    const draftId = String(team.id || '').toLowerCase();\n    const nativeKit = draftId === 'raimon' ? null : (rogueTeam && (rogueTeam.kit || DRAFT_ROGUE_KITS[rogueTeam.key])) || null;\n    const usedAssets = sharedAssets || { ids: new Set(), refs: new Set() };\n    const nativeMembers = draftId === 'raimon' ? new Map() : new Map((rogueTeam && rogueTeam.players || []).map(m => [Number(m.id), m]));\n    const players = chosen.map(({ record, role }, i) => {\n      let pd = draftPlayerFor(record, role, draftId);\n      let mapped = !!(pd && pd.cs);\n      if (mapped) {\n        const mappedRef = Sprites.refOf(pd), mappedKey = String(mappedRef.file) + ':' + Number(mappedRef.row);\n        if (usedAssets.ids.has(Number(pd.id)) || usedAssets.refs.has(mappedKey)) mapped = false;\n      }\n      if (!mapped) pd = draftTemplatePlayer(role, usedAssets, draftId);\n      if (!pd || !pd.cs) throw new Error('No se encontró un perfil Rogue base para ' + (record.name || role));\n      const native = mapped ? nativeMembers.get(Number(pd.id)) : null;\n      let teamKeeper = draftId !== 'raimon' && !native && role === 'POR' && rogueTeam ? rogueTeam.players.find(m => m.role === 'POR') : null;\n      let teamSprite = native && native.file ? native : teamKeeper && teamKeeper.file ? teamKeeper : null;\n      if (teamSprite && usedAssets.refs.has(String(teamSprite.file) + ':' + Number(teamSprite.row))) teamSprite = null;\n      const sprite = teamSprite\n        ? { file: String(teamSprite.file), row: Number(teamSprite.row) || 0 }\n        : Object.assign({}, Sprites.refOf(pd));\n      const spriteRefKey = String(sprite.file) + ':' + Number(sprite.row);\n      usedAssets.ids.add(Number(pd.id));\n      if (teamSprite === native && native) usedAssets.ids.add(Number(native.id));\n      if (teamSprite === teamKeeper && teamKeeper) usedAssets.ids.add(Number(teamKeeper.id));\n      usedAssets.refs.add(spriteRefKey);\n      // Las filas Rogue nativas conservan su uniforme; los sprites de colección reciben el kit de su equipo.\n      const hasNativeKit = !!(rogueTeam && rogueTeam.kit);\n      if (role !== 'POR' && nativeKit && (/^c\\d+\\.png$/i.test(sprite.file) || (hasNativeKit && /^r\\d+\\.png$/i.test(sprite.file)))) {\n        sprite.kit = Object.assign({}, nativeKit);\n      }\n      // Si faltase una hoja, usar un muñeco entero y vestirlo con los colores de este equipo.\n      const fallbackKit = nativeKit || (draftId === 'raimon' ? { a: '#D5B410', b: '#39527B' } : null);\n      sprite.customFallbacks = [draftFallbackSprite(fallbackKit), DRAFT_GENERIC_SPRITE];\n      const rating = Number(record.rating) || Number(record.med) || 70;\n      const draftStats = record.draftStats && typeof record.draftStats === 'object' ? record.draftStats : {};\n      const stat = key => {\n        const base = Number(pd.ie && pd.ie[key]);\n        const draftValue = key === 'tiro' ? Number(draftStats.tir)\n          : key === 'control' ? Number(draftStats.reg)\n          : key === 'defensa' ? Number(draftStats.rob)\n          : key === 'rapidez' ? Number(draftStats.vel) : NaN;\n        if (Number.isFinite(draftValue) && draftValue > 0) return Math.round(draftValue * 0.7 + rating * 0.3);\n        return Math.round(base ? base * 0.45 + rating * 0.55 : rating);\n      };\n      const techs = mapped ? startingTechs(pd) : [];\n      const matchPlayer = buildMatchPlayer(pd.id, role, stat, techs, [], side * 11 + i, positions[i]);\n      matchPlayer.stamDrain = +(1.3 - rating / 200).toFixed(2);\n      if (role === 'POR') {\n        const keeperRating = Number(draftStats.ata) || rating;\n        matchPlayer.gk = Math.round(keeperRating * 0.7 + rating * 0.3);\n      }\n      matchPlayer.key = String(record.face || record.name || ('draft-' + side + '-' + i));\n      matchPlayer.name = String(record.name || pd.name || 'Jugador');\n      matchPlayer.sprite = sprite;\n      return matchPlayer;\n    });\n    return { name: String(team.name || 'Equipo Draft'), key: String(team.id || team.name || ''), players };\n  }\n"

DESPUES = "  function buildDraftRogueTeam(team, side, sharedAssets) {\n    const chosen = draftPickEleven(team);\n    const roles = chosen.map(x => x.role);\n    const positions = layout(roles);\n    const rogueTeam = TEAM(draftTeamKey(team, side));\n    const draftId = String(team.id || '').toLowerCase();\n    const nativeKit = draftId === 'raimon' ? null : (rogueTeam && (rogueTeam.kit || DRAFT_ROGUE_KITS[rogueTeam.key])) || null;\n    const usedAssets = sharedAssets || { ids: new Set(), refs: new Set() };\n    const nativeMembers = draftId === 'raimon' ? new Map() : new Map((rogueTeam && rogueTeam.players || []).map(m => [Number(m.id), m]));\n    const onceDebug = [];\n    // La identidad manda: dos equipos del mismo partido pueden compartir personaje\n    // (Royal Academy y su versión Redux, por ejemplo). El cupo de apariencias se\n    // controla dentro de cada once; los suplentes sí evitan repetir hoja en todo el partido.\n    const teamIds = new Set();\n    const teamRefs = new Set();\n    const players = chosen.map(({ record, role }, i) => {\n      let pd = draftPlayerFor(record, role, draftId);\n      let mapped = !!pd;\n      let refBase = null;\n      if (mapped) {\n        // La hoja de colección (cs) manda; si el jugador solo existe en la plantilla\n        // Rogue, se acepta su referencia auténtica file,row.\n        const nativo = nativeMembers.get(Number(pd.id));\n        refBase = pd.cs ? Sprites.refOf(pd)\n          : (nativo && nativo.file ? { file: String(nativo.file), row: Number(nativo.row) || 0 } : null);\n        if (!refBase) mapped = false;\n        else if (teamIds.has(Number(pd.id)) || teamRefs.has(String(refBase.file) + ':' + Number(refBase.row))) { mapped = false; refBase = null; }\n      }\n      if (!mapped) {\n        pd = draftTemplatePlayer(role, usedAssets, draftId);\n        refBase = pd && pd.cs ? Sprites.refOf(pd) : null;\n      }\n      if (!pd || !refBase) {\n        console.warn('[draft] sin perfil Rogue', { equipo: draftId, rol: role, nombre: String(record.name || ''), cara: String(record.face || ''), id: pd && pd.id, mapeado: mapped });\n        throw new Error('No se encontró un perfil Rogue base para ' + (record.name || role));\n      }\n      const native = mapped ? nativeMembers.get(Number(pd.id)) : null;\n      // El portero nativo del rival solo se usa cuando el jugador NO tiene identidad propia.\n      let teamKeeper = !mapped && draftId !== 'raimon' && role === 'POR' && rogueTeam ? rogueTeam.players.find(m => m.role === 'POR') : null;\n      let teamSprite = native && native.file ? native : teamKeeper && teamKeeper.file ? teamKeeper : null;\n      if (teamSprite && usedAssets.refs.has(String(teamSprite.file) + ':' + Number(teamSprite.row))) teamSprite = null;\n      const sprite = teamSprite\n        ? { file: String(teamSprite.file), row: Number(teamSprite.row) || 0 }\n        : Object.assign({}, refBase);\n      const spriteRefKey = String(sprite.file) + ':' + Number(sprite.row);\n      teamIds.add(Number(pd.id));\n      if (mapped) teamRefs.add(String(refBase.file) + ':' + Number(refBase.row));\n      usedAssets.ids.add(Number(pd.id));\n      if (teamSprite === native && native) usedAssets.ids.add(Number(native.id));\n      if (teamSprite === teamKeeper && teamKeeper) usedAssets.ids.add(Number(teamKeeper.id));\n      usedAssets.refs.add(spriteRefKey);\n      // Las filas Rogue nativas conservan su uniforme; los sprites de colección reciben el kit de su equipo.\n      const hasNativeKit = !!(rogueTeam && rogueTeam.kit);\n      if (role !== 'POR' && nativeKit && (/^c\\d+\\.png$/i.test(sprite.file) || (hasNativeKit && /^r\\d+\\.png$/i.test(sprite.file)))) {\n        sprite.kit = Object.assign({}, nativeKit);\n      }\n      // Si faltase una hoja, usar un muñeco entero y vestirlo con los colores de este equipo.\n      const fallbackKit = nativeKit || (draftId === 'raimon' ? { a: '#D5B410', b: '#39527B' } : null);\n      sprite.customFallbacks = [draftFallbackSprite(fallbackKit), DRAFT_GENERIC_SPRITE];\n      const rating = Number(record.rating) || Number(record.med) || 70;\n      const draftStats = record.draftStats && typeof record.draftStats === 'object' ? record.draftStats : {};\n      const stat = key => {\n        const base = Number(pd.ie && pd.ie[key]);\n        const draftValue = key === 'tiro' ? Number(draftStats.tir)\n          : key === 'control' ? Number(draftStats.reg)\n          : key === 'defensa' ? Number(draftStats.rob)\n          : key === 'rapidez' ? Number(draftStats.vel) : NaN;\n        if (Number.isFinite(draftValue) && draftValue > 0) return Math.round(draftValue * 0.7 + rating * 0.3);\n        return Math.round(base ? base * 0.45 + rating * 0.55 : rating);\n      };\n      const techs = mapped ? startingTechs(pd) : [];\n      const matchPlayer = buildMatchPlayer(pd.id, role, stat, techs, [], side * 11 + i, positions[i]);\n      matchPlayer.stamDrain = +(1.3 - rating / 200).toFixed(2);\n      if (role === 'POR') {\n        const keeperRating = Number(draftStats.ata) || rating;\n        matchPlayer.gk = Math.round(keeperRating * 0.7 + rating * 0.3);\n      }\n      matchPlayer.key = String(record.face || record.name || ('draft-' + side + '-' + i));\n      matchPlayer.name = String(record.name || pd.name || 'Jugador');\n      matchPlayer.sprite = sprite;\n      // Diagnóstico del once: permite comprobar que ningún puesto usa un muñeco de respaldo.\n      if (ROGUE_EMBED) onceDebug.push({ name: matchPlayer.name, side, role, mapped: mapped,\n        id: pd && pd.id != null ? Number(pd.id) : null, sprite: { file: String(sprite.file), row: Number(sprite.row) || 0 } });\n      return matchPlayer;\n    });\n    if (ROGUE_EMBED) {\n      window.__draftOnceDebug = (window.__draftOnceDebug || []).concat(onceDebug);\n      window.__draftOnceEquipos = (window.__draftOnceEquipos || []).concat([{ side, name: String(team.name || ''), key: String(team.id || '') }]);\n    }\n    return { name: String(team.name || 'Equipo Draft'), key: String(team.id || team.name || ''), players };\n  }\n"


def main():
    mapa = leer(MAPA)
    if "n141_royalredux_1" in mapa:
        print("draft-map.js ya estaba actualizado.")
    else:
        ancla = '"alpino_Yule":21589'
        inicio = mapa.find("window.RogueDraftMap")
        pos = mapa.find(ancla + "});", inicio) if inicio >= 0 else -1
        if pos < 0:
            raise SystemExit("No encuentro el final del mapa Draft->Rogue")
        nuevo = (ancla + ',"n141_royalredux_1":21535,"n141_royalredux_2":21541,'
                 '"n141_royalredux_3":21538});')
        mapa = mapa[:pos] + nuevo + mapa[pos + len(ancla + "});"):]
        escribir(MAPA, mapa)
        print("draft-map.js: identidades de Royal Academy Redux anadidas.")

    motor = leer(MOTOR)
    if MARCA2 in motor:
        print("draftPlayerFor ya estaba actualizado.")
    else:
        if DRAFT_FOR_ANTES not in motor:
            raise SystemExit("ERROR [draftPlayerFor]: no encuentro el bloque original")
        motor = motor.replace(DRAFT_FOR_ANTES, DRAFT_FOR_DESPUES)
        escribir(MOTOR, motor)
        print("draftPlayerFor: el mapa manda sin sustituciones.")

    motor = leer(MOTOR)
    if MARCA in motor:
        print("rogue/index.html ya estaba actualizado.")
    else:
        if ANTES not in motor:
            raise SystemExit("ERROR [buildDraftRogueTeam]: no encuentro el bloque original")
        motor = motor.replace(ANTES, DESPUES)
        escribir(MOTOR, motor)
        print("rogue/index.html: referencias file,row aceptadas y identidad con prioridad.")


if __name__ == "__main__":
    main()
