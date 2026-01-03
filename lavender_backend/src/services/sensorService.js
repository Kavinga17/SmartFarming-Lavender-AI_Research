class SensorService {
  analyzeSensorData(sensorData) {
    const issues = [];
    const standards = {
      nitrogen: { min: 40, max: 80, optimal: 60, unit: 'ppm', description: 'Essential for leaf growth and green color' },
      phosphorus: { min: 20, max: 50, optimal: 35, unit: 'ppm', description: 'Important for root development and flowering' },
      potassium: { min: 30, max: 70, optimal: 50, unit: 'ppm', description: 'Improves disease resistance and overall health' },
      moisture: { min: 20, max: 40, optimal: 30, unit: '%', description: 'Soil moisture content (lavender prefers dry conditions)' },
      temperature: { min: 15, max: 30, optimal: 22, unit: '°C', description: 'Ambient temperature' },
      ph: { min: 6.5, max: 7.5, optimal: 7, unit: 'pH', description: 'Soil acidity/alkalinity (lavender prefers neutral to slightly alkaline)' }
    };

    console.log('📊 Analyzing sensor data...');
    
    // Check each sensor
    for (const [key, value] of Object.entries(sensorData)) {
      const standard = standards[key];
      if (standard) {
        if (value < standard.min || value > standard.max) {
          issues.push(`${key}_out_of_range`);
          console.log(`  ${key}: ${value}${standard.unit} (optimal: ${standard.min}-${standard.max})`);
          console.log(`    ❌ Out of range`);
        } else {
          console.log(`  ${key}: ${value}${standard.unit} (optimal: ${standard.min}-${standard.max})`);
          console.log(`    ✅ Optimal`);
        }
      }
    }

    const status = issues.length === 0 ? 'optimal' : 'needs_attention';
    const message = issues.length === 0 
      ? 'All sensor readings within optimal range' 
      : `${issues.length} sensor(s) out of optimal range`;

    return {
      status,
      message,
      issues,
      severity: issues.length > 2 ? 'high' : issues.length > 0 ? 'medium' : 'low',
      standards,
      timestamp: new Date().toISOString()
    };
  }
}

module.exports = SensorService;  // Make sure it's exported as a class