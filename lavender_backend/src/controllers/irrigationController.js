// controllers/irrigationController.js
const Irrigation = require('../models/irrigation');
const DiagnosticResult = require('../models/diagnostic');

// Calculate base irrigation for lavender
const calculateLavenderIrrigation = (numberOfPlants) => {
  // Lavender needs: ~500mL per plant per week (divided into intervals)
  const waterPerPlantPerWeek = 500; // mL
  const optimalInterval = 3; // days for lavender
  const waterPerCycle = (waterPerPlantPerWeek / (7/optimalInterval)) * numberOfPlants;
  
  return {
    waterPerCycle: Math.round(waterPerCycle),
    intervalHours: optimalInterval * 24,
    flowRate: 2.5 // L/min
  };
};

// Create/Update irrigation schedule
exports.setupIrrigation = async (req, res) => {
  try {
    const { numberOfPlants, plantType, isAutomated } = req.body;
    const userId = req.user.id;
    
    // Calculate irrigation based on plant count
    const calculation = calculateLavenderIrrigation(numberOfPlants);
    
    // Check for existing irrigation schedule
    let irrigation = await Irrigation.findOne({ userId });
    
    if (irrigation) {
      // Update existing
      irrigation.numberOfPlants = numberOfPlants;
      irrigation.plantType = plantType || 'lavender';
      irrigation.calculatedWaterPerPlant = calculation.waterPerCycle / numberOfPlants;
      irrigation.totalWaterPerCycle = calculation.waterPerCycle;
      irrigation.calculatedIntervalHours = calculation.intervalHours;
      irrigation.flowRate = calculation.flowRate;
      irrigation.nextScheduled = new Date(Date.now() + calculation.intervalHours * 3600000);
    } else {
      // Create new
      irrigation = new Irrigation({
        userId,
        numberOfPlants,
        plantType: plantType || 'lavender',
        calculatedWaterPerPlant: calculation.waterPerCycle / numberOfPlants,
        totalWaterPerCycle: calculation.waterPerCycle,
        calculatedIntervalHours: calculation.intervalHours,
        flowRate: calculation.flowRate,
        nextScheduled: new Date(Date.now() + calculation.intervalHours * 3600000),
        isAutomated
      });
    }
    
    await irrigation.save();
    
    res.json({
      success: true,
      irrigation: irrigation,
      calculation: {
        waterPerCycle: calculation.waterPerCycle,
        intervalDays: calculation.intervalHours / 24,
        nextWatering: irrigation.nextScheduled
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

// Apply diagnostic override
exports.applyDiagnosticOverride = async (req, res) => {
  try {
    const { diagnosticId } = req.body;
    const userId = req.user.id;
    
    const diagnostic = await DiagnosticResult.findById(diagnosticId);
    if (!diagnostic) {
      return res.status(404).json({ error: 'Diagnostic not found' });
    }
    
    const irrigation = await Irrigation.findOne({ userId });
    if (!irrigation) {
      return res.status(404).json({ error: 'Irrigation schedule not found' });
    }
    
    // Calculate adjustments based on diagnosis
    let adjustment = {
      waterAmountChange: 0,
      intervalChange: 0,
      durationCycles: 3 // Default: apply for 3 cycles
    };
    
    switch(diagnostic.diagnosis.status) {
      case 'overwatered':
        adjustment.waterAmountChange = -30; // Reduce water by 30%
        adjustment.intervalChange = +40; // Increase interval by 40%
        break;
      case 'underwatered':
        adjustment.waterAmountChange = +40; // Increase water by 40%
        adjustment.intervalChange = -20; // Decrease interval by 20%
        break;
      case 'disease_risk':
        adjustment.waterAmountChange = -20;
        adjustment.intervalChange = +30;
        break;
      default:
        // No adjustment for healthy plants
    }
    
    // Apply override
    irrigation.overrideSettings = {
      isActive: true,
      reason: diagnostic.diagnosis.status,
      moistureLevel: diagnostic.moistureLevel,
      adjustedWaterAmount: adjustment.waterAmountChange,
      adjustedInterval: adjustment.intervalChange,
      durationCycles: adjustment.durationCycles,
      remainingCycles: adjustment.durationCycles
    };
    
    irrigation.status = 'override';
    
    // Update diagnostic record
    diagnostic.appliedToIrrigation = true;
    diagnostic.appliedAt = new Date();
    diagnostic.irrigationAdjustment = {
      needed: adjustment.waterAmountChange !== 0 || adjustment.intervalChange !== 0,
      adjustmentType: adjustment.waterAmountChange > 0 ? 'increase' : 'decrease',
      waterAmountChange: adjustment.waterAmountChange,
      intervalChange: adjustment.intervalChange,
      duration: adjustment.durationCycles * (irrigation.calculatedIntervalHours / 24)
    };
    
    await Promise.all([irrigation.save(), diagnostic.save()]);
    
    res.json({
      success: true,
      message: `Irrigation override applied for ${diagnostic.diagnosis.status}`,
      override: irrigation.overrideSettings,
      nextCycle: irrigation.nextScheduled
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

// Get current irrigation status
exports.getIrrigationStatus = async (req, res) => {
  try {
    const irrigation = await Irrigation.findOne({ userId: req.user.id })
      .populate('userId', 'name email');
    
    if (!irrigation) {
      return res.json({
        hasSchedule: false,
        message: 'No irrigation schedule set up'
      });
    }
    
    res.json({
      hasSchedule: true,
      irrigation,
      timeUntilNext: irrigation.nextScheduled - new Date()
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

// Manual water now
exports.waterNow = async (req, res) => {
  try {
    const irrigation = await Irrigation.findOne({ userId: req.user.id });
    
    if (!irrigation) {
      return res.status(404).json({ error: 'No irrigation schedule found' });
    }
    
    // Simulate watering
    irrigation.lastIrrigation = new Date();
    irrigation.nextScheduled = new Date(Date.now() + irrigation.calculatedIntervalHours * 3600000);
    
    // If in override mode, decrement remaining cycles
    if (irrigation.overrideSettings.isActive && irrigation.overrideSettings.remainingCycles > 0) {
      irrigation.overrideSettings.remainingCycles -= 1;
      
      if (irrigation.overrideSettings.remainingCycles === 0) {
        irrigation.overrideSettings.isActive = false;
        irrigation.status = 'active';
      }
    }
    
    await irrigation.save();
    
    // Log this watering event
    // await WateringLog.create({ ... });
    
    res.json({
      success: true,
      message: `Watering completed. ${irrigation.totalWaterPerCycle}mL released.`,
      nextWatering: irrigation.nextScheduled,
      overrideRemaining: irrigation.overrideSettings.remainingCycles
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};