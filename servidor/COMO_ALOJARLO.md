# Servidor de la carrera online

Esto es lo que hace que los dos móviles se encuentren por el número de 5 cifras.
Es un programa muy pequeño: abre una sala por número y pasa los mensajes de un
jugador al otro. No guarda nada y no sabe nada de tu partida.

**Sin él la carrera online no funciona.** Los dos teléfonos necesitan un sitio
donde verse las caras; eso es todo lo que hace esto.

---

## Alojarlo en Render (gratis, y ya tienes la cuenta hecha)

Render lee el repositorio de GitHub, así que no hay que subir nada a mano.

1. Entra en **render.com** y conéctalo con tu cuenta de GitHub.
2. **New → Web Service**.
3. Elige el repositorio **Inazuma-Draft-**.
4. Rellena solo esto y deja el resto como está:

   | Campo | Valor |
   |---|---|
   | Name | `inazuma-relay` |
   | Root Directory | `servidor` |
   | Runtime | `Node` |
   | Build Command | `npm install` |
   | Start Command | `node relay.js` |
   | Instance Type | `Free` |

5. **Create Web Service** y espera un par de minutos.

Cuando acabe te dará una dirección parecida a
`https://inazuma-relay.onrender.com`.

**Esa dirección, cambiando `https` por `wss`, es la que hay que poner en el
juego:**

```
wss://inazuma-relay.onrender.com
```

> Ojo: en el plan gratis el servidor se duerme si nadie lo usa en 15 minutos.
> La primera vez que entréis después de un rato tarda unos 30 segundos en
> despertar. Si os molesta, la instancia de pago más barata son 7 dólares al mes
> y no se duerme nunca.

---

## Comprobar que funciona

Abre en el navegador la dirección que te ha dado Render
(`https://inazuma-relay.onrender.com`). Tiene que poner:

```
relay ok
```

Si pone eso, está vivo.

---

## Probarlo en local

```bash
cd servidor
npm install
node relay.js
```

Escucha en el puerto 3000. Para usar el juego de tu ordenador contra él, abre
`index.html#relay=ws://127.0.0.1:3000`.

---

## Si prefieres otro sitio

Vale cualquier sitio que arranque un programa de Node: Railway, Koyeb, Fly.io...
El programa es `relay.js`, necesita `npm install` y escucha en el puerto que
indique la variable de entorno `PORT`.
