import { Server } from 'socket.io'
import { createServer } from 'http'
import Redis from 'ioredis'

const httpServer = createServer()
const io = new Server(httpServer, {
  cors: { origin: '*' }
})

const redis = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379')
})

io.on('connection', (socket) => {
  console.log('Client connected:', socket.id)
  
  socket.on('subscribe', (room: string) => {
    socket.join(room)
    console.log(`Client ${socket.id} joined room: ${room}`)
  })
  
  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id)
  })
})

// Redis Pub/Sub for multi-instance scaling
redis.subscribe('updates', (err) => {
  if (err) console.error('Redis subscribe error:', err)
})

redis.on('message', (channel, message) => {
  const data = JSON.parse(message)
  io.to(data.room).emit(data.event, data.payload)
})

const PORT = process.env.PORT || 8003
httpServer.listen(PORT, () => {
  console.log(`Realtime service running on port ${PORT}`)
})
