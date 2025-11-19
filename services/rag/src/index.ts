import Fastify from 'fastify'

const app = Fastify({ logger: true })

app.get('/health', async () => {
  return { status: 'healthy', service: 'rag' }
})

app.post('/search', async (request) => {
  const { query } = request.body as { query: string }
  
  // TODO: Implement semantic search
  return {
    query,
    results: [],
    message: 'RAG service scaffold - implementation pending'
  }
})

const start = async () => {
  try {
    await app.listen({ port: 8002, host: '0.0.0.0' })
  } catch (err) {
    app.log.error(err)
    process.exit(1)
  }
}

start()
