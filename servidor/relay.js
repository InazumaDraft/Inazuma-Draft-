// Servidor de paso (relay) para la carrera online de Inazuma Draft.
// No hace falta entenderlo: los dos móviles se conectan aquí, se emparejan por
// el número de 5 cifras y este reparte los mensajes de uno a otro.
//
//   node relay.js
//
// Escucha en el puerto que indique la variable PORT (o el 3000).

const http = require('http');
const { WebSocketServer } = require('ws');

const PORT = process.env.PORT || 3000;

const servidor = http.createServer((req, res) => {
  if (req.url === '/' || req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('relay ok\n');
    return;
  }
  res.writeHead(404); res.end();
});

const wss = new WebSocketServer({ server: servidor });
const salas = new Map();          // "48392" -> Set de conexiones

wss.on('connection', (ws) => {
  ws.sala = null;
  console.log('+ alguien se conecta');
  const enviar = (o) => { try { ws.send(JSON.stringify(o)); } catch (e) { } };

  ws.on('message', (crudo) => {
    let o;
    try { o = JSON.parse(crudo); } catch (e) { return; }
    if (!o || !o.t) return;

    if (o.t === 'entrar') {
      const cod = String(o.sala || '').replace(/\D/g, '').slice(0, 5);
      if (cod.length !== 5) { enviar({ t: 'no' }); return; }
      let s = salas.get(cod);
      if (!s) {
        // si la sala no existe solo la puede abrir quien invita
        if (o.rol !== 'anfitrion') { enviar({ t: 'no' }); return; }
        s = new Set();
        salas.set(cod, s);
        enviar({ t: 'ok' });          // la sala ya existe, ya se puede enseñar el número
      }
      if (s.size >= 2) { enviar({ t: 'lleno' }); return; }
      s.add(ws);
      ws.sala = cod;
      console.log('  entra en la sala ' + cod + ' como ' + o.rol + ' (' + s.size + '/2)');
      if (s.size === 2) for (const c of s) { try { c.send(JSON.stringify({ t: 'sala' })); } catch (e) { } }
      return;
    }

    if (o.t === 'msg') {
      const s = salas.get(ws.sala);
      if (!s) return;
      const txt = String(o.txt == null ? '' : o.txt);
      for (const c of s) {
        if (c === ws) continue;
        try { c.send(JSON.stringify({ t: 'msg', txt })); } catch (e) { }
      }
      return;
    }
  });

  const irse = () => {
    const s = salas.get(ws.sala);
    if (!s) return;
    s.delete(ws);
    ws.sala = null;
    if (s.size === 0) { salas.delete(s); salas.delete(ws.sala); return; }
    for (const c of s) { try { c.send(JSON.stringify({ t: 'adios' })); } catch (e) { } }
  };
  ws.on('close', irse);
  ws.on('error', () => { try { ws.close(); } catch (e) { } });
});

servidor.listen(PORT, '0.0.0.0', () => {
  console.log('relay escuchando en el puerto ' + PORT);
});
