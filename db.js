const mongoose = require('mongoose');

// ─── User Model (for approval system) ────────────────────
const userSchema = new mongoose.Schema({
  userId: { type: String, required: true, unique: true },
  chatId: { type: String, required: true },
  username: { type: String },
  firstName: { type: String },
  lastName: { type: String },
  approved: { type: Boolean, default: false },
  rejected: { type: Boolean, default: false },
  requestedAt: { type: Date, default: Date.now },
  approvedAt: { type: Date, default: null },
  approvedBy: { type: String, default: null }
});

const User = mongoose.model('User', userSchema);

// ─── Subscription Model ───────────────────────────────────
const subscriptionSchema = new mongoose.Schema({
  chatId: { type: String, required: true },
  userId: { type: String, required: true },
  username: { type: String },
  provincia: { type: String, required: true },
  provinciaCode: { type: String, required: true },
  tramite: { type: String, required: true },
  tramiteCode: { type: String, required: true },
  oficina: { type: String, default: 'Cualquiera' },
  oficinaCode: { type: String, default: '' },
  active: { type: Boolean, default: true },
  lastNotified: { type: Date, default: null },
  createdAt: { type: Date, default: Date.now }
});

const Subscription = mongoose.model('Subscription', subscriptionSchema);

async function connectDB() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('✅ MongoDB connected');
  } catch (err) {
    console.error('❌ MongoDB connection error:', err);
    process.exit(1);
  }
}

module.exports = { connectDB, Subscription, User };
