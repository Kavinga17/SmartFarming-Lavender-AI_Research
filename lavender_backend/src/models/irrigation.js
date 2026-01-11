// models/irrigation.js
const mongoose = require('mongoose');

const IrrigationScheduleSchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  plantType: {
    type: String,
    default: 'lavender',
    enum: ['lavender', 'rosemary', 'sage', 'custom']
  },
  numberOfPlants: {
    type: Number,
    required: true,
    min: 1
  },
  // Normal schedule calculation
  calculatedWaterPerPlant: { type: Number }, // in mL
  calculatedIntervalHours: { type: Number }, // in hours
  totalWaterPerCycle: { type: Number }, // in mL
  flowRate: { type: Number, default: 2.5 }, // L/min
  
  // Current status
  status: {
    type: String,
    enum: ['active', 'paused', 'override', 'maintenance'],
    default: 'active'
  },
  
  // Smart override from diagnostics
  overrideSettings: {
    isActive: { type: Boolean, default: false },
    reason: String, // e.g., 'overwatering', 'underwatering', 'disease'
    moistureLevel: Number, // 0-100%
    adjustedWaterAmount: Number, // % adjustment (+/-)
    adjustedInterval: Number, // % adjustment (+/-)
    durationCycles: Number, // how many cycles this override lasts
    remainingCycles: Number
  },
  
  // History
  lastIrrigation: Date,
  nextScheduled: Date,
  
  // Settings
  isAutomated: { type: Boolean, default: true },
  manualOverride: {
    isActive: Boolean,
    manualWaterAmount: Number,
    manualInterval: Number
  }
}, { timestamps: true });

module.exports = mongoose.model('Irrigation', IrrigationScheduleSchema);