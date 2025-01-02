const WebSocket = require('./node_modules/ws');

const server = new WebSocket.Server({ port: 8080 });

let clients = [];

server.on('connection', (socket) => {
  console.log('New client connected');
  clients.push(socket);

  socket.on('message', (message) => {
    // Broadcast the message to all other clients
    clients.forEach((client) => {
      if (client !== socket && client.readyState === WebSocket.OPEN) {
        client.send(message);
      }
    });
  });

  socket.on('close', () => {
    console.log('Client disconnected');
    clients = clients.filter((client) => client !== socket);
  });

  socket.on('error', (error) => {
    console.log(`WebSocket error: ${error}`);
  });
});
