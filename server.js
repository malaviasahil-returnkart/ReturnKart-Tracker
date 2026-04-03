require('dotenv').config();
const express = require('express');
const cors = require('cors');

const emailRoutes = require('./routes/email');
const orderRoutes = require('./routes/orders');

const app = express();

const allowedOrigins = [
  'https://return-manager.replit.app',
  'https://returnkart.in',
  'https://www.returnkart.in',
  'http://localhost:3000',
  'http://localhost:5173',
];

app.use(cors({
  origin: function (origin, callback) {
    if (!origin) return callback(null, true);
    if (allowedOrigins.includes(origin)) return callback(null, true);
    if (origin.endsWith('.replit.dev') || origin.endsWith('.replit.app')) return callback(null, true);
    return callback(new Error('Not allowed by CORS'));
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
}));

app.use(express.json());

app.use('/api/email', emailRoutes);
app.use('/api/orders', orderRoutes);

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'returnkart-backend', timestamp: new Date().toISOString() });
});

app.get('/', (req, res) => {
  res.json({ message: 'ReturnKart API is running', version: '2.0.0', db: 'supabase' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 ReturnKart backend running on port ${PORT}`);
});
