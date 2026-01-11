// routes/irrigation.js
const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const irrigationController = require('../controllers/irrigationController');

// All routes require authentication
router.use(auth);

// Setup irrigation schedule
router.post('/setup', irrigationController.setupIrrigation);

// Get current status
router.get('/status', irrigationController.getIrrigationStatus);

// Manual water now
router.post('/water-now', irrigationController.waterNow);

// Apply diagnostic override
router.post('/apply-override', irrigationController.applyDiagnosticOverride);

// Get irrigation history
router.get('/history', async (req, res) => {
  // Implementation for watering history
});

// Update automation settings
router.put('/settings', async (req, res) => {
  // Implementation for settings update
});

module.exports = router;